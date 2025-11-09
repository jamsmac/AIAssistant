"""
Documentation Analyzer Router
API endpoints for documentation analysis and auto-schema generation
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncpg
import logging
import json

from ..db_pool import get_db_pool
from ..doc_analyzer import (
    OpenAPIAnalyzer,
    AnalysisEngine,
    SchemaGenerator,
    DocumentConfig,
    AnalysisStatus
)
from ..doc_analyzer.sheets_exporter import get_sheets_exporter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/doc-analyzer", tags=["doc-analyzer"])


# ==================== Request/Response Models ====================

class DocumentCreate(BaseModel):
    """Request model for creating a new document source"""
    name: str = Field(..., description="Friendly name for the documentation")
    type: str = Field(..., description="Type of documentation (openapi, swagger, pdf)")
    source_type: str = Field(default="url", description="Source type (url, upload, text)")
    source_url: Optional[str] = Field(None, description="URL to fetch documentation from")
    file_content: Optional[str] = Field(None, description="Direct content of the documentation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    analyze_immediately: bool = Field(default=True, description="Start analysis immediately")


class DocumentResponse(BaseModel):
    """Response model for document source"""
    id: str
    name: str
    type: str
    source_type: str
    source_url: Optional[str]
    status: str
    error_message: Optional[str]
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    doc_source_id: str
    status: str
    summary: str
    endpoint_count: int
    schema_count: int
    endpoints: List[Dict[str, Any]]
    schemas: Dict[str, Any]
    diagram: Optional[str]


class SchemaGenerateRequest(BaseModel):
    """Request to generate SQL for a schema"""
    doc_source_id: str
    schema_name: str
    include_audit_fields: bool = True
    execute_immediately: bool = False


# ==================== Helper Functions ====================

async def _run_analysis(doc_source_id: str, pool: asyncpg.Pool):
    """Background task to analyze documentation"""
    try:
        # Get document source
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, name, type, source_type, source_url, file_content, metadata
                FROM doc_sources WHERE id = $1
            """, doc_source_id)

            if not row:
                logger.error(f"Document source not found: {doc_source_id}")
                return

        # Create config
        config = DocumentConfig(
            id=str(row['id']),
            name=row['name'],
            type=row['type'],
            source_type=row['source_type'],
            source_url=row['source_url'],
            file_content=row['file_content'],
            metadata=row['metadata'] or {}
        )

        # Create analyzer based on type
        if config.type in ['openapi', 'swagger']:
            analyzer = OpenAPIAnalyzer(config, pool)
        else:
            raise ValueError(f"Unsupported document type: {config.type}")

        # Update status to processing
        await analyzer.update_status(AnalysisStatus.PROCESSING)

        # Parse document
        logger.info(f"Parsing document {doc_source_id}...")
        parsed_content = await analyzer.parse_document()

        # Analyze with AI
        logger.info(f"Analyzing with AI {doc_source_id}...")
        analysis_engine = AnalysisEngine(pool)
        ai_results = await analysis_engine.analyze_openapi_spec(parsed_content)

        # Save endpoints
        await analyzer.save_endpoints(ai_results['endpoints'])

        # Generate SQL for schemas and save
        schema_generator = SchemaGenerator(pool)
        for schema_name, schema_data in ai_results['schemas'].items():
            # Generate SQL
            sql = schema_generator.generate_create_table_sql(schema_name, schema_data)
            schema_data['generated_sql'] = sql

        await analyzer.save_schemas(ai_results['schemas'])

        # Save full analysis result
        await analyzer.save_analysis_result(
            analysis_type='full',
            results=ai_results,
            ai_summary=ai_results.get('summary', ''),
            ai_model='claude-3-5-sonnet-20241022'
        )

        # Update status to completed
        await analyzer.update_status(AnalysisStatus.COMPLETED)

        logger.info(f"Analysis completed for document {doc_source_id}")

    except Exception as e:
        logger.error(f"Analysis failed for document {doc_source_id}: {e}")

        # Update status to failed
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE doc_sources
                SET status = 'failed', error_message = $1
                WHERE id = $2
            """, str(e), doc_source_id)


# ==================== API Endpoints ====================

@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    doc: DocumentCreate,
    background_tasks: BackgroundTasks,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Create a new documentation source and optionally start analysis.
    """
    try:
        # Create document source
        config = DocumentConfig(
            name=doc.name,
            type=doc.type,
            source_type=doc.source_type,
            source_url=doc.source_url,
            file_content=doc.file_content,
            metadata=doc.metadata,
            status=AnalysisStatus.PENDING
        )

        # Save to database
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO doc_sources (
                    name, type, source_type, source_url, file_content, metadata, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, name, type, source_type, source_url, status,
                          error_message, processing_started_at, processing_completed_at,
                          created_at, updated_at
            """, config.name, config.type, config.source_type, config.source_url,
                config.file_content, json.dumps(config.metadata), config.status)

            doc_id = str(row['id'])

        # Schedule analysis if requested
        if doc.analyze_immediately:
            background_tasks.add_task(_run_analysis, doc_id, pool)

        return DocumentResponse(
            id=doc_id,
            name=row['name'],
            type=row['type'],
            source_type=row['source_type'],
            source_url=row['source_url'],
            status=row['status'],
            error_message=row['error_message'],
            processing_started_at=row['processing_started_at'],
            processing_completed_at=row['processing_completed_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    List all documentation sources with optional filtering.
    """
    try:
        query = """
            SELECT id, name, type, source_type, source_url, status,
                   error_message, processing_started_at, processing_completed_at,
                   created_at, updated_at
            FROM doc_sources
            WHERE 1=1
        """
        params = []
        param_count = 1

        if type:
            query += f" AND type = ${param_count}"
            params.append(type)
            param_count += 1

        if status:
            query += f" AND status = ${param_count}"
            params.append(status)
            param_count += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
        params.extend([limit, offset])

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [DocumentResponse(**{**dict(row), 'id': str(row['id'])}) for row in rows]

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    """Get a specific documentation source by ID."""
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, name, type, source_type, source_url, status,
                       error_message, processing_started_at, processing_completed_at,
                       created_at, updated_at
                FROM doc_sources WHERE id = $1
            """, doc_id)

            if not row:
                raise HTTPException(status_code=404, detail="Document not found")

        return DocumentResponse(**{**dict(row), 'id': str(row['id'])})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}/analysis", response_model=AnalysisResponse)
async def get_analysis_results(doc_id: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    """Get analysis results for a document."""
    try:
        # Get document status
        async with pool.acquire() as conn:
            doc_row = await conn.fetchrow("""
                SELECT status FROM doc_sources WHERE id = $1
            """, doc_id)

            if not doc_row:
                raise HTTPException(status_code=404, detail="Document not found")

            # Get endpoints
            endpoint_rows = await conn.fetch("""
                SELECT method, path, summary, description, ai_explanation,
                       parameters, request_body, responses, tags
                FROM doc_endpoints WHERE doc_source_id = $1
            """, doc_id)

            endpoints = [dict(row) for row in endpoint_rows]

            # Get schemas
            schema_rows = await conn.fetch("""
                SELECT schema_name, schema_type, properties, required_fields,
                       description, ai_explanation, generated_sql
                FROM doc_schemas WHERE doc_source_id = $1
            """, doc_id)

            schemas = {row['schema_name']: dict(row) for row in schema_rows}

            # Get summary
            analysis_row = await conn.fetchrow("""
                SELECT ai_summary FROM doc_analyses
                WHERE doc_source_id = $1 AND analysis_type = 'full'
                ORDER BY created_at DESC LIMIT 1
            """, doc_id)

            summary = analysis_row['ai_summary'] if analysis_row else ""

        return AnalysisResponse(
            doc_source_id=doc_id,
            status=doc_row['status'],
            summary=summary,
            endpoint_count=len(endpoints),
            schema_count=len(schemas),
            endpoints=endpoints,
            schemas=schemas,
            diagram=None  # TODO: Generate diagram
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{doc_id}/export/sheets")
async def export_to_google_sheets(doc_id: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    """Export analysis results to Google Sheets."""
    try:
        # Get document and analysis data
        async with pool.acquire() as conn:
            # Get document info
            doc_row = await conn.fetchrow("""
                SELECT id, name, status, source_url
                FROM doc_sources WHERE id = $1
            """, doc_id)

            if not doc_row:
                raise HTTPException(status_code=404, detail="Document not found")

            if doc_row['status'] != 'completed':
                raise HTTPException(
                    status_code=400,
                    detail=f"Document analysis not completed. Status: {doc_row['status']}"
                )

            # Get API metadata from source URL
            api_name = doc_row['name']
            api_version = "unknown"
            spec_version = "unknown"

            # Try to get version info from analysis
            analysis_row = await conn.fetchrow("""
                SELECT results FROM doc_analyses
                WHERE doc_source_id = $1 AND analysis_type = 'full'
                ORDER BY created_at DESC LIMIT 1
            """, doc_id)

            if analysis_row and analysis_row['results']:
                results = analysis_row['results']
                if isinstance(results, str):
                    results = json.loads(results)
                api_version = results.get('api_version', 'unknown')
                spec_version = results.get('spec_version', results.get('openapi_version', 'unknown'))

            # Get endpoints
            endpoint_rows = await conn.fetch("""
                SELECT method, path, summary, description, ai_explanation,
                       parameters, request_body, responses, tags
                FROM doc_endpoints
                WHERE doc_source_id = $1
                ORDER BY path, method
            """, doc_id)

            endpoints = [dict(row) for row in endpoint_rows]

            # Get schemas
            schema_rows = await conn.fetch("""
                SELECT schema_name, schema_type, properties, required_fields,
                       description, ai_explanation, generated_sql
                FROM doc_schemas
                WHERE doc_source_id = $1
                ORDER BY schema_name
            """, doc_id)

            schemas = {row['schema_name']: dict(row) for row in schema_rows}

            # Get summary
            summary_row = await conn.fetchrow("""
                SELECT ai_summary FROM doc_analyses
                WHERE doc_source_id = $1 AND analysis_type = 'full'
                ORDER BY created_at DESC LIMIT 1
            """, doc_id)

            summary = summary_row['ai_summary'] if summary_row else ""

        # Export to Google Sheets
        exporter = get_sheets_exporter()
        result = await exporter.export_analysis(
            doc_source_id=doc_id,
            api_name=api_name,
            api_version=api_version,
            spec_version=spec_version,
            endpoints=endpoints,
            schemas=schemas,
            summary=summary
        )

        # Save export record if successful
        if result.get('success'):
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO doc_exports (
                        doc_source_id, export_type, destination_url,
                        exported_endpoint_count, exported_schema_count,
                        status, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, doc_id, 'google_sheets', result.get('sheet_url'),
                    len(endpoints), len(schemas), 'completed',
                    json.dumps({'sheet_id': result.get('sheet_id')}))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export to Google Sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{doc_id}/analyze")
async def trigger_analysis(
    doc_id: str,
    background_tasks: BackgroundTasks,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Manually trigger analysis for a document."""
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM doc_sources WHERE id = $1", doc_id
            )

            if not row:
                raise HTTPException(status_code=404, detail="Document not found")

        background_tasks.add_task(_run_analysis, doc_id, pool)

        return {"message": "Analysis started", "doc_id": doc_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schemas/generate-sql")
async def generate_schema_sql(
    request: SchemaGenerateRequest,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Generate SQL CREATE TABLE statement for a schema."""
    try:
        async with pool.acquire() as conn:
            schema_row = await conn.fetchrow("""
                SELECT id, schema_name, schema_type, properties, required_fields, description
                FROM doc_schemas
                WHERE doc_source_id = $1 AND schema_name = $2
            """, request.doc_source_id, request.schema_name)

            if not schema_row:
                raise HTTPException(status_code=404, detail="Schema not found")

        schema_data = {
            'type': schema_row['schema_type'],
            'properties': schema_row['properties'],
            'required': schema_row['required_fields'] or [],
            'description': schema_row['description'] or ''
        }

        generator = SchemaGenerator(pool)
        sql = generator.generate_create_table_sql(
            request.schema_name,
            schema_data,
            request.include_audit_fields
        )

        # Execute if requested
        if request.execute_immediately:
            success = await generator.execute_create_table(sql, request.schema_name)
            table_name = generator.sanitize_table_name(request.schema_name)

            await generator.save_generated_schema(
                str(schema_row['id']),
                table_name,
                sql,
                "created" if success else "failed",
                None if success else "Execution failed"
            )

            return {
                "sql": sql,
                "executed": success,
                "table_name": table_name
            }

        return {"sql": sql, "executed": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate SQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    """Delete a documentation source and all its analysis data."""
    try:
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM doc_sources WHERE id = $1", doc_id
            )

            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Document not found")

        return {"message": "Document deleted successfully", "doc_id": doc_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(pool: asyncpg.Pool = Depends(get_db_pool)):
    """Get overall statistics for documentation analyzer."""
    try:
        async with pool.acquire() as conn:
            total_docs = await conn.fetchval(
                "SELECT COUNT(*) FROM doc_sources"
            )
            completed_docs = await conn.fetchval(
                "SELECT COUNT(*) FROM doc_sources WHERE status = 'completed'"
            )
            total_endpoints = await conn.fetchval(
                "SELECT COUNT(*) FROM doc_endpoints"
            )
            total_schemas = await conn.fetchval(
                "SELECT COUNT(*) FROM doc_schemas"
            )

        return {
            "total_documents": total_docs,
            "completed_analyses": completed_docs,
            "total_endpoints": total_endpoints,
            "total_schemas": total_schemas
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
