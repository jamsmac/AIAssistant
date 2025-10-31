# Quick Prompts for AI Development System

## 📁 File References
Always mention files with @:
```
@database.py explain caching
@ai_router.py add retry logic
@chat/page.tsx fix loading state
```

## 🔍 Analysis
```
Explain how @ai_router.py selects models
Show me all API endpoints in @server.py
What does session_id do in @database.py
```

## 🛠️ Adding Features
```
@database.py add method to get user stats (requests, tokens, cost)
@server.py create POST /api/users endpoint with validation
@chat/page.tsx add export chat to PDF button
```

## 🐛 Fixing Bugs
```
@ai_router.py rate limiting not working, fix it
@chat/page.tsx context memory counter not updating
The streaming endpoint returns 500 error, debug it
```

## 🎨 UI Changes
```
@chat/page.tsx add dark/light theme toggle
@models-ranking/page.tsx make fully responsive (mobile/tablet/desktop)
Add loading skeleton to dashboard widgets
```

## 📊 Database
```
@database.py optimize get_performance_analytics query
Add index to requests table on timestamp column
Create migration to add users table
```

## 🧪 Testing
```
Write unit tests for @database.py cache methods
Create test script for streaming endpoint with 5 parallel requests
Add integration test for chat with context
```

## 🚀 Good Prompt Structure
1. **Action**: what to do
2. **Location**: which file (@filename)
3. **Details**: specific requirements
4. **Test**: how to verify

Example:
```
@database.py add method get_model_usage(days=7) that returns:
- model name
- total requests
- success rate
- total cost
Return as List[Dict]. Add docstring. Then show test command.
```

## 💡 Tips
- Open relevant files before asking
- Use @ to reference files
- Ask for explanation if unclear
- Request test commands
- One task at a time
```