"""
OpenAPI/Swagger Analyzer
Parses and analyzes OpenAPI/Swagger documentation
"""

import yaml
import json
import httpx
from typing import Dict, List, Any, Optional
from .base_analyzer import BaseAnalyzer, DocumentConfig, AnalysisStatus
import logging

logger = logging.getLogger(__name__)


class OpenAPIAnalyzer(BaseAnalyzer):
    """Analyzer for OpenAPI/Swagger specifications"""

    def __init__(self, config: DocumentConfig, db_pool):
        super().__init__(config, db_pool)
        self.spec: Optional[Dict] = None

    async def parse_document(self) -> Dict[str, Any]:
        """Parse OpenAPI specification from URL or content"""
        try:
            # Get content
            if self.config.source_type == 'url' and self.config.source_url:
                content = await self._fetch_from_url(self.config.source_url)
            elif self.config.file_content:
                content = self.config.file_content
            else:
                raise ValueError("No content source provided")

            # Parse YAML or JSON
            try:
                # Try JSON first
                self.spec = json.loads(content)
            except json.JSONDecodeError:
                # Try YAML
                self.spec = yaml.safe_load(content)

            if not self.spec:
                raise ValueError("Failed to parse specification")

            # Extract structure
            parsed_data = {
                'info': self.spec.get('info', {}),
                'openapi_version': self.spec.get('openapi') or self.spec.get('swagger'),
                'servers': self.spec.get('servers', []),
                'paths': await self._parse_paths(),
                'schemas': await self._parse_schemas(),
                'security_schemes': self.spec.get('components', {}).get('securitySchemes', {}),
                'tags': self.spec.get('tags', [])
            }

            logger.info(f"Parsed OpenAPI spec: {len(parsed_data['paths'])} endpoints, "
                       f"{len(parsed_data['schemas'])} schemas")

            return parsed_data

        except Exception as e:
            logger.error(f"Failed to parse OpenAPI document: {e}")
            raise

    async def _fetch_from_url(self, url: str) -> str:
        """Fetch OpenAPI spec from URL"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    async def _parse_paths(self) -> List[Dict[str, Any]]:
        """Extract all API endpoints from paths"""
        paths = []
        spec_paths = self.spec.get('paths', {})

        for path, methods in spec_paths.items():
            for method, details in methods.items():
                # Skip non-HTTP methods (like parameters, $ref, etc.)
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                    continue

                endpoint = {
                    'path': path,
                    'method': method.upper(),
                    'summary': details.get('summary', ''),
                    'description': details.get('description', ''),
                    'parameters': self._parse_parameters(details.get('parameters', [])),
                    'request_body': self._parse_request_body(details.get('requestBody', {})),
                    'responses': self._parse_responses(details.get('responses', {})),
                    'tags': details.get('tags', []),
                    'security': details.get('security', []),
                    'deprecated': details.get('deprecated', False),
                    'operation_id': details.get('operationId', '')
                }

                paths.append(endpoint)

        return paths

    def _parse_parameters(self, parameters: List) -> List[Dict]:
        """Parse endpoint parameters"""
        parsed_params = []
        for param in parameters:
            parsed_params.append({
                'name': param.get('name', ''),
                'in': param.get('in', ''),  # query, path, header, cookie
                'description': param.get('description', ''),
                'required': param.get('required', False),
                'schema': param.get('schema', {}),
                'example': param.get('example')
            })
        return parsed_params

    def _parse_request_body(self, request_body: Dict) -> Optional[Dict]:
        """Parse request body specification"""
        if not request_body:
            return None

        content = request_body.get('content', {})
        # Get first content type (usually application/json)
        content_type = list(content.keys())[0] if content else None

        if content_type:
            return {
                'content_type': content_type,
                'schema': content[content_type].get('schema', {}),
                'description': request_body.get('description', ''),
                'required': request_body.get('required', False)
            }

        return None

    def _parse_responses(self, responses: Dict) -> Dict[str, Any]:
        """Parse response specifications"""
        parsed_responses = {}

        for status_code, response_data in responses.items():
            content = response_data.get('content', {})
            content_type = list(content.keys())[0] if content else None

            parsed_responses[status_code] = {
                'description': response_data.get('description', ''),
                'content_type': content_type,
                'schema': content.get(content_type, {}).get('schema', {}) if content_type else {}
            }

        return parsed_responses

    async def _parse_schemas(self) -> Dict[str, Any]:
        """Extract data schemas/models from OpenAPI 3.x or Swagger 2.0"""
        # Check for OpenAPI 3.x format (components.schemas)
        components = self.spec.get('components', {})
        schemas = components.get('schemas', {})

        # If no schemas found, check for Swagger 2.0 format (definitions)
        if not schemas:
            schemas = self.spec.get('definitions', {})
            if schemas:
                logger.info(f"Found {len(schemas)} schemas in Swagger 2.0 'definitions' section")

        parsed_schemas = {}

        for schema_name, schema_def in schemas.items():
            parsed_schemas[schema_name] = {
                'type': schema_def.get('type', 'object'),
                'properties': schema_def.get('properties', {}),
                'required': schema_def.get('required', []),
                'description': schema_def.get('description', ''),
                'example': schema_def.get('example'),
                'enum': schema_def.get('enum')
            }

        return parsed_schemas

    async def analyze_with_ai(self, content: Dict) -> Dict[str, Any]:
        """
        This method delegates AI analysis to the AnalysisEngine.
        It's implemented here to satisfy the abstract method requirement.
        """
        # Import here to avoid circular dependency
        from .analysis_engine import AnalysisEngine

        engine = AnalysisEngine(self.db_pool)
        return await engine.analyze_openapi_spec(content)

    async def generate_mermaid_diagram(self) -> str:
        """Generate Mermaid diagram showing API structure"""
        if not self.spec:
            return ""

        lines = ["graph TD"]

        # Add API info
        api_name = self.spec.get('info', {}).get('title', 'API')
        lines.append(f'    API["{api_name}"]')

        # Group endpoints by tags
        paths = self.spec.get('paths', {})
        tag_groups = {}

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    continue

                tags = details.get('tags', ['default'])
                for tag in tags:
                    if tag not in tag_groups:
                        tag_groups[tag] = []

                    tag_groups[tag].append({
                        'method': method.upper(),
                        'path': path,
                        'summary': details.get('summary', '')
                    })

        # Add tag nodes and endpoints
        for i, (tag, endpoints) in enumerate(tag_groups.items()):
            tag_id = f"TAG{i}"
            lines.append(f'    {tag_id}["{tag}"]')
            lines.append(f'    API --> {tag_id}')

            for j, endpoint in enumerate(endpoints[:3]):  # Limit to 3 per tag
                endpoint_id = f"E{i}_{j}"
                method = endpoint['method']
                path = endpoint['path']
                lines.append(f'    {endpoint_id}["{method} {path}"]')
                lines.append(f'    {tag_id} --> {endpoint_id}')

        return '\n'.join(lines)

    async def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of the API"""
        if not self.spec:
            return {}

        paths = self.spec.get('paths', {})

        # Check for OpenAPI 3.x schemas or Swagger 2.0 definitions
        schemas = self.spec.get('components', {}).get('schemas', {})
        if not schemas:
            schemas = self.spec.get('definitions', {})

        # Count endpoints by method
        method_counts = {}
        total_endpoints = 0

        for path, methods in paths.items():
            for method in methods.keys():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    method_counts[method.upper()] = method_counts.get(method.upper(), 0) + 1
                    total_endpoints += 1

        # Detect spec version
        spec_version = self.spec.get('openapi') or self.spec.get('swagger', 'unknown')

        return {
            'total_endpoints': total_endpoints,
            'total_schemas': len(schemas),
            'methods': method_counts,
            'api_version': self.spec.get('info', {}).get('version', 'unknown'),
            'api_title': self.spec.get('info', {}).get('title', 'Unknown API'),
            'spec_version': spec_version
        }
