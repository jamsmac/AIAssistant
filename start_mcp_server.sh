#!/bin/bash
# Start MCP Server for AI Assistant Platform

set -e

echo "🚀 Starting MCP Server for AI Assistant Platform..."

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="/Users/js/autopilot-core"
export DATABASE_PATH="/Users/js/autopilot-core/data/history.db"

# Load .env file if exists
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if database exists
if [ ! -f "$DATABASE_PATH" ]; then
    echo "⚠️  Database not found at $DATABASE_PATH"
    echo "📊 Creating database..."
    python -c "from agents.database import Database; db = Database(); print('✅ Database initialized')"
fi

# Start MCP server
echo "✨ MCP Server ready!"
echo "📡 Listening on stdio..."
python agents/mcp_server.py
