"""
Analysis Engine - AI-powered documentation analysis and explanation
"""

import os
from typing import Dict, List, Any, Optional
from anthropic import AsyncAnthropic
import logging

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """AI-powered analysis engine for documentation"""

    def __init__(self, db_pool, api_key: Optional[str] = None):
        self.db_pool = db_pool
        api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.warning("No Anthropic API key found. AI analysis will be disabled.")
            self.client = None
        else:
            self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    async def explain_endpoint(self, endpoint: Dict[str, Any], language: str = "ru") -> str:
        """Generate simple explanation of what an endpoint does"""
        if not self.client:
            return self._generate_basic_explanation(endpoint)

        try:
            method = endpoint.get('method', '')
            path = endpoint.get('path', '')
            summary = endpoint.get('summary', '')
            description = endpoint.get('description', '')

            if language == "ru":
                prompt = f"""Объясни простыми словами что делает этот API эндпоинт:

Метод: {method}
Путь: {path}
Краткое описание: {summary}
Подробное описание: {description}

Ответь ОДНИМ предложением на русском языке, объясняя что делает этот эндпоинт и для чего он нужен."""
            else:
                prompt = f"""Explain in simple terms what this API endpoint does:

Method: {method}
Path: {path}
Summary: {summary}
Description: {description}

Answer in ONE sentence explaining what this endpoint does and what it's used for."""

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"AI explanation failed: {e}")
            return self._generate_basic_explanation(endpoint)

    async def explain_schema(self, schema_name: str, schema: Dict[str, Any],
                           language: str = "ru") -> str:
        """Generate simple explanation of what a schema represents"""
        if not self.client:
            return self._generate_basic_schema_explanation(schema_name, schema)

        try:
            properties = schema.get('properties', {})
            field_names = ', '.join(properties.keys())
            description = schema.get('description', '')

            if language == "ru":
                prompt = f"""Объясни простыми словами что за данные представляет эта схема:

Название: {schema_name}
Поля: {field_names}
Описание: {description}

Ответь кратко на русском языке (2-3 предложения), объясняя что это за данные и для чего они используются."""
            else:
                prompt = f"""Explain in simple terms what data this schema represents:

Name: {schema_name}
Fields: {field_names}
Description: {description}

Answer briefly (2-3 sentences) explaining what this data represents and what it's used for."""

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"AI schema explanation failed: {e}")
            return self._generate_basic_schema_explanation(schema_name, schema)

    async def analyze_openapi_spec(self, parsed_content: Dict[str, Any],
                                  language: str = "ru") -> Dict[str, Any]:
        """Comprehensive AI analysis of entire OpenAPI specification"""
        results = {
            'endpoints': [],
            'schemas': {},
            'summary': '',
            'recommendations': []
        }

        # Analyze each endpoint
        for endpoint in parsed_content.get('paths', []):
            try:
                explanation = await self.explain_endpoint(endpoint, language)
                endpoint['ai_explanation'] = explanation
                results['endpoints'].append(endpoint)
            except Exception as e:
                logger.error(f"Failed to analyze endpoint {endpoint.get('path')}: {e}")
                endpoint['ai_explanation'] = self._generate_basic_explanation(endpoint)
                results['endpoints'].append(endpoint)

        # Analyze each schema
        for schema_name, schema_data in parsed_content.get('schemas', {}).items():
            try:
                explanation = await self.explain_schema(schema_name, schema_data, language)
                schema_data['ai_explanation'] = explanation
                results['schemas'][schema_name] = schema_data
            except Exception as e:
                logger.error(f"Failed to analyze schema {schema_name}: {e}")
                schema_data['ai_explanation'] = self._generate_basic_schema_explanation(
                    schema_name, schema_data
                )
                results['schemas'][schema_name] = schema_data

        # Generate overall summary
        try:
            results['summary'] = await self._generate_api_summary(parsed_content, language)
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            results['summary'] = self._generate_basic_summary(parsed_content)

        return results

    async def _generate_api_summary(self, parsed_content: Dict[str, Any],
                                   language: str = "ru") -> str:
        """Generate overall API summary"""
        if not self.client:
            return self._generate_basic_summary(parsed_content)

        try:
            info = parsed_content.get('info', {})
            api_title = info.get('title', 'Unknown API')
            api_description = info.get('description', '')
            endpoint_count = len(parsed_content.get('paths', []))
            schema_count = len(parsed_content.get('schemas', {}))

            if language == "ru":
                prompt = f"""Создай краткое резюме для этого API:

Название: {api_title}
Описание: {api_description}
Количество эндпоинтов: {endpoint_count}
Количество схем данных: {schema_count}

Напиши краткое резюме на русском (3-5 предложений), объясняя:
1. Что делает этот API
2. Основные возможности
3. Для кого он предназначен"""
            else:
                prompt = f"""Create a brief summary for this API:

Title: {api_title}
Description: {api_description}
Endpoint count: {endpoint_count}
Schema count: {schema_count}

Write a brief summary (3-5 sentences) explaining:
1. What this API does
2. Main capabilities
3. Who it's intended for"""

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Failed to generate API summary: {e}")
            return self._generate_basic_summary(parsed_content)

    def _generate_basic_explanation(self, endpoint: Dict[str, Any]) -> str:
        """Generate basic explanation without AI"""
        method = endpoint.get('method', '')
        path = endpoint.get('path', '')
        summary = endpoint.get('summary', '')

        if summary:
            return summary

        # Generate based on HTTP method
        action_map = {
            'GET': 'получает данные из',
            'POST': 'создает новую запись в',
            'PUT': 'обновляет данные в',
            'DELETE': 'удаляет данные из',
            'PATCH': 'частично обновляет данные в'
        }

        action = action_map.get(method, 'выполняет операцию с')
        return f"Этот эндпоинт {action} {path}"

    def _generate_basic_schema_explanation(self, schema_name: str,
                                          schema: Dict[str, Any]) -> str:
        """Generate basic schema explanation without AI"""
        description = schema.get('description', '')
        if description:
            return description

        property_count = len(schema.get('properties', {}))
        return f"Схема данных '{schema_name}' содержит {property_count} полей"

    def _generate_basic_summary(self, parsed_content: Dict[str, Any]) -> str:
        """Generate basic summary without AI"""
        info = parsed_content.get('info', {})
        api_title = info.get('title', 'Unknown API')
        endpoint_count = len(parsed_content.get('paths', []))
        schema_count = len(parsed_content.get('schemas', {}))

        return (f"API '{api_title}' содержит {endpoint_count} эндпоинтов "
                f"и {schema_count} схем данных.")

    async def generate_field_descriptions(self, properties: Dict[str, Any],
                                        language: str = "ru") -> Dict[str, str]:
        """Generate descriptions for schema fields"""
        descriptions = {}

        if not self.client:
            return {name: f"Поле {name}" for name in properties.keys()}

        try:
            field_list = '\n'.join([
                f"- {name}: {prop.get('type', 'unknown')}"
                for name, prop in properties.items()
            ])

            if language == "ru":
                prompt = f"""Для каждого поля создай краткое описание (5-10 слов):

{field_list}

Формат ответа: одна строка на поле в формате "название: описание" """
            else:
                prompt = f"""For each field, create a brief description (5-10 words):

{field_list}

Response format: one line per field as "name: description" """

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            lines = response.content[0].text.strip().split('\n')
            for line in lines:
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        field_name = parts[0].strip().lstrip('-').strip()
                        description = parts[1].strip()
                        descriptions[field_name] = description

        except Exception as e:
            logger.error(f"Failed to generate field descriptions: {e}")

        # Fill in missing descriptions
        for name in properties.keys():
            if name not in descriptions:
                descriptions[name] = f"Поле {name}"

        return descriptions
