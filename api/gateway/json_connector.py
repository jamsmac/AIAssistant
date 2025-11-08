"""
JSON Data Source Connector
Connects to JSON files (local or remote URLs)
"""

import aiohttp
import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import time

from .base_connector import BaseConnector, ConnectionConfig, SyncResult, SyncType


class JSONConnector(BaseConnector):
    """
    Connector for JSON data sources (files or URLs)

    Config structure:
    {
        "source_type": "file",  # "file" or "url"
        "source_path": "/path/to/file.json" or "https://example.com/data.json",
        "data_path": "results",  # Optional: path within JSON to actual data
        "watch_for_changes": false,  # Auto-reload on file changes
        "timeout": 30
    }
    """

    def __init__(self, config: ConnectionConfig, db_pool):
        super().__init__(config, db_pool)
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_modified: Optional[datetime] = None

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
        Test if the JSON source is accessible

        Returns:
            bool: True if connection successful
        """
        try:
            source_type = self.config.config.get('source_type', 'file')

            if source_type == 'file':
                source_path = self.config.config.get('source_path')
                if not source_path:
                    return False

                path = Path(source_path)
                return path.exists() and path.is_file()

            elif source_type == 'url':
                source_path = self.config.config.get('source_path')
                if not source_path:
                    return False

                session = await self._get_session()
                async with session.head(source_path) as response:
                    return response.status == 200

            return False

        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False

    async def fetch_data(self, **kwargs) -> SyncResult:
        """
        Fetch data from JSON source

        Args:
            **kwargs: Override config parameters
                - source_path: Override source path
                - data_path: Override data extraction path

        Returns:
            SyncResult with fetched data
        """
        start_time = time.time()
        result = SyncResult(success=False)

        try:
            source_type = self.config.config.get('source_type', 'file')
            source_path = kwargs.get('source_path', self.config.config.get('source_path'))
            data_path = kwargs.get('data_path', self.config.config.get('data_path', ''))

            if not source_path:
                result.error_message = "Source path not configured"
                return result

            # Check cache first
            cache_key = self._build_cache_key(source_path)
            cached_data = await self.get_cached_data(cache_key)

            if cached_data is not None:
                result.success = True
                result.data = cached_data
                result.records_fetched = len(cached_data) if isinstance(cached_data, list) else 1
                result.records_processed = result.records_fetched
                result.records_success = result.records_fetched
                result.duration_ms = int((time.time() - start_time) * 1000)
                return result

            # Fetch data based on source type
            if source_type == 'file':
                json_data = await self._read_file(source_path)
            elif source_type == 'url':
                json_data = await self._fetch_url(source_path)
            else:
                result.error_message = f"Unknown source type: {source_type}"
                return result

            if json_data is None:
                result.error_message = "Failed to read JSON data"
                return result

            # Extract data if path specified
            extracted_data = self._extract_data(json_data, data_path)

            # Validate that we have data
            if extracted_data is None:
                result.error_message = "No data found at specified path"
                return result

            # Cache the result
            cache_ttl = self.config.config.get('cache_ttl', 3600)
            await self.cache_data(cache_key, extracted_data, cache_ttl)

            result.success = True
            result.data = extracted_data
            result.records_fetched = len(extracted_data) if isinstance(extracted_data, list) else 1
            result.records_processed = result.records_fetched
            result.records_success = result.records_fetched

        except json.JSONDecodeError as e:
            result.error_message = f"Invalid JSON: {str(e)}"
            result.error_details = {"line": e.lineno, "column": e.colno}

        except Exception as e:
            result.error_message = f"Fetch error: {str(e)}"
            result.error_details = {"exception": str(type(e).__name__)}

        finally:
            result.duration_ms = int((time.time() - start_time) * 1000)

        return result

    async def _read_file(self, file_path: str) -> Optional[Any]:
        """
        Read JSON from a file

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data or None
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return None

            # Check if file has been modified since last read
            current_mtime = datetime.fromtimestamp(path.stat().st_mtime)

            if self.last_modified and current_mtime <= self.last_modified:
                # File hasn't changed, return cached
                pass

            self.last_modified = current_mtime

            # Read file asynchronously
            loop = asyncio.get_event_loop()
            def read_sync():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)

            data = await loop.run_in_executor(None, read_sync)
            return data

        except Exception as e:
            print(f"Failed to read file: {str(e)}")
            return None

    async def _fetch_url(self, url: str) -> Optional[Any]:
        """
        Fetch JSON from a URL

        Args:
            url: URL to fetch from

        Returns:
            Parsed JSON data or None
        """
        try:
            session = await self._get_session()

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"HTTP {response.status} when fetching URL")
                    return None

        except aiohttp.ClientError as e:
            print(f"Failed to fetch URL: {str(e)}")
            return None

        except Exception as e:
            print(f"Error fetching URL: {str(e)}")
            return None

    async def sync(self, mapping_id: Optional[str] = None, **kwargs) -> SyncResult:
        """
        Synchronize JSON data to database

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
                    # Ensure data is a list
                    data_list = fetch_result.data if isinstance(fetch_result.data, list) else [fetch_result.data]

                    transformed_data = await self._apply_mapping(data_list, mapping)
                    await self._store_data(transformed_data, mapping)

                    fetch_result.records_processed = len(transformed_data)
                    fetch_result.records_success = len(transformed_data)
                else:
                    fetch_result.error_message = f"Mapping {mapping_id} not found"
                    fetch_result.success = False

            except Exception as e:
                fetch_result.error_message = f"Mapping error: {str(e)}"
                fetch_result.error_details = {"exception": str(type(e).__name__)}
                fetch_result.success = False

        fetch_result.duration_ms = int((time.time() - start_time) * 1000)

        # Log sync history
        await self.log_sync_history(fetch_result, SyncType.MANUAL, "api")

        return fetch_result

    def _extract_data(self, json_data: Any, data_path: str) -> Any:
        """
        Extract data from JSON using dot notation path

        Args:
            json_data: Source JSON data
            data_path: Path to data (e.g., "data.users" or "results.items")

        Returns:
            Extracted data
        """
        if not data_path:
            return json_data

        current = json_data

        # Support both dot notation and bracket notation
        for key in data_path.split('.'):
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return None
            elif isinstance(current, list):
                # If key is a number, treat as array index
                try:
                    index = int(key)
                    current = current[index]
                except (ValueError, IndexError):
                    return None
            else:
                return None

        return current

    def _build_cache_key(self, source_path: str) -> str:
        """Build a cache key from source path"""
        import hashlib
        return hashlib.md5(source_path.encode()).hexdigest()

    async def _get_mapping(self, mapping_id: str) -> Optional[Dict]:
        """Get data mapping configuration from database"""
        query = "SELECT * FROM gateway_data_mappings WHERE id = $1"
        row = await self.db_pool.fetchrow(query, mapping_id)
        return dict(row) if row else None

    async def _apply_mapping(self, data: List[Dict], mapping: Dict) -> List[Dict]:
        """Apply transformation rules from mapping"""
        import json as jsonlib

        transformed = []
        target_schema = jsonlib.loads(mapping['target_schema']) if isinstance(mapping['target_schema'], str) else mapping['target_schema']
        transform_rules = jsonlib.loads(mapping['transformation_rules']) if mapping.get('transformation_rules') else {}

        for item in data:
            transformed_item = {}

            # Apply field mapping
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
        elif transform_type == 'parse_int':
            try:
                return int(value)
            except (ValueError, TypeError):
                return rule.get('default', 0)
        elif transform_type == 'parse_float':
            try:
                return float(value)
            except (ValueError, TypeError):
                return rule.get('default', 0.0)

        return value

    async def _store_data(self, data: List[Dict], mapping: Dict) -> None:
        """Store transformed data in database"""
        target_table = mapping.get('target_table')
        if not target_table:
            return

        for item in data:
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

    async def watch_for_changes(self, callback):
        """
        Watch file for changes and trigger callback

        Args:
            callback: Async function to call when file changes
        """
        if self.config.config.get('source_type') != 'file':
            return

        source_path = self.config.config.get('source_path')
        if not source_path:
            return

        path = Path(source_path)
        last_mtime = path.stat().st_mtime if path.exists() else None

        while True:
            await asyncio.sleep(5)  # Check every 5 seconds

            if not path.exists():
                continue

            current_mtime = path.stat().st_mtime

            if last_mtime and current_mtime > last_mtime:
                # File has changed
                try:
                    await callback(self)
                except Exception as e:
                    print(f"Error in change callback: {str(e)}")

            last_mtime = current_mtime

    def __del__(self):
        """Cleanup"""
        if self.session and not self.session.closed:
            asyncio.create_task(self.session.close())
