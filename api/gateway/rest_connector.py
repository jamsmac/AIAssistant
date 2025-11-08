"""
REST API Connector
Connects to external REST APIs and fetches data
"""

import aiohttp
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import time

from .base_connector import BaseConnector, ConnectionConfig, SyncResult, SyncType


class RESTConnector(BaseConnector):
    """
    Connector for REST API data sources

    Config structure:
    {
        "base_url": "https://api.example.com",
        "endpoint": "/users",
        "method": "GET",  # GET, POST, PUT, DELETE
        "headers": {"Authorization": "Bearer token"},
        "params": {"page": 1, "limit": 100},
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 1
    }
    """

    def __init__(self, config: ConnectionConfig, db_pool):
        super().__init__(config, db_pool)
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(
                total=self.config.config.get('timeout', 30)
            )
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def test_connection(self) -> bool:
        """
        Test if the REST API is accessible

        Returns:
            bool: True if connection successful
        """
        try:
            base_url = self.config.config.get('base_url')
            endpoint = self.config.config.get('endpoint', '/')

            if not base_url:
                return False

            url = f"{base_url}{endpoint}"
            headers = self._build_headers()

            session = await self._get_session()
            async with session.get(url, headers=headers) as response:
                return response.status < 500

        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False

    async def fetch_data(self, **kwargs) -> SyncResult:
        """
        Fetch data from the REST API

        Args:
            **kwargs: Override config parameters
                - endpoint: Override endpoint
                - params: Override query parameters
                - method: Override HTTP method
                - data: Request body for POST/PUT

        Returns:
            SyncResult with fetched data
        """
        start_time = time.time()
        result = SyncResult(success=False)

        try:
            # Build request parameters
            base_url = self.config.config.get('base_url')
            endpoint = kwargs.get('endpoint', self.config.config.get('endpoint', '/'))
            method = kwargs.get('method', self.config.config.get('method', 'GET')).upper()
            params = kwargs.get('params', self.config.config.get('params', {}))
            data = kwargs.get('data', self.config.config.get('data'))

            if not base_url:
                result.error_message = "Base URL not configured"
                return result

            url = f"{base_url}{endpoint}"
            headers = self._build_headers()

            # Check rate limits
            rate_limit_ok = await self.check_rate_limit(
                max_requests=self.config.config.get('rate_limit_requests', 100),
                window_seconds=self.config.config.get('rate_limit_window', 60)
            )

            if not rate_limit_ok:
                result.error_message = "Rate limit exceeded"
                return result

            # Check cache first
            cache_key = self._build_cache_key(endpoint, params)
            cached_data = await self.get_cached_data(cache_key)

            if cached_data is not None:
                result.success = True
                result.data = cached_data
                result.records_fetched = len(cached_data) if isinstance(cached_data, list) else 1
                result.records_processed = result.records_fetched
                result.records_success = result.records_fetched
                result.duration_ms = int((time.time() - start_time) * 1000)
                return result

            # Make the request with retries
            retry_count = self.config.config.get('retry_count', 3)
            retry_delay = self.config.config.get('retry_delay', 1)

            for attempt in range(retry_count):
                try:
                    session = await self._get_session()

                    request_kwargs = {
                        'headers': headers,
                        'params': params
                    }

                    if method in ['POST', 'PUT', 'PATCH'] and data:
                        request_kwargs['json'] = data

                    async with session.request(method, url, **request_kwargs) as response:
                        if response.status == 200:
                            response_data = await response.json()

                            # Extract data from response based on config
                            data_path = self.config.config.get('data_path', '')
                            extracted_data = self._extract_data(response_data, data_path)

                            # Cache the result
                            cache_ttl = self.config.config.get('cache_ttl', 3600)
                            await self.cache_data(cache_key, extracted_data, cache_ttl)

                            result.success = True
                            result.data = extracted_data
                            result.records_fetched = len(extracted_data) if isinstance(extracted_data, list) else 1
                            result.records_processed = result.records_fetched
                            result.records_success = result.records_fetched
                            break

                        elif response.status < 500:
                            # Client error, don't retry
                            error_text = await response.text()
                            result.error_message = f"HTTP {response.status}: {error_text}"
                            break

                        else:
                            # Server error, retry
                            if attempt < retry_count - 1:
                                await asyncio.sleep(retry_delay * (attempt + 1))
                            else:
                                error_text = await response.text()
                                result.error_message = f"HTTP {response.status} after {retry_count} retries: {error_text}"

                except aiohttp.ClientError as e:
                    if attempt < retry_count - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                    else:
                        result.error_message = f"Request failed after {retry_count} retries: {str(e)}"

        except Exception as e:
            result.error_message = f"Fetch error: {str(e)}"
            result.error_details = {"exception": str(type(e).__name__)}

        finally:
            result.duration_ms = int((time.time() - start_time) * 1000)

        return result

    async def sync(self, mapping_id: Optional[str] = None, **kwargs) -> SyncResult:
        """
        Synchronize data from REST API to database

        Args:
            mapping_id: Optional data mapping to apply
            **kwargs: Parameters passed to fetch_data

        Returns:
            SyncResult with sync operation details
        """
        start_time = time.time()

        # Fetch data
        fetch_result = await self.fetch_data(**kwargs)

        if not fetch_result.success:
            await self.log_sync_history(fetch_result, SyncType.MANUAL, "api")
            return fetch_result

        # If mapping provided, transform and store data
        if mapping_id and fetch_result.data:
            try:
                mapping = await self._get_mapping(mapping_id)
                if mapping:
                    transformed_data = await self._apply_mapping(fetch_result.data, mapping)
                    await self._store_data(transformed_data, mapping)

                    fetch_result.records_processed = len(transformed_data)
                    fetch_result.records_success = len(transformed_data)
                else:
                    fetch_result.error_message = f"Mapping {mapping_id} not found"
                    fetch_result.success = False

            except Exception as e:
                fetch_result.error_message = f"Mapping error: {str(e)}"
                fetch_result.success = False

        fetch_result.duration_ms = int((time.time() - start_time) * 1000)

        # Log sync history
        await self.log_sync_history(fetch_result, SyncType.MANUAL, "api")

        return fetch_result

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers from config and credentials"""
        headers = self.config.config.get('headers', {}).copy()

        # Add authentication if available
        if self.config.credentials:
            auth_type = self.config.credentials.get('auth_type', 'bearer')

            if auth_type == 'bearer':
                token = self.config.credentials.get('token')
                if token:
                    headers['Authorization'] = f"Bearer {token}"

            elif auth_type == 'api_key':
                key_name = self.config.credentials.get('key_name', 'X-API-Key')
                key_value = self.config.credentials.get('key_value')
                if key_value:
                    headers[key_name] = key_value

            elif auth_type == 'basic':
                import base64
                username = self.config.credentials.get('username')
                password = self.config.credentials.get('password')
                if username and password:
                    auth_str = f"{username}:{password}"
                    auth_bytes = base64.b64encode(auth_str.encode()).decode()
                    headers['Authorization'] = f"Basic {auth_bytes}"

        return headers

    def _build_cache_key(self, endpoint: str, params: Dict) -> str:
        """Build a cache key from endpoint and params"""
        import hashlib
        key_parts = [endpoint]
        if params:
            # Sort params for consistent cache keys
            sorted_params = sorted(params.items())
            key_parts.append(str(sorted_params))

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _extract_data(self, response: Any, data_path: str) -> Any:
        """
        Extract data from response using JSONPath-like syntax

        Args:
            response: Response data
            data_path: Path to data (e.g., "data.users" or "results")

        Returns:
            Extracted data
        """
        if not data_path:
            return response

        current = response
        for key in data_path.split('.'):
            if isinstance(current, dict):
                current = current.get(key, current)
            else:
                break

        return current

    async def _get_mapping(self, mapping_id: str) -> Optional[Dict]:
        """Get data mapping configuration from database"""
        query = "SELECT * FROM gateway_data_mappings WHERE id = $1"
        row = await self.db_pool.fetchrow(query, mapping_id)
        return dict(row) if row else None

    async def _apply_mapping(self, data: List[Dict], mapping: Dict) -> List[Dict]:
        """
        Apply transformation rules from mapping

        Args:
            data: Source data
            mapping: Mapping configuration

        Returns:
            Transformed data
        """
        import json

        transformed = []
        source_schema = json.loads(mapping['source_schema']) if isinstance(mapping['source_schema'], str) else mapping['source_schema']
        target_schema = json.loads(mapping['target_schema']) if isinstance(mapping['target_schema'], str) else mapping['target_schema']
        transform_rules = json.loads(mapping['transformation_rules']) if mapping.get('transformation_rules') else {}

        for item in data:
            transformed_item = {}

            # Simple field mapping
            for target_field, source_field in target_schema.items():
                if source_field in item:
                    value = item[source_field]

                    # Apply transformation if specified
                    if target_field in transform_rules:
                        rule = transform_rules[target_field]
                        value = self._apply_transform(value, rule)

                    transformed_item[target_field] = value

            transformed.append(transformed_item)

        return transformed

    def _apply_transform(self, value: Any, rule: Dict) -> Any:
        """Apply a transformation rule to a value"""
        transform_type = rule.get('type')

        if transform_type == 'uppercase':
            return str(value).upper()
        elif transform_type == 'lowercase':
            return str(value).lower()
        elif transform_type == 'trim':
            return str(value).strip()
        elif transform_type == 'default':
            return value if value else rule.get('default')
        elif transform_type == 'map':
            mapping = rule.get('mapping', {})
            return mapping.get(value, value)

        return value

    async def _store_data(self, data: List[Dict], mapping: Dict) -> None:
        """Store transformed data in database"""
        target_table = mapping.get('target_table')
        if not target_table:
            return

        # This is a simplified version - in production you'd want more robust handling
        for item in data:
            # Build INSERT query dynamically
            fields = list(item.keys())
            values = [item[f] for f in fields]
            placeholders = [f"${i+1}" for i in range(len(fields))]

            query = f"""
            INSERT INTO {target_table} ({','.join(fields)})
            VALUES ({','.join(placeholders)})
            ON CONFLICT DO NOTHING
            """

            try:
                await self.db_pool.execute(query, *values)
            except Exception as e:
                print(f"Failed to store record: {str(e)}")

    def __del__(self):
        """Cleanup"""
        if self.session and not self.session.closed:
            asyncio.create_task(self.session.close())
