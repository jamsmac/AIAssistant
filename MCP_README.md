# 🔌 Model Context Protocol (MCP) Integration

## ✨ Overview

Your AI Assistant Platform now includes full MCP (Model Context Protocol) support! This allows Claude Desktop and other MCP-compatible clients to interact directly with your platform through a standardized protocol.

## 🎯 What Can You Do With MCP?

Through MCP, Claude Desktop can:

### 📁 Project Management
- Create new projects
- List all your projects
- Manage project details

### 💾 Database Operations
- Create custom databases with schemas
- Query and filter database records
- Add, update, and delete records
- List all databases in a project

### 🤖 AI Chat
- Send messages to AI with intelligent routing
- Access chat history and sessions
- Get real-time responses

### ⚙️ Workflows
- Execute AI-powered workflows
- List and manage workflows
- Track workflow execution

### 📊 Analytics
- Get platform statistics
- View AI model rankings
- Monitor usage and costs

## 🚀 Quick Setup

### 1. Installation

```bash
cd ~/autopilot-core

# Activate virtual environment
source venv/bin/activate

# Install MCP SDK (already done)
pip install 'mcp[cli]>=1.20.0'
```

### 2. Configure Claude Desktop

#### macOS

```bash
# Create config directory
mkdir -p ~/Library/Application\ Support/Claude

# Copy configuration
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude Desktop
```

#### Windows

```powershell
# Create config at: %APPDATA%\Claude\claude_desktop_config.json
# Copy contents from claude_desktop_config.json
# Restart Claude Desktop
```

#### Linux

```bash
# Create config directory
mkdir -p ~/.config/Claude

# Copy configuration
cp claude_desktop_config.json ~/.config/Claude/claude_desktop_config.json

# Restart Claude Desktop
```

### 3. Test MCP Server

```bash
# Run test suite
python test_mcp_server.py

# Expected output:
# ✅ Test 1 PASSED: 12 tools available
# ✅ Test 2 PASSED: Stats tool works
# ✅ Test 3 PASSED: List projects tool works
# ✅ Test 4 PASSED: Chat tool works
# ✅ Test 5 PASSED: Rankings tool works
```

## 📋 Available MCP Tools

### Project Management
| Tool | Description | Parameters |
|------|-------------|------------|
| `create_project` | Create a new project | name, description, user_id |
| `list_projects` | List all projects | user_id |

### Database Management
| Tool | Description | Parameters |
|------|-------------|------------|
| `create_database` | Create custom database | name, project_id, schema |
| `list_databases` | List databases | project_id |
| `query_database` | Query records | database_id, filters, limit |
| `create_record` | Create record | database_id, data |

### AI Chat
| Tool | Description | Parameters |
|------|-------------|------------|
| `chat` | Send AI message | prompt, task_type, budget, complexity |
| `list_chat_sessions` | List chat sessions | user_id |

### Workflows
| Tool | Description | Parameters |
|------|-------------|------------|
| `execute_workflow` | Execute workflow | workflow_id, input_data |
| `list_workflows` | List workflows | - |

### Analytics
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_stats` | Get statistics | days |
| `get_model_rankings` | Get AI rankings | - |

## 🎓 Usage Examples

### In Claude Desktop

Once configured, you can use natural language:

**Example 1: List Projects**
```
Can you show me all my projects using the MCP tools?
```

**Example 2: Create Database**
```
Create a new database called "customers" in project 1 with fields:
- name (text)
- email (text)
- created_at (date)
```

**Example 3: Chat with AI**
```
Use the chat tool to ask: "What's the best AI model for coding tasks?"
```

**Example 4: Get Analytics**
```
Show me platform statistics for the last 30 days
```

**Example 5: Execute Workflow**
```
Execute workflow ID 5 with input data: {"user_id": 1, "action": "process"}
```

### Manual Testing

```bash
# Test tool listing
python -c "
from agents.mcp_server import list_tools
import asyncio
tools = asyncio.run(list_tools())
print(f'Found {len(tools)} tools')
"

# Run full test suite
python test_mcp_server.py
```

## 🔧 Configuration

### Environment Variables

The MCP server uses these environment variables:

```bash
PYTHONPATH=/Users/js/autopilot-core
DATABASE_PATH=/Users/js/autopilot-core/data/history.db
GEMINI_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here
GROK_API_KEY=your-key-here
```

### Config File Location

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

### Config File Format

```json
{
  "mcpServers": {
    "ai-assistant-platform": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/agents/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/project",
        "DATABASE_PATH": "/path/to/database.db"
      }
    }
  }
}
```

## 🐛 Troubleshooting

### MCP Server Not Starting

**Problem:** Claude Desktop can't connect to MCP server

**Solutions:**

1. Check Python path is correct
2. Verify file permissions: `chmod +x agents/mcp_server.py`
3. Test manually: `./start_mcp_server.sh`
4. Check Claude Desktop logs: `~/Library/Logs/Claude/mcp-*.log`

### Tools Not Appearing

**Problem:** Claude Desktop doesn't show MCP tools

**Solutions:**

1. Restart Claude Desktop completely (Quit and reopen)
2. Verify config file location
3. Check config file syntax (valid JSON)
4. Test server: `python test_mcp_server.py`

### Import Errors

**Problem:** `ModuleNotFoundError` or import errors

**Solutions:**

1. Set PYTHONPATH: `export PYTHONPATH=/Users/js/autopilot-core`
2. Activate virtual environment: `source venv/bin/activate`
3. Reinstall dependencies: `pip install -r requirements.txt`

### Database Errors

**Problem:** Database not found or locked

**Solutions:**

1. Check database exists: `ls -la data/history.db`
2. Verify permissions: `chmod 644 data/history.db`
3. Initialize if missing: See setup guide

## 📚 Architecture

### MCP Server Architecture

```
┌─────────────────────────────────────────┐
│         Claude Desktop App              │
└──────────────┬──────────────────────────┘
               │ MCP Protocol (stdio)
               │
┌──────────────▼──────────────────────────┐
│         MCP Server (Python)             │
│  - Tool Registration                    │
│  - Request Handling                     │
│  - Response Formatting                  │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────▼─────┐   ┌──────▼────────┐
│ Database  │   │   AI Router   │
│  Module   │   │    Module     │
└───────────┘   └───────────────┘
```

### Communication Flow

1. **User Request** → Claude Desktop UI
2. **Tool Selection** → Claude selects appropriate MCP tool
3. **Tool Invocation** → MCP server receives request via stdio
4. **Processing** → Server executes tool logic
5. **Response** → Server returns JSON response
6. **Display** → Claude Desktop shows result to user

## 🔒 Security

### Best Practices

1. **API Keys:** Store in `.env`, never commit to git
2. **Database Access:** MCP has full access - use with trusted clients only
3. **Network:** MCP uses stdio (no network exposure)
4. **Validation:** All inputs are validated via Pydantic models

### Access Control

MCP server runs with same permissions as Claude Desktop. Consider:

- Read-only mode for sensitive operations
- Audit logging for all MCP requests
- Rate limiting for resource-intensive tools

## 📈 Performance

### Optimization Tips

1. **Caching:** AI responses are cached automatically
2. **Connection Pooling:** Database connections are reused
3. **Async Operations:** All tools use async/await
4. **Lazy Loading:** Modules loaded only when needed

### Monitoring

Check MCP server performance:

```bash
# View logs
tail -f ~/Library/Logs/Claude/mcp-*.log

# Monitor database
sqlite3 data/history.db "SELECT COUNT(*) FROM requests;"

# Check cache hit rate
python -c "from agents.database import HistoryDatabase; db = HistoryDatabase(); print(db.get_cache_stats())"
```

## 🎯 Next Steps

1. **Explore Tools:** Try all 12 MCP tools in Claude Desktop
2. **Build Workflows:** Create custom workflows using MCP
3. **Extend Server:** Add new tools for your specific needs
4. **Monitor Usage:** Track MCP tool usage and performance

## 📞 Support

- **Documentation:** [MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)
- **Testing:** `python test_mcp_server.py`
- **Logs:** `~/Library/Logs/Claude/mcp-*.log`
- **Issues:** Check [README.md](README.md) for troubleshooting

## 🌟 Features

### Current Features (v1.0)
- ✅ 12 MCP tools across 5 categories
- ✅ Full project and database management
- ✅ AI chat integration
- ✅ Workflow execution
- ✅ Real-time analytics
- ✅ Comprehensive error handling
- ✅ Pydantic validation
- ✅ Async/await support

### Planned Features (v1.1)
- 🔄 File upload/download
- 🔄 Webhook triggers
- 🔄 Batch operations
- 🔄 Advanced filtering
- 🔄 Data export (CSV, JSON)

## 🏆 Benefits

### For Developers
- **Standardized API:** MCP protocol is industry standard
- **Type Safety:** Pydantic models for all inputs/outputs
- **Easy Testing:** Comprehensive test suite included
- **Documentation:** Auto-generated from tool definitions

### For Users
- **Natural Language:** Use plain English in Claude Desktop
- **Visual Interface:** Claude Desktop's beautiful UI
- **Context Aware:** Claude remembers conversation context
- **Powerful:** Access all platform features

## 📊 Statistics

- **Tools:** 12 available tools
- **Categories:** 5 tool categories
- **Lines of Code:** ~500 in MCP server
- **Test Coverage:** 5 integration tests
- **Supported Clients:** Claude Desktop, MCP Inspector, Custom clients

---

## 🎉 Success!

Your AI Assistant Platform is now MCP-enabled! You can:

1. ✅ Use Claude Desktop to manage projects
2. ✅ Query databases with natural language
3. ✅ Execute AI workflows
4. ✅ Get real-time analytics
5. ✅ Build custom automations

**Next:** Open Claude Desktop and try: "List my projects using MCP tools"

**Built with ❤️ using Model Context Protocol**
