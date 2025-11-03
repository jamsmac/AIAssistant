# 🤖 CLAUDE CODE PROMPTS - Ready to Copy & Paste

**Для использования в Cursor с Claude Code**

**Как использовать:**
1. Открой Cursor
2. Открой файл который нужно создать/изменить
3. Открой Claude Code (Cmd+Shift+P → "Claude Code")
4. Вставь промпт
5. Claude генерирует код
6. Review → Accept → Done!

---

## 📅 DAY 1 PROMPTS

### **TASK 1.1: Extend Database Schema**

**File:** `agents/database.py`

**Prompt:**
```
I have an existing HistoryDatabase class in this file that manages 6 tables (requests, users, chat_sessions, session_messages, request_cache, ai_model_rankings).

Add 6 new tables to support Projects, Databases, Workflows, and Integrations:

NEW TABLES:

1. projects
   - id INTEGER PRIMARY KEY
   - user_id INTEGER (FK to users)
   - name TEXT NOT NULL
   - description TEXT
   - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - INDEX on user_id

2. databases
   - id INTEGER PRIMARY KEY
   - project_id INTEGER (FK to projects)
   - name TEXT NOT NULL
   - schema_json TEXT (JSON string with column definitions)
   - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - INDEX on project_id

3. database_records
   - id INTEGER PRIMARY KEY
   - database_id INTEGER (FK to databases)
   - data_json TEXT (JSON string with record data)
   - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - INDEX on database_id

4. workflows
   - id INTEGER PRIMARY KEY
   - user_id INTEGER (FK to users)
   - name TEXT NOT NULL
   - trigger_type TEXT (manual, schedule, webhook, etc.)
   - trigger_config TEXT (JSON)
   - actions_json TEXT (JSON array of actions)
   - enabled BOOLEAN DEFAULT 1
   - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - INDEX on user_id

5. workflow_executions
   - id INTEGER PRIMARY KEY
   - workflow_id INTEGER (FK to workflows)
   - status TEXT (success, failed, running)
   - result_json TEXT (JSON with execution details)
   - error TEXT NULL
   - executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - INDEX on workflow_id

6. integration_tokens
   - id INTEGER PRIMARY KEY
   - user_id INTEGER (FK to users)
   - integration_type TEXT (gmail, google_drive, telegram)
   - access_token TEXT
   - refresh_token TEXT
   - expires_at TIMESTAMP
   - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - INDEX on (user_id, integration_type)

Add these tables to __init__ method, create them in _create_tables().

Also add corresponding methods:

Projects:
- create_project(user_id, name, description) -> int
- get_projects(user_id) -> List[Dict]
- get_project(project_id, user_id) -> Dict
- update_project(project_id, user_id, name, description) -> bool
- delete_project(project_id, user_id) -> bool

Databases:
- create_database(project_id, name, schema_json) -> int
- get_databases(project_id) -> List[Dict]
- get_database(database_id) -> Dict
- delete_database(database_id) -> bool

Database Records:
- create_record(database_id, data_json) -> int
- get_records(database_id, limit=100, offset=0) -> List[Dict]
- get_record(record_id) -> Dict
- update_record(record_id, data_json) -> bool
- delete_record(record_id) -> bool

Workflows:
- create_workflow(user_id, name, trigger_type, trigger_config, actions_json) -> int
- get_workflows(user_id) -> List[Dict]
- get_workflow(workflow_id, user_id) -> Dict
- update_workflow(workflow_id, user_id, **kwargs) -> bool
- delete_workflow(workflow_id, user_id) -> bool

Workflow Executions:
- create_execution(workflow_id, status, result_json, error=None) -> int
- get_executions(workflow_id, limit=50) -> List[Dict]

Integration Tokens:
- save_integration_token(user_id, integration_type, access_token, refresh_token, expires_at) -> int
- get_integration_token(user_id, integration_type) -> Dict
- delete_integration_token(user_id, integration_type) -> bool

Keep existing methods and tables intact. Use same patterns (with sqlite3.connect, row_factory, etc.).
```

---

### **TASK 1.2A: File Upload in Chat**

**File:** `app/chat/page.tsx`

**Prompt:**
```
This is a chat interface built with Next.js 14 and Tailwind CSS.

Add file upload functionality:

1. Add file input button next to the message input field:
   - Icon: Paperclip from lucide-react
   - Accept: .pdf, .jpg, .jpeg, .png, .txt
   - Show selected file name below input
   - "Remove" button to clear selection

2. When file is selected:
   - Extract text from file (if PDF/image, use OCR or pdf.js)
   - For images: convert to base64
   - For PDF: use pdf.js to extract text
   - For text files: read directly

3. When sending message with file:
   - Include file content in API request
   - Format: { prompt: "...", file: { name: "...", type: "...", content: "..." } }
   - Show file preview in chat message
   - Display file name and type

4. UI elements:
   - File preview card with icon and name
   - Loading state while processing file
   - Error message if file too large (>10MB) or unsupported

Use existing dark theme styling (bg-gray-900, text-white).
Keep existing functionality (streaming, session memory, etc.).
Add error handling for file processing.
```

---

### **TASK 1.2B: Chat History Sidebar**

**File:** `app/chat/page.tsx`

**Prompt:**
```
Add a collapsible left sidebar for chat history:

SIDEBAR DESIGN:
- Width: 280px when open, 0px when closed
- Toggle button: Chevron icon (left/right)
- Dark background: bg-gray-800
- Border-right: border-gray-700

SIDEBAR CONTENT:
1. Header:
   - "Chat History" title
   - "New Chat" button (+ icon)

2. Session List:
   - Fetch from GET /api/sessions
   - Each item shows:
     * First message preview (truncated)
     * Timestamp (relative: "2h ago")
     * Hover: Show delete button
   - Active session highlighted
   - Click to load session

3. Search:
   - Search input at top
   - Filter sessions by message content
   - Debounced search (300ms)

4. Loading states:
   - Skeleton loaders for sessions
   - Empty state: "No chat history"

FUNCTIONALITY:
- Load sessions on mount
- Click session → load messages
- Delete session → confirmation modal → DELETE /api/sessions/{id}
- New Chat → clear current, create new session
- Auto-close on mobile (<768px)

Keep existing chat functionality intact.
Use existing styling and components.
```

---

### **TASK 1.2C: Voice Input**

**File:** `app/chat/page.tsx`

**Prompt:**
```
Add voice input using browser SpeechRecognition API:

BUTTON:
- Icon: Mic from lucide-react
- Position: Next to send button
- States: idle (gray), listening (red pulsing), processing (spinner)

FUNCTIONALITY:
1. Click to start:
   - Check browser support (window.webkitSpeechRecognition || window.SpeechRecognition)
   - Show "Speak now..." placeholder
   - Start recognition with continuous=true, interimResults=true

2. While listening:
   - Show interim results in input field
   - Red pulsing animation on mic button
   - "Stop" label below button

3. On result:
   - Insert final transcript into input field
   - Stop recognition
   - User can edit before sending

4. Error handling:
   - No browser support: Show message "Voice input not supported"
   - Microphone permission denied: Show error
   - Recognition error: Retry or show error

ADDITIONAL:
- Keyboard shortcut: Ctrl+Shift+V to toggle
- Language: Auto-detect or default to user language
- Mobile support: Use native recognition if available

Use existing styling. Add subtle animations for feedback.
```

---

### **TASK 1.3: Fix Rankings Endpoint**

**File:** `agents/database.py`

**Prompt:**
```
Add get_all_rankings() method to HistoryDatabase class:

METHOD: get_all_rankings() -> List[Dict]

IMPLEMENTATION:
1. Query ai_model_rankings table
2. Group by model
3. Calculate aggregates for each model:
   - AVG(quality_score) as avg_quality
   - AVG(speed_score) as avg_speed
   - AVG(cost_score) as avg_cost
   - AVG(creativity_score) as avg_creativity
   - AVG(accuracy_score) as avg_accuracy
   - AVG(context_score) as avg_context
   - AVG(overall_score) as avg_overall
   - COUNT(*) as total_rankings

4. Return list of dicts:
   [{
     "model": "claude-sonnet-4-20250514",
     "avg_quality": 4.5,
     "avg_speed": 4.2,
     "avg_cost": 3.0,
     "avg_creativity": 4.8,
     "avg_accuracy": 4.6,
     "avg_context": 4.7,
     "avg_overall": 4.4,
     "total_rankings": 150
   }, ...]

5. Order by avg_overall DESC

Use existing patterns (with sqlite3.connect, row_factory, dict(row)).
```

**File:** `api/server.py`

**Prompt:**
```
Fix /api/rankings endpoint:

Current error: 'HistoryDatabase' object has no attribute 'get_all_rankings'

Fix: Call the newly added get_all_rankings() method:

@app.get("/api/rankings")
async def get_rankings():
    """Get AI model rankings"""
    try:
        db = get_db()
        rankings = db.get_all_rankings()
        return {
            "success": True,
            "rankings": rankings,
            "count": len(rankings)
        }
    except Exception as e:
        logger.error(f"Rankings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

Also update RankingsResponse Pydantic model if needed.
```

---

### **TASK 2.1: Projects API**

**File:** `api/server.py`

**Prompt:**
```
Add projects management API endpoints after existing endpoints:

PYDANTIC MODELS (add at top with other models):

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ProjectResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    created_at: str
    database_count: int = 0

ENDPOINTS:

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreate,
    token_data: dict = Depends(verify_jwt_token)
):
    """Create new project"""
    try:
        db = get_db()
        project_id = db.create_project(
            user_id=token_data['user_id'],
            name=request.name,
            description=request.description
        )
        project = db.get_project(project_id, token_data['user_id'])
        return ProjectResponse(**project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects", response_model=List[ProjectResponse])
async def list_projects(token_data: dict = Depends(verify_jwt_token)):
    """List all user's projects"""
    try:
        db = get_db()
        projects = db.get_projects(token_data['user_id'])
        return [ProjectResponse(**p) for p in projects]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    token_data: dict = Depends(verify_jwt_token)
):
    """Get project details"""
    try:
        db = get_db()
        project = db.get_project(project_id, token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectResponse(**project)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    request: ProjectUpdate,
    token_data: dict = Depends(verify_jwt_token)
):
    """Update project"""
    try:
        db = get_db()
        success = db.update_project(
            project_id=project_id,
            user_id=token_data['user_id'],
            name=request.name,
            description=request.description
        )
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        project = db.get_project(project_id, token_data['user_id'])
        return ProjectResponse(**project)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: int,
    token_data: dict = Depends(verify_jwt_token)
):
    """Delete project"""
    try:
        db = get_db()
        success = db.delete_project(project_id, token_data['user_id'])
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "message": "Project deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

Add proper error handling, logging, and type hints.
Keep existing endpoints intact.
```

---

### **TASK 2.2: Databases API**

**File:** `api/server.py`

**Prompt:**
```
Add custom databases API endpoints:

PYDANTIC MODELS:

class DatabaseSchema(BaseModel):
    columns: List[Dict[str, Any]] = Field(..., description="Column definitions")
    # Example: [{"name": "title", "type": "text", "required": true}, ...]

class DatabaseCreate(BaseModel):
    project_id: int
    name: str = Field(..., min_length=1, max_length=100)
    schema: DatabaseSchema

class DatabaseResponse(BaseModel):
    id: int
    project_id: int
    name: str
    schema: DatabaseSchema
    record_count: int = 0
    created_at: str

class RecordCreate(BaseModel):
    data: Dict[str, Any] = Field(..., description="Record data matching schema")

class RecordResponse(BaseModel):
    id: int
    database_id: int
    data: Dict[str, Any]
    created_at: str
    updated_at: str

ENDPOINTS:

@app.post("/api/databases", response_model=DatabaseResponse)
@app.get("/api/databases", response_model=List[DatabaseResponse])
@app.get("/api/databases/{database_id}", response_model=DatabaseResponse)
@app.delete("/api/databases/{database_id}")

@app.post("/api/databases/{database_id}/records", response_model=RecordResponse)
@app.get("/api/databases/{database_id}/records", response_model=List[RecordResponse])
@app.get("/api/databases/{database_id}/records/{record_id}", response_model=RecordResponse)
@app.put("/api/databases/{database_id}/records/{record_id}", response_model=RecordResponse)
@app.delete("/api/databases/{database_id}/records/{record_id}")

Include:
- Schema validation (check column types match data)
- Required fields validation
- JWT auth on all endpoints
- Error handling
- Pagination for records (limit=100, offset=0)

Column types supported: text, number, boolean, date, select
For select type, validate value is in options list.
```

---

### **TASK 2.3: Projects Frontend**

**File:** `app/projects/page.tsx`

**Prompt:**
```
Create projects management page:

LAYOUT:
- Header with "Projects" title
- "New Project" button (gradient, top-right)
- Grid of project cards (3 columns on desktop, 1 on mobile)

PROJECT CARD:
- Dark card with hover effect
- Project name (text-xl, font-bold)
- Description (text-gray-400, truncated)
- Database count badge
- Created date (relative: "2 days ago")
- Click → navigate to /projects/[id]

NEW PROJECT MODAL:
- Form with name and description inputs
- "Create" button (disabled if name empty)
- Close on backdrop click or X button
- POST /api/projects
- On success: close modal, refresh list

FUNCTIONALITY:
- Fetch projects on mount from GET /api/projects
- Loading state: skeleton cards
- Empty state: "No projects yet. Create your first project!"
- Error handling: toast notification
- Auth: redirect to /login if no token

STYLING:
- Dark theme (bg-gray-900)
- Cards: bg-gray-800 with border-gray-700
- Gradient button: from-blue-500 to-purple-500
- Rounded-xl, shadow-lg
- Smooth animations

Use 'use client', useState, useEffect.
Add lucide-react icons.
```

---

## 📅 DAY 2 PROMPTS

### **TASK 3.1: Workflow Engine**

**File:** `agents/workflow_engine.py` (new file)

**Prompt:**
```
Create a workflow execution engine:

CLASS: WorkflowEngine

INIT:
- Initialize database connection
- Load MCP client (for integrations)
- Setup logger

TRIGGERS (support these 5):
1. manual - Execute on demand
2. schedule - Cron expression (future: use APScheduler)
3. webhook - HTTP POST receives payload
4. email_received - New email in Gmail (via MCP)
5. record_created - New database record

ACTIONS (support these 10):
1. send_email - Send via Gmail MCP
2. create_record - Add to database
3. call_webhook - HTTP POST
4. run_ai_agent - Execute AI Router
5. send_notification - Log message
6. update_record - Update database record
7. delete_record - Delete from database
8. send_telegram - Send via Telegram MCP
9. create_project - Create new project
10. execute_workflow - Chain another workflow

METHODS:

def execute(self, workflow_id: int) -> Dict:
    """
    Execute workflow by ID
    
    1. Load workflow from database
    2. Check if enabled
    3. Parse trigger config
    4. Execute each action sequentially
    5. Log execution
    6. Return results
    """

def execute_action(self, action: Dict) -> Dict:
    """
    Execute single action
    
    action = {
        "type": "send_email",
        "config": {"to": "...", "subject": "...", "body": "..."}
    }
    
    Returns: {"success": True/False, "result": ..., "error": ...}
    """

def parse_variables(self, text: str, context: Dict) -> str:
    """
    Replace {{variables}} in text
    
    Example: "Hello {{user.name}}" with context={"user": {"name": "John"}}
    Returns: "Hello John"
    """

ERROR HANDLING:
- Try/except for each action
- Continue on action failure (don't stop workflow)
- Log errors
- Return detailed error info

Use type hints, docstrings, logging.
Keep it simple - MVP functionality only.
```

---

### **TASK 3.2: Workflows API**

**File:** `api/server.py`

**Prompt:**
```
Add workflows management API:

PYDANTIC MODELS:

class WorkflowTrigger(BaseModel):
    type: Literal['manual', 'schedule', 'webhook', 'email_received', 'record_created']
    config: Dict[str, Any] = {}

class WorkflowAction(BaseModel):
    type: str  # send_email, create_record, etc.
    config: Dict[str, Any]

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    trigger: WorkflowTrigger
    actions: List[WorkflowAction] = Field(..., min_items=1)
    enabled: bool = True

class WorkflowResponse(BaseModel):
    id: int
    user_id: int
    name: str
    trigger: WorkflowTrigger
    actions: List[WorkflowAction]
    enabled: bool
    created_at: str
    last_executed_at: Optional[str] = None

class ExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    status: Literal['success', 'failed', 'running']
    result: Dict[str, Any]
    error: Optional[str]
    executed_at: str

ENDPOINTS:

@app.post("/api/workflows", response_model=WorkflowResponse)
async def create_workflow(...)

@app.get("/api/workflows", response_model=List[WorkflowResponse])
async def list_workflows(...)

@app.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(...)

@app.put("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(...)

@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(...)

@app.post("/api/workflows/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(...):
    """Execute workflow manually"""
    from workflow_engine import WorkflowEngine
    engine = WorkflowEngine()
    result = engine.execute(workflow_id)
    # Save execution to database
    # Return execution result

@app.get("/api/workflows/{workflow_id}/executions", response_model=List[ExecutionResponse])
async def list_executions(...)

All endpoints require JWT auth.
Parse JSON columns (trigger, actions) before returning.
```

---

### **TASK 3.3: Workflows UI**

**File:** `app/workflows/page.tsx`

**Prompt:**
```
Create workflows management page:

LAYOUT:
- Header with "Workflows" title
- "New Workflow" button
- Table of workflows

TABLE COLUMNS:
- Name
- Trigger (badge with type)
- Status (toggle: enabled/disabled)
- Last Run (relative time or "Never")
- Actions (Execute button, Edit, Delete)

NEW WORKFLOW MODAL:
Form sections:
1. Name input
2. Trigger selector:
   - Dropdown: Manual, Schedule, Webhook, Email Received, Record Created
   - Config inputs based on trigger type
     * Schedule: cron expression input
     * Webhook: show webhook URL
     * Email Received: Gmail filter
     * Record Created: select database
3. Actions builder:
   - "Add Action" button
   - Each action:
     * Type dropdown (10 types)
     * Config inputs per type
     * Remove button
   - Drag to reorder (optional)
4. Enabled checkbox
5. Create button

EXECUTE WORKFLOW:
- Click Execute → confirmation
- POST /api/workflows/{id}/execute
- Show loading spinner
- On complete: show result modal with:
  * Success/Failed status
  * Action results
  * Execution time
  * Errors (if any)

EXECUTIONS HISTORY (expandable row):
- Click workflow row to expand
- Show last 10 executions
- Columns: Status, Time, Duration, View Details
- Details modal: full execution log

FUNCTIONALITY:
- Fetch workflows on mount
- Real-time status updates (optional: polling or websockets)
- Filter: All, Enabled, Disabled
- Search by name

STYLING:
- Dark theme
- Status badges: green (enabled), gray (disabled)
- Trigger badges: different colors per type
- Smooth animations
```

---

### **TASK 4.1: MCP Client**

**File:** `agents/mcp_client.py` (new file)

**Prompt:**
```
Create MCP (Model Context Protocol) client for integrations:

CLASS: MCPClient

SUPPORTED SERVICES:
1. gmail - Read/send emails
2. google_drive - List/upload files
3. telegram - Send messages

METHODS:

def connect(self, service: str, token: Dict) -> bool:
    """
    Connect to MCP service
    
    Args:
        service: 'gmail', 'google_drive', or 'telegram'
        token: access token dict from database
    
    Returns: True if connected successfully
    """

def gmail_send(self, to: str, subject: str, body: str) -> Dict:
    """Send email via Gmail API"""

def gmail_list(self, query: str = '', max_results: int = 10) -> List[Dict]:
    """List emails matching query"""

def drive_list(self, folder_id: str = 'root') -> List[Dict]:
    """List files in Drive folder"""

def drive_upload(self, file_path: str, folder_id: str = 'root') -> Dict:
    """Upload file to Drive"""

def telegram_send(self, chat_id: str, text: str) -> Dict:
    """Send Telegram message"""

def disconnect(self) -> bool:
    """Close connection and cleanup"""

IMPLEMENTATION:
- Use google-auth and google-api-python-client for Google services
- Use python-telegram-bot for Telegram
- Handle token refresh automatically
- Retry on rate limits (exponential backoff)
- Comprehensive error handling
- Logging

ERROR HANDLING:
- InvalidTokenError - token expired/invalid
- RateLimitError - too many requests
- ServiceUnavailableError - service down
- PermissionError - insufficient permissions

For MVP: Use direct API calls, not actual MCP protocol yet.
Add proper type hints and docstrings.
```

---

### **TASK 4.2: Integrations API**

**File:** `api/server.py`

**Prompt:**
```
Add integrations management API:

PYDANTIC MODELS:

class IntegrationInfo(BaseModel):
    type: Literal['gmail', 'google_drive', 'telegram']
    name: str
    description: str
    icon: str
    requires_oauth: bool
    status: Literal['connected', 'disconnected', 'error']
    last_sync: Optional[str] = None

class ConnectRequest(BaseModel):
    integration_type: str
    # For Telegram (bot token):
    bot_token: Optional[str] = None

ENDPOINTS:

@app.get("/api/integrations", response_model=List[IntegrationInfo])
async def list_integrations(token_data: dict = Depends(verify_jwt_token)):
    """List all available integrations with status"""
    # Return hard-coded list of 3 integrations
    # Check database for connection status
    # Gmail: connected if token exists
    # Drive: connected if token exists
    # Telegram: connected if token exists

@app.post("/api/integrations/connect")
async def connect_integration(request: ConnectRequest, token_data: dict = Depends(verify_jwt_token)):
    """
    Initiate connection to integration
    
    For Gmail/Drive: return OAuth URL
    For Telegram: save bot token directly
    """
    if request.integration_type in ['gmail', 'google_drive']:
        # Generate OAuth URL
        oauth_url = generate_oauth_url(request.integration_type)
        return {"oauth_url": oauth_url}
    elif request.integration_type == 'telegram':
        # Save bot token
        db = get_db()
        db.save_integration_token(
            user_id=token_data['user_id'],
            integration_type='telegram',
            access_token=request.bot_token,
            refresh_token='',
            expires_at=datetime.now() + timedelta(days=365)
        )
        return {"success": True}

@app.get("/api/integrations/callback")
async def oauth_callback(code: str, state: str):
    """
    OAuth callback handler
    
    1. Exchange code for tokens
    2. Save tokens to database
    3. Redirect to integrations page with success message
    """

@app.post("/api/integrations/disconnect")
async def disconnect_integration(integration_type: str, token_data: dict = Depends(verify_jwt_token)):
    """Disconnect integration"""
    db = get_db()
    db.delete_integration_token(token_data['user_id'], integration_type)
    return {"success": True}

@app.post("/api/integrations/test")
async def test_integration(integration_type: str, token_data: dict = Depends(verify_jwt_token)):
    """Test integration connection"""
    # Get token from database
    # Try to connect and make simple API call
    # Return success/error

For OAuth: Use google-auth-oauthlib.flow
Store state in session or temporary table for security.
```

---

### **TASK 4.3: Integrations UI**

**File:** `app/integrations/page.tsx`

**Prompt:**
```
Create integrations management page:

LAYOUT:
- Header with "Integrations" title
- Grid of integration cards (2 columns)

INTEGRATION CARD:
- Large icon/logo at top
- Integration name (Gmail, Google Drive, Telegram)
- Short description
- Status badge (Connected/Disconnected)
- Last sync time (if connected)
- Action button:
  * If disconnected: "Connect" (gradient button)
  * If connected: "Disconnect" (red button)
  * "Test Connection" button (if connected)

CONNECTION FLOW:

Gmail/Drive (OAuth):
1. Click "Connect"
2. Open OAuth popup
3. User authorizes
4. Callback handles token exchange
5. Close popup, refresh status

Telegram (Direct):
1. Click "Connect"
2. Show modal with bot token input
3. Instructions: "Get token from @BotFather"
4. "Save" button
5. POST /api/integrations/connect
6. Close modal, refresh status

DISCONNECT:
- Confirmation modal
- "Are you sure? This will revoke access."
- POST /api/integrations/disconnect
- Refresh status

TEST CONNECTION:
- POST /api/integrations/test
- Show toast: "✓ Connection successful" or "✗ Connection failed"

SETTINGS MODAL (per integration):
- View permissions granted
- Last sync time
- Usage stats (API calls today)
- Re-authenticate button
- Revoke access button

FUNCTIONALITY:
- Fetch integrations on mount
- Auto-refresh status every 30s
- Handle OAuth popup (window.open)
- Handle OAuth callback (window.postMessage)

STYLING:
- Dark theme
- Large integration cards with icons
- Gradient on hover
- Status indicators: green (connected), red (error), gray (disconnected)
- Smooth transitions

Add proper icons for each integration (lucide-react or custom SVGs).
```

---

### **TASK 5.1: Unified Navigation**

**File:** `app/layout.tsx`

**Prompt:**
```
Update app layout with unified navigation:

SIDEBAR:
- Fixed left sidebar (240px wide)
- Dark background (bg-gray-900)
- Navigation items:
  1. Dashboard (Home icon)
  2. Chat (MessageSquare icon)
  3. Projects (Folder icon)
  4. Workflows (Zap icon)
  5. Integrations (Plug icon)
  6. Analytics (BarChart icon)
- Active item highlighted (gradient background)
- Hover effects

TOP BAR:
- Right side:
  * User avatar/email
  * Notifications icon (bell)
  * Settings icon (gear)
  * Logout button

USER MENU (dropdown):
- User email
- Account Settings
- API Keys
- Logout

MOBILE:
- Hamburger menu button (top-left)
- Slide-in sidebar
- Overlay backdrop
- Close on item click or backdrop click

FUNCTIONALITY:
- Store user info in state/context
- Highlight active route
- Logout clears localStorage and redirects to /login
- Smooth transitions

STYLING:
- Dark theme throughout
- Icons from lucide-react
- Gradient active state: from-blue-500 to-purple-500
- Typography: font-sans, consistent sizes

Keep existing functionality, just add navigation wrapper.
```

**File:** `app/page.tsx`

**Prompt:**
```
Create dashboard overview page:

LAYOUT:
4 stat cards at top (grid):
1. Total Projects - count from GET /api/projects
2. Active Workflows - count enabled workflows
3. Connected Integrations - count connected
4. AI Requests Today - count from GET /api/stats

STATS CARDS:
- Large number (text-4xl)
- Label below (text-gray-400)
- Icon (top-right, gradient color)
- Background: bg-gray-800
- Hover effect: scale-105

RECENT ACTIVITY FEED:
- List of recent actions across all modules
- Items:
  * "Created project: Project Name" (2h ago)
  * "Executed workflow: Workflow Name" (3h ago)
  * "Connected Gmail" (Yesterday)
  * "AI Request: Query..." (5m ago)
- Icon + text + timestamp
- Limit: 20 items
- Load more button

QUICK ACTIONS:
- "New Project" button → opens modal
- "New Workflow" button → /workflows
- "Connect Integration" → /integrations
- "Start Chat" → /chat

CHARTS (optional):
- AI Requests over time (line chart)
- Model usage distribution (pie chart)
- Workflow execution stats (bar chart)

Use recharts for charts.
Fetch data from multiple endpoints on mount.
Show loading skeletons while fetching.
```

---

## 🛠️ TESTING PROMPTS

### **Integration Test Script**

**File:** `scripts/integration_test.py`

**Prompt:**
```
Create comprehensive integration test script:

TEST SCENARIOS:

1. Auth Flow:
   - Register new user
   - Login
   - Get user info with token
   - Verify token expiration handling

2. Projects Flow:
   - Create project
   - List projects
   - Create database in project
   - Add records to database
   - Query records
   - Delete record
   - Delete database
   - Delete project

3. Workflows Flow:
   - Create workflow with AI action
   - Execute workflow manually
   - Check execution status
   - List execution history
   - Update workflow (disable)
   - Delete workflow

4. Integrations Flow:
   - Connect Telegram (with test token)
   - Test connection
   - Disconnect

5. Cross-Module:
   - Create project
   - Add database with records
   - Create workflow that queries database and sends result via AI
   - Execute workflow
   - Verify results

IMPLEMENTATION:
- Use requests library
- Test against localhost:8000
- Print colored output (green=pass, red=fail)
- Summary at end
- Exit code 0 if all pass, 1 if any fail

Run with: python scripts/integration_test.py
```

---

## ✅ QUICK REFERENCE

### **How to Use These Prompts:**

```
1. Open Cursor
2. Navigate to file (or create new)
3. Cmd+Shift+P → "Claude Code"
4. Paste prompt
5. Review generated code
6. Accept changes
7. Test immediately
8. Fix any issues
9. Move to next task
```

### **Tips:**
- ✅ Test each task before moving to next
- ✅ Commit after each major task
- ✅ Keep terminal open for errors
- ✅ Use `git diff` to review changes
- ✅ Deploy at end of each day

---

**READY TO BUILD! 🚀**

Start with DAY 1, TASK 1.1 and work systematically through each prompt.
