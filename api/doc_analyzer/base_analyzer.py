"""
Base Analyzer - Abstract class for documentation analyzers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncpg
import logging
import json

logger = logging.getLogger(__name__)


class AnalysisStatus(str, Enum):
    """Analysis status states"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DocumentConfig:
    """Configuration for a documentation source"""
    id: Optional[str] = None
    name: str = ""
    type: str = ""  # 'openapi', 'swagger', 'pdf', 'google_sheets'
    source_type: str = "url"  # 'url', 'upload', 'text'
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: AnalysisStatus = AnalysisStatus.PENDING
    created_by: Optional[str] = None


@dataclass
class AnalysisResult:
    """Results from documentation analysis"""
    doc_source_id: str
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    schemas: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    diagrams: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAnalyzer(ABC):
    """
    Abstract base class for documentation analyzers.
    Provides common functionality for all analyzer types.
    """

    def __init__(self, config: DocumentConfig, db_pool: asyncpg.Pool):
        self.config = config
        self.db_pool = db_pool
        self.processing_start_time: Optional[datetime] = None

    @abstractmethod
    async def parse_document(self) -> Dict[str, Any]:
        """
        Parse the documentation and extract structure.
        Returns raw parsed data.
        """
        pass

    @abstractmethod
    async def analyze_with_ai(self, content: Dict) -> Dict[str, Any]:
        """
        Analyze content using AI to generate explanations.
        Returns AI-enhanced analysis.
        """
        pass

    async def save_source(self) -> str:
        """Save or update document source in database"""
        async with self.db_pool.acquire() as conn:
            if self.config.id:
                # Update existing source
                await conn.execute("""
                    UPDATE doc_sources
                    SET name = $1, type = $2, source_type = $3,
                        source_url = $4, file_path = $5, file_content = $6,
                        metadata = $7, status = $8, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $9
                """, self.config.name, self.config.type, self.config.source_type,
                    self.config.source_url, self.config.file_path,
                    self.config.file_content, self.config.metadata,
                    self.config.status, self.config.id)

                logger.info(f"Updated doc source: {self.config.id}")
                return self.config.id
            else:
                # Insert new source
                row = await conn.fetchrow("""
                    INSERT INTO doc_sources (
                        name, type, source_type, source_url, file_path,
                        file_content, metadata, status, created_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """, self.config.name, self.config.type, self.config.source_type,
                    self.config.source_url, self.config.file_path,
                    self.config.file_content, self.config.metadata,
                    self.config.status, self.config.created_by)

                self.config.id = str(row['id'])
                logger.info(f"Created new doc source: {self.config.id}")
                return self.config.id

    async def update_status(self, status: AnalysisStatus, error_message: Optional[str] = None):
        """Update analysis status"""
        self.config.status = status

        async with self.db_pool.acquire() as conn:
            if status == AnalysisStatus.PROCESSING:
                await conn.execute("""
                    UPDATE doc_sources
                    SET status = $1, processing_started_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """, status, self.config.id)
                self.processing_start_time = datetime.utcnow()

            elif status == AnalysisStatus.COMPLETED:
                await conn.execute("""
                    UPDATE doc_sources
                    SET status = $1, processing_completed_at = CURRENT_TIMESTAMP,
                        error_message = NULL
                    WHERE id = $2
                """, status, self.config.id)

            elif status == AnalysisStatus.FAILED:
                await conn.execute("""
                    UPDATE doc_sources
                    SET status = $1, error_message = $2
                    WHERE id = $3
                """, status, error_message, self.config.id)

            logger.info(f"Updated doc source {self.config.id} status to {status}")

    async def save_analysis_result(self, analysis_type: str, results: Dict,
                                   ai_summary: Optional[str] = None,
                                   ai_model: Optional[str] = None) -> str:
        """Save analysis results to database"""
        processing_time_ms = None
        if self.processing_start_time:
            delta = datetime.utcnow() - self.processing_start_time
            processing_time_ms = int(delta.total_seconds() * 1000)

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO doc_analyses (
                    doc_source_id, analysis_type, results, ai_summary,
                    ai_model, processing_time_ms
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, self.config.id, analysis_type, json.dumps(results), ai_summary,
                ai_model, processing_time_ms)

            analysis_id = str(row['id'])
            logger.info(f"Saved analysis result: {analysis_id}")
            return analysis_id

    async def save_endpoints(self, endpoints: List[Dict[str, Any]]):
        """Save extracted endpoints to database"""
        if not endpoints:
            return

        async with self.db_pool.acquire() as conn:
            for endpoint in endpoints:
                await conn.execute("""
                    INSERT INTO doc_endpoints (
                        doc_source_id, method, path, summary, description,
                        ai_explanation, parameters, request_body, responses,
                        tags, security, deprecated
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """, self.config.id, endpoint.get('method', ''),
                    endpoint.get('path', ''), endpoint.get('summary', ''),
                    endpoint.get('description', ''), endpoint.get('ai_explanation', ''),
                    json.dumps(endpoint.get('parameters')) if endpoint.get('parameters') else None,
                    json.dumps(endpoint.get('request_body')) if endpoint.get('request_body') else None,
                    json.dumps(endpoint.get('responses')) if endpoint.get('responses') else None,
                    endpoint.get('tags', []),
                    json.dumps(endpoint.get('security')) if endpoint.get('security') else None,
                    endpoint.get('deprecated', False))

            logger.info(f"Saved {len(endpoints)} endpoints for doc {self.config.id}")

    async def save_schemas(self, schemas: Dict[str, Any]):
        """Save extracted schemas to database"""
        if not schemas:
            return

        async with self.db_pool.acquire() as conn:
            for schema_name, schema_data in schemas.items():
                # Sanitize table name
                sql_table_name = await conn.fetchval(
                    "SELECT sanitize_table_name($1)", schema_name
                )

                await conn.execute("""
                    INSERT INTO doc_schemas (
                        doc_source_id, schema_name, schema_type, properties,
                        required_fields, description, ai_explanation,
                        generated_sql, sql_table_name
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (doc_source_id, schema_name)
                    DO UPDATE SET
                        schema_type = EXCLUDED.schema_type,
                        properties = EXCLUDED.properties,
                        required_fields = EXCLUDED.required_fields,
                        description = EXCLUDED.description,
                        ai_explanation = EXCLUDED.ai_explanation,
                        generated_sql = EXCLUDED.generated_sql,
                        sql_table_name = EXCLUDED.sql_table_name
                """, self.config.id, schema_name,
                    schema_data.get('type', 'object'),
                    json.dumps(schema_data.get('properties', {})),
                    schema_data.get('required', []),
                    schema_data.get('description', ''),
                    schema_data.get('ai_explanation', ''),
                    schema_data.get('generated_sql', ''),
                    sql_table_name)

            logger.info(f"Saved {len(schemas)} schemas for doc {self.config.id}")

    async def get_analysis_results(self) -> Optional[AnalysisResult]:
        """Retrieve all analysis results for this document"""
        if not self.config.id:
            return None

        async with self.db_pool.acquire() as conn:
            # Get endpoints
            endpoint_rows = await conn.fetch("""
                SELECT method, path, summary, description, ai_explanation,
                       parameters, request_body, responses, tags
                FROM doc_endpoints
                WHERE doc_source_id = $1
                ORDER BY path, method
            """, self.config.id)

            endpoints = [dict(row) for row in endpoint_rows]

            # Get schemas
            schema_rows = await conn.fetch("""
                SELECT schema_name, schema_type, properties, required_fields,
                       description, ai_explanation, generated_sql
                FROM doc_schemas
                WHERE doc_source_id = $1
                ORDER BY schema_name
            """, self.config.id)

            schemas = {
                row['schema_name']: dict(row)
                for row in schema_rows
            }

            # Get summary from analyses
            analysis_row = await conn.fetchrow("""
                SELECT ai_summary, results
                FROM doc_analyses
                WHERE doc_source_id = $1
                  AND analysis_type = 'full'
                ORDER BY created_at DESC
                LIMIT 1
            """, self.config.id)

            summary = ""
            metadata = {}
            if analysis_row:
                summary = analysis_row['ai_summary'] or ""
                metadata = analysis_row['results'] or {}

            return AnalysisResult(
                doc_source_id=self.config.id,
                endpoints=endpoints,
                schemas=schemas,
                summary=summary,
                metadata=metadata
            )

    async def delete_source(self):
        """Delete document source and all related data (cascades)"""
        if not self.config.id:
            return

        async with self.db_pool.acquire() as conn:
            await conn.execute("DELETE FROM doc_sources WHERE id = $1", self.config.id)
            logger.info(f"Deleted doc source: {self.config.id}")
