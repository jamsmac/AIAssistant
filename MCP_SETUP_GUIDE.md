# 🔧 MCP Setup Guide

Complete guide for setting up Model Context Protocol (MCP) for AI Assistant Platform.

## 📋 Overview

This guide will help you:
1. Install MCP dependencies
2. Configure Claude Desktop to use your MCP server
3. Test MCP tools
4. Troubleshoot common issues

## 🎯 What is MCP?

Model Context Protocol (MCP) is a standard protocol that allows AI assistants like Claude to interact with external tools and services. With MCP, Claude can:

- Create and manage projects
- Query and modify databases
- Execute AI workflows
- Get real-time analytics
- And much more!

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ~/autopilot-core

# Activate virtual environment
source venv/bin/activate

# Install MCP SDK
pip install 'mcp[cli]>=1.20.0'
```

### 2. Test MCP Server

```bash
# Test the MCP server locally
./start_mcp_server.sh
```

You should see:
```
🚀 Starting MCP Server for AI Assistant Platform...
📋 Loading environment variables from .env...
✨ MCP Server ready!
📡 Listening on stdio...
```

Press `Ctrl+C` to stop the server.

### 3. Configure Claude Desktop

#### macOS Configuration

1. **Locate Claude Desktop config file:**
   ```bash
   # Create directory if it doesn't exist
   mkdir -p ~/Library/Application\ Support/Claude
   ```

2. **Copy the configuration:**
   ```bash
   cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. **Verify the config:**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   Should show:
   ```json
   {
     "mcpServers": {
       "ai-assistant-platform": {
         "command": "/Users/js/autopilot-core/venv/bin/python",
         "args": [
           "/Users/js/autopilot-core/agents/mcp_server.py"
         ],
         "env": {
           "PYTHONPATH": "/Users/js/autopilot-core",
           "DATABASE_PATH": "/Users/js/autopilot-core/data/history.db"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop**
   - Quit Claude Desktop completely
   - Reopen Claude Desktop
   - MCP server will start automatically

#### Windows Configuration

1. **Locate Claude Desktop config file:**
   ```powershell
   # Path: %APPDATA%\Claude\claude_desktop_config.json
   ```

2. **Create config manually:**
   - Open: `C:\Users\YourUsername\AppData\Roaming\Claude\claude_desktop_config.json`
   - Update paths to match your installation

3. **Restart Claude Desktop**

#### Linux Configuration

1. **Locate Claude Desktop config file:**
   ```bash
   mkdir -p ~/.config/Claude
   cp claude_desktop_config.json ~/.config/Claude/claude_desktop_config.json
   ```

2. **Restart Claude Desktop**

## 🛠️ Available MCP Tools

Once configured, Claude Desktop will have access to these tools:

### 📁 Project Management
- `create_project` - Create a new project
- `list_projects` - List all projects

### 💾 Database Management
- `create_database` - Create a custom database with schema
- `list_databases` - List databases in a project
- `query_database` - Query records from a database
- `create_record` - Create a new record

### 🤖 AI Chat
- `chat` - Send message to AI with intelligent routing
- `list_chat_sessions` - List chat sessions

### ⚙️ Workflows
- `execute_workflow` - Execute an AI workflow
- `list_workflows` - List all workflows

### 📊 Analytics
- `get_stats` - Get platform statistics
- `get_model_rankings` - Get AI model rankings

## 🧪 Testing MCP Tools

### Test in Claude Desktop

After configuration, try these commands in Claude Desktop:

1. **List projects:**
   ```
   Can you list my projects using MCP?
   ```

2. **Get statistics:**
   ```
   Show me platform statistics for the last 7 days
   ```

3. **Chat with AI:**
   ```
   Use the chat tool to ask: "What is 2+2?"
   ```

4. **Get model rankings:**
   ```
   Show me the top AI model rankings
   ```

### Manual Testing

Test the MCP server directly:

```bash
cd ~/autopilot-core
source venv/bin/activate

# Test with mcp CLI
python -c "
from agents.mcp_server import list_tools
import asyncio
tools = asyncio.run(list_tools())
for tool in tools:
    print(f'✅ {tool.name}: {tool.description}')
"
```

## 🔍 Troubleshooting

### MCP Server Not Starting

**Issue:** Claude Desktop can't connect to MCP server

**Solutions:**

1. **Check Python path:**
   ```bash
   which python
   # Should be: /Users/js/autopilot-core/venv/bin/python
   ```

2. **Check file permissions:**
   ```bash
   chmod +x start_mcp_server.sh
   chmod +x agents/mcp_server.py
   ```

3. **Test manually:**
   ```bash
   ./start_mcp_server.sh
   # Should start without errors
   ```

4. **Check logs:**
   - macOS: `~/Library/Logs/Claude/mcp-*.log`
   - Check for error messages

### Import Errors

**Issue:** `ModuleNotFoundError: No module named 'agents'`

**Solutions:**

1. **Check PYTHONPATH:**
   ```bash
   export PYTHONPATH="/Users/js/autopilot-core"
   ```

2. **Update config:**
   Add to `claude_desktop_config.json`:
   ```json
   "env": {
     "PYTHONPATH": "/Users/js/autopilot-core"
   }
   ```

3. **Reinstall dependencies:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Database Errors

**Issue:** `sqlite3.OperationalError: no such table`

**Solutions:**

1. **Initialize database:**
   ```bash
   cd ~/autopilot-core
   source venv/bin/activate
   python -c "from agents.database import Database; db = Database()"
   ```

2. **Check database path:**
   ```bash
   ls -la data/history.db
   # Should exist
   ```

3. **Verify permissions:**
   ```bash
   chmod 644 data/history.db
   ```

### Tools Not Appearing

**Issue:** Claude Desktop doesn't show MCP tools

**Solutions:**

1. **Restart Claude Desktop:**
   - Completely quit the app
   - Reopen

2. **Check config location:**
   ```bash
   # macOS
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

   # Should contain mcpServers configuration
   ```

3. **Verify MCP server is running:**
   - Check Claude Desktop logs
   - Test server manually

## 📚 Advanced Configuration

### Custom Environment Variables

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-assistant-platform": {
      "command": "/Users/js/autopilot-core/venv/bin/python",
      "args": [
        "/Users/js/autopilot-core/agents/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/js/autopilot-core",
        "DATABASE_PATH": "/Users/js/autopilot-core/data/history.db",
        "LOG_LEVEL": "INFO",
        "GEMINI_API_KEY": "your-key-here",
        "OPENROUTER_API_KEY": "your-key-here"
      }
    }
  }
}
```

### Multiple MCP Servers

You can run multiple MCP servers:

```json
{
  "mcpServers": {
    "ai-assistant-platform": {
      "command": "/Users/js/autopilot-core/venv/bin/python",
      "args": ["/Users/js/autopilot-core/agents/mcp_server.py"]
    },
    "another-server": {
      "command": "node",
      "args": ["/path/to/another/server.js"]
    }
  }
}
```

## 🔒 Security Considerations

### API Keys

- **Never commit** API keys to git
- Store in `.env` file (gitignored)
- Pass through environment variables in MCP config

### Database Access

- MCP server has **full access** to your database
- Only use with trusted AI assistants
- Consider read-only mode for production

### Network Access

- MCP uses stdio (standard input/output)
- No network exposure by default
- Safe for local development

## 🎓 Learning More

### MCP Documentation

- **Official Docs:** https://modelcontextprotocol.io/
- **Python SDK:** https://github.com/modelcontextprotocol/python-sdk
- **Examples:** https://github.com/modelcontextprotocol/servers

### AI Assistant Platform

- **README:** [README.md](README.md)
- **API Docs:** http://localhost:8000/docs
- **Deployment:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## 📞 Support

Having issues? Try these resources:

1. **Check logs:**
   ```bash
   tail -f ~/Library/Logs/Claude/mcp-*.log
   ```

2. **Test components:**
   ```bash
   # Test database
   python -c "from agents.database import Database; print(Database().get_statistics())"

   # Test AI router
   python -c "from agents.ai_router import AIRouter; print('AI Router OK')"
   ```

3. **Restart everything:**
   ```bash
   # Kill any running servers
   pkill -f "mcp_server.py"

   # Restart Claude Desktop
   # Restart backend: python api/server.py
   ```

## ✅ Success Checklist

- [ ] MCP SDK installed (`pip list | grep mcp`)
- [ ] Config file created at correct location
- [ ] Python paths are correct
- [ ] Database exists and is accessible
- [ ] Environment variables loaded
- [ ] Claude Desktop restarted
- [ ] Tools appear in Claude Desktop
- [ ] Test queries work successfully

---

## 🎉 You're All Set!

Your AI Assistant Platform is now connected to Claude Desktop via MCP. You can now:

- Create projects and databases through Claude
- Query data using natural language
- Execute AI workflows
- Get real-time analytics
- And much more!

**Next Steps:**
1. Try the test queries above
2. Explore available tools
3. Build custom workflows
4. Share feedback!

**Built with ❤️ using Model Context Protocol**
