#!/usr/bin/env python3
"""
MCP Server for AI Assistant Platform

Provides MCP tools for:
- Database operations (projects, databases, records)
- AI chat and routing
- Workflow execution
- Integration management
- Analytics and stats
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import BaseModel, Field

# Import local modules (when running as part of the platform)
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.database import HistoryDatabase as Database
    from agents.ai_router import AIRouter
    from agents.workflow_engine import WorkflowEngine
    LOCAL_IMPORTS = True
except ImportError as e:
    LOCAL_IMPORTS = False
    Database = None
    AIRouter = None
    WorkflowEngine = None
    logging.warning(f"Local modules not available. Running in standalone mode. Error: {e}")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for tool arguments
class ProjectCreateArgs(BaseModel):
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    user_id: int = Field(description="User ID", default=1)


class DatabaseCreateArgs(BaseModel):
    name: str = Field(description="Database name")
    project_id: int = Field(description="Project ID")
    schema_definition: Dict[str, Any] = Field(description="Database schema definition", alias="schema")


class DatabaseQueryArgs(BaseModel):
    database_id: int = Field(description="Database ID")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Query filters")
    limit: Optional[int] = Field(default=100, description="Maximum results")


class RecordCreateArgs(BaseModel):
    database_id: int = Field(description="Database ID")
    data: Dict[str, Any] = Field(description="Record data")


class ChatArgs(BaseModel):
    prompt: str = Field(description="User message/prompt")
    task_type: str = Field(default="general", description="Task type: general, code, math, analysis")
    budget: str = Field(default="balanced", description="Budget: free, balanced, premium")
    complexity: str = Field(default="medium", description="Complexity: low, medium, high")
    session_id: Optional[int] = Field(default=None, description="Chat session ID")


class WorkflowExecuteArgs(BaseModel):
    workflow_id: int = Field(description="Workflow ID")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Input data for workflow")


class StatsArgs(BaseModel):
    days: Optional[int] = Field(default=7, description="Number of days for stats")


# Initialize MCP Server
mcp_server = Server("ai-assistant-platform")


# Database connection (lazy initialization)
_db: Optional[Database] = None
_ai_router: Optional[AIRouter] = None
_workflow_engine: Optional[WorkflowEngine] = None


def get_db() -> Database:
    """Get database instance (lazy initialization)"""
    global _db
    if _db is None and LOCAL_IMPORTS:
        _db = Database()
    return _db


def get_ai_router() -> AIRouter:
    """Get AI router instance (lazy initialization)"""
    global _ai_router
    if _ai_router is None and LOCAL_IMPORTS:
        _ai_router = AIRouter()
    return _ai_router


def get_workflow_engine() -> WorkflowEngine:
    """Get workflow engine instance (lazy initialization)"""
    global _workflow_engine
    if _workflow_engine is None and LOCAL_IMPORTS:
        _workflow_engine = WorkflowEngine(get_db())
    return _workflow_engine


# === TOOLS REGISTRATION ===

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        # Project Management
        Tool(
            name="create_project",
            description="Create a new project in the AI Assistant Platform",
            inputSchema=ProjectCreateArgs.model_json_schema()
        ),
        Tool(
            name="list_projects",
            description="List all projects for a user",
            inputSchema={"type": "object", "properties": {"user_id": {"type": "integer"}}}
        ),

        # Database Management
        Tool(
            name="create_database",
            description="Create a new custom database with schema",
            inputSchema=DatabaseCreateArgs.model_json_schema()
        ),
        Tool(
            name="list_databases",
            description="List all databases in a project",
            inputSchema={"type": "object", "properties": {"project_id": {"type": "integer"}}}
        ),
        Tool(
            name="query_database",
            description="Query records from a database",
            inputSchema=DatabaseQueryArgs.model_json_schema()
        ),
        Tool(
            name="create_record",
            description="Create a new record in a database",
            inputSchema=RecordCreateArgs.model_json_schema()
        ),

        # AI Chat
        Tool(
            name="chat",
            description="Send a message to AI assistant with intelligent model routing",
            inputSchema=ChatArgs.model_json_schema()
        ),
        Tool(
            name="list_chat_sessions",
            description="List all chat sessions for a user",
            inputSchema={"type": "object", "properties": {"user_id": {"type": "integer", "default": 1}}}
        ),

        # Workflows
        Tool(
            name="execute_workflow",
            description="Execute an AI workflow",
            inputSchema=WorkflowExecuteArgs.model_json_schema()
        ),
        Tool(
            name="list_workflows",
            description="List all workflows for a user",
            inputSchema={"type": "object", "properties": {"user_id": {"type": "integer", "default": 1}}}
        ),

        # Analytics
        Tool(
            name="get_stats",
            description="Get platform statistics and analytics",
            inputSchema=StatsArgs.model_json_schema()
        ),
        Tool(
            name="get_model_rankings",
            description="Get AI model rankings by category",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


# === TOOL IMPLEMENTATIONS ===

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute MCP tool"""

    logger.info(f"Executing tool: {name} with args: {arguments}")

    try:
        if not LOCAL_IMPORTS:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Platform modules not available. Running in standalone mode.",
                    "tool": name
                })
            )]

        # Project Management Tools
        if name == "create_project":
            args = ProjectCreateArgs(**arguments)
            db = get_db()
            project_id = db.create_project(
                user_id=args.user_id,
                name=args.name,
                description=args.description
            )
            project = db.get_project(project_id, args.user_id)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "project": project,
                    "project_id": project_id,
                    "message": f"Project '{args.name}' created successfully"
                }, default=str)
            )]

        elif name == "list_projects":
            user_id = arguments.get("user_id", 1)
            db = get_db()
            projects = db.get_projects(user_id)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "projects": projects,
                    "count": len(projects)
                }, default=str)
            )]

        # Database Management Tools
        elif name == "create_database":
            args = DatabaseCreateArgs(**arguments)
            db = get_db()
            # Convert schema dict to JSON string
            schema_json = json.dumps(args.schema_definition)
            database_id = db.create_database(
                project_id=args.project_id,
                name=args.name,
                schema_json=schema_json
            )
            database = db.get_database(database_id)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "database": database,
                    "database_id": database_id,
                    "message": f"Database '{args.name}' created successfully"
                }, default=str)
            )]

        elif name == "list_databases":
            project_id = arguments.get("project_id")
            db = get_db()
            databases = db.get_databases(project_id=project_id)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "databases": databases,
                    "count": len(databases)
                }, default=str)
            )]

        elif name == "query_database":
            args = DatabaseQueryArgs(**arguments)
            db = get_db()
            # get_records takes database_id, limit, offset (not filters)
            # For now, we'll ignore filters and use limit
            records = db.get_records(
                database_id=args.database_id,
                limit=args.limit or 100,
                offset=0
            )
            # Apply filters in memory if provided
            if args.filters:
                filtered_records = []
                for record in records:
                    match = True
                    for key, value in args.filters.items():
                        record_data = json.loads(record.get('data_json', '{}'))
                        if record_data.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered_records.append(record)
                records = filtered_records
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "records": records,
                    "count": len(records)
                }, default=str)
            )]

        elif name == "create_record":
            args = RecordCreateArgs(**arguments)
            db = get_db()
            # Convert data dict to JSON string
            data_json = json.dumps(args.data)
            record_id = db.create_record(
                database_id=args.database_id,
                data_json=data_json
            )
            record = db.get_record(record_id)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "record": record,
                    "record_id": record_id,
                    "message": "Record created successfully"
                }, default=str)
            )]

        # AI Chat Tools
        elif name == "chat":
            args = ChatArgs(**arguments)
            router = get_ai_router()

            # Convert complexity string to int (low=3, medium=5, high=8)
            complexity_map = {"low": 3, "medium": 5, "high": 8}
            complexity_int = complexity_map.get(args.complexity.lower(), 5)

            # Route request to appropriate model
            response = router.route(
                prompt=args.prompt,
                task_type=args.task_type,
                budget=args.budget,
                complexity=complexity_int,
                session_id=str(args.session_id) if args.session_id else None
            )

            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "response": response.get("response"),
                    "model": response.get("model"),
                    "tokens": response.get("tokens"),
                    "cost": response.get("cost"),
                    "cached": response.get("cached", False)
                }, default=str)
            )]

        elif name == "list_chat_sessions":
            user_id = arguments.get("user_id", 1)
            db = get_db()
            # get_chat_sessions method doesn't exist yet
            # Return empty list for now
            sessions = []
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "sessions": sessions,
                    "count": len(sessions),
                    "note": "Chat sessions feature not yet implemented"
                }, default=str)
            )]

        # Workflow Tools
        elif name == "execute_workflow":
            args = WorkflowExecuteArgs(**arguments)
            engine = get_workflow_engine()
            result = await engine.execute_workflow(
                workflow_id=args.workflow_id,
                input_data=args.input_data or {}
            )
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": result.get("success", False),
                    "result": result,
                    "message": result.get("message", "Workflow executed")
                }, default=str)
            )]

        elif name == "list_workflows":
            user_id = arguments.get("user_id", 1)
            db = get_db()
            workflows = db.get_workflows(user_id)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "workflows": workflows,
                    "count": len(workflows)
                }, default=str)
            )]

        # Analytics Tools
        elif name == "get_stats":
            args = StatsArgs(**arguments)
            db = get_db()
            # get_stats() doesn't take days parameter, but returns last 7 days by default
            stats = db.get_stats()
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "stats": stats,
                    "period": f"Last {args.days or 7} days"
                }, default=str)
            )]

        elif name == "get_model_rankings":
            db = get_db()
            rankings = db.get_all_rankings()
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "rankings": rankings,
                    "count": len(rankings)
                }, default=str)
            )]

        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}",
                    "available_tools": [
                        "create_project", "list_projects",
                        "create_database", "list_databases", "query_database", "create_record",
                        "chat", "list_chat_sessions",
                        "execute_workflow", "list_workflows",
                        "get_stats", "get_model_rankings"
                    ]
                })
            )]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "arguments": arguments
            })
        )]


# === SERVER STARTUP ===

async def main():
    """Run MCP server"""
    logger.info("Starting AI Assistant Platform MCP Server...")
    logger.info(f"Local imports available: {LOCAL_IMPORTS}")

    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
