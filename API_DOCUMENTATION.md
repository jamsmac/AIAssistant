# 🔌 API Documentation - AI Assistant Platform

**Version**: 2.0.0
**Base URL**: `https://your-domain.com/api` or `http://localhost:8000/api`
**Last Updated**: 2025-11-09

---

## 📑 Table of Contents

1. [Authentication](#authentication)
2. [Core Endpoints](#core-endpoints)
3. [AI & Chat](#ai--chat)
4. [Projects](#projects)
5. [Workflows](#workflows)
6. [Integrations](#integrations)
7. [Credits System](#credits-system)
8. [Document Analyzer](#document-analyzer)
9. [Monitoring & Analytics](#monitoring--analytics)
10. [Error Handling](#error-handling)
11. [Rate Limiting](#rate-limiting)
12. [Webhooks](#webhooks)

---

## 🔐 Authentication

### Authentication Methods

The API uses **httpOnly cookies** for authentication (not Bearer tokens in headers).

**Cookie-Based Authentication:**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```http
HTTP/1.1 200 OK
Set-Cookie: auth_token=...; HttpOnly; Secure; SameSite=Strict
Content-Type: application/json

{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com"
  }
}
```

### Making Authenticated Requests

**JavaScript/TypeScript:**
```typescript
fetch('https://your-domain.com/api/projects', {
  method: 'GET',
  credentials: 'include', // IMPORTANT: Include cookies
  headers: {
    'Content-Type': 'application/json'
  }
})
```

**Python:**
```python
import requests

session = requests.Session()
session.post('https://your-domain.com/api/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123'
})

# Subsequent requests use session cookies
response = session.get('https://your-domain.com/api/projects')
```

**cURL:**
```bash
# Login and save cookies
curl -c cookies.txt -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Use cookies in subsequent requests
curl -b cookies.txt https://your-domain.com/api/projects
```

---

## 📍 Core Endpoints

### Health Check

**GET** `/api/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-11-09T10:30:00Z"
}
```

### Get Current User

**GET** `/api/auth/me`

Get current authenticated user information.

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2025-01-01T00:00:00Z",
  "is_active": true,
  "has_2fa": false
}
```

---

## 🤖 AI & Chat

### Send AI Message

**POST** `/api/ai/chat`

Send a message to an AI model.

**Request:**
```json
{
  "message": "Explain quantum computing in simple terms",
  "model": "gpt-4",
  "conversation_id": "conv_123",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response:**
```json
{
  "response": "Quantum computing is...",
  "model": "gpt-4",
  "tokens_used": 245,
  "credits_consumed": 10,
  "conversation_id": "conv_123"
}
```

### List Available Models

**GET** `/api/models`

Get list of available AI models.

**Response:**
```json
{
  "models": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "provider": "openai",
      "cost_per_1k_tokens": 0.03,
      "max_tokens": 8192,
      "capabilities": ["chat", "code", "analysis"]
    },
    {
      "id": "claude-3",
      "name": "Claude 3 Sonnet",
      "provider": "anthropic",
      "cost_per_1k_tokens": 0.015,
      "max_tokens": 200000,
      "capabilities": ["chat", "long-context", "analysis"]
    }
  ]
}
```

### Get Chat History

**GET** `/api/history?limit=50&offset=0`

Retrieve conversation history.

**Query Parameters:**
- `limit` (integer): Number of conversations to return (default: 50)
- `offset` (integer): Pagination offset (default: 0)
- `conversation_id` (string, optional): Specific conversation

**Response:**
```json
{
  "conversations": [
    {
      "id": "conv_123",
      "created_at": "2025-11-09T10:00:00Z",
      "model": "gpt-4",
      "message_count": 12,
      "last_message": "Thank you for the explanation!"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

---

## 📁 Projects

### List Projects

**GET** `/api/projects`

Get all projects for current user.

**Response:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "My First Project",
      "description": "Learning AI automation",
      "created_at": "2025-01-15T00:00:00Z",
      "updated_at": "2025-11-09T00:00:00Z",
      "workflow_count": 5,
      "integration_count": 2
    }
  ]
}
```

### Create Project

**POST** `/api/projects`

Create a new project.

**Request:**
```json
{
  "name": "New Project",
  "description": "Project description",
  "settings": {
    "default_model": "gpt-4",
    "budget_limit": 1000
  }
}
```

**Response:**
```json
{
  "id": 2,
  "name": "New Project",
  "description": "Project description",
  "created_at": "2025-11-09T10:30:00Z",
  "settings": {
    "default_model": "gpt-4",
    "budget_limit": 1000
  }
}
```

### Get Project

**GET** `/api/projects/{project_id}`

Get specific project details.

**Response:**
```json
{
  "id": 1,
  "name": "My Project",
  "description": "Description",
  "created_at": "2025-01-15T00:00:00Z",
  "workflows": [...],
  "integrations": [...],
  "stats": {
    "total_workflows": 5,
    "total_executions": 1250,
    "credits_used": 5000
  }
}
```

### Update Project

**PUT** `/api/projects/{project_id}`

Update project details.

**Request:**
```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### Delete Project

**DELETE** `/api/projects/{project_id}`

Delete a project (soft delete).

**Response:**
```json
{
  "message": "Project deleted successfully",
  "id": 1
}
```

---

## 🔄 Workflows

### List Workflows

**GET** `/api/workflows?project_id=1`

Get workflows, optionally filtered by project.

**Response:**
```json
{
  "workflows": [
    {
      "id": 1,
      "name": "Daily Report Generator",
      "description": "Generates daily reports",
      "enabled": true,
      "trigger_type": "schedule",
      "trigger_config": {"cron": "0 9 * * *"},
      "created_at": "2025-01-20T00:00:00Z",
      "last_execution": "2025-11-09T09:00:00Z",
      "execution_count": 290
    }
  ]
}
```

### Create Workflow

**POST** `/api/workflows`

Create a new workflow.

**Request:**
```json
{
  "name": "Email Summarizer",
  "description": "Summarizes incoming emails",
  "enabled": true,
  "definition": {
    "trigger": {
      "type": "webhook",
      "config": {"path": "/webhooks/email"}
    },
    "nodes": [
      {
        "id": "node_1",
        "type": "ai_call",
        "config": {"model": "gpt-4", "prompt": "Summarize: {{email.body}}"}
      },
      {
        "id": "node_2",
        "type": "send_email",
        "config": {"to": "{{email.from}}", "subject": "Summary"}
      }
    ],
    "edges": [
      {"from": "trigger", "to": "node_1"},
      {"from": "node_1", "to": "node_2"}
    ]
  }
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Email Summarizer",
  "webhook_url": "https://your-domain.com/webhooks/wf_abc123",
  "created_at": "2025-11-09T10:30:00Z"
}
```

### Execute Workflow

**POST** `/api/workflows/{workflow_id}/execute`

Manually trigger a workflow.

**Request:**
```json
{
  "input": {
    "test_mode": true,
    "data": {"custom": "input"}
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_123",
  "status": "running",
  "started_at": "2025-11-09T10:30:00Z"
}
```

### Get Workflow Execution

**GET** `/api/workflows/{workflow_id}/executions/{execution_id}`

Get execution details.

**Response:**
```json
{
  "id": "exec_123",
  "workflow_id": 1,
  "status": "completed",
  "started_at": "2025-11-09T10:30:00Z",
  "completed_at": "2025-11-09T10:30:15Z",
  "duration_ms": 15000,
  "result": {
    "output": "Summary generated successfully",
    "credits_used": 5
  },
  "logs": [
    {"timestamp": "2025-11-09T10:30:01Z", "level": "info", "message": "Starting node_1"}
  ]
}
```

---

## 🔌 Integrations

### List Integrations

**GET** `/api/integrations`

Get all connected integrations.

**Response:**
```json
{
  "integrations": [
    {
      "id": 1,
      "type": "telegram",
      "name": "My Bot",
      "status": "connected",
      "connected_at": "2025-01-10T00:00:00Z",
      "last_used": "2025-11-09T09:00:00Z"
    }
  ]
}
```

### Connect Integration

**POST** `/api/integrations/connect`

Connect a new integration.

**Request (Telegram):**
```json
{
  "integration_type": "telegram",
  "bot_token": "123456:ABC-DEF...",
  "chat_id": "123456789"
}
```

**Request (OAuth):**
```json
{
  "integration_type": "google",
  "oauth_code": "4/0AX4XfWh..."
}
```

**Response:**
```json
{
  "id": 2,
  "type": "telegram",
  "status": "connected",
  "webhook_url": "https://your-domain.com/webhooks/telegram/abc123"
}
```

### Test Integration

**POST** `/api/integrations/test?integration_type=telegram`

Test integration connection.

**Response:**
```json
{
  "status": "success",
  "message": "Connection test successful",
  "details": {
    "bot_username": "@my_bot",
    "can_send_messages": true
  }
}
```

### Disconnect Integration

**POST** `/api/integrations/disconnect?integration_type=telegram`

Disconnect an integration.

**Response:**
```json
{
  "message": "Integration disconnected successfully"
}
```

---

## 💳 Credits System

### Get Credit Balance

**GET** `/api/credits/balance`

Get current credit balance.

**Response:**
```json
{
  "balance": 1250,
  "currency": "USD",
  "last_purchase": "2025-11-01T00:00:00Z",
  "auto_recharge_enabled": true,
  "auto_recharge_threshold": 100
}
```

### Purchase Credits

**POST** `/api/credits/purchase`

Purchase credits via payment provider.

**Request:**
```json
{
  "package": "pro",
  "payment_method": "stripe",
  "return_url": "https://your-app.com/credits/success"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_test_123"
}
```

### Get Credit History

**GET** `/api/credits/history?limit=50&offset=0`

Get credit transaction history.

**Response:**
```json
{
  "transactions": [
    {
      "id": 1,
      "type": "purchase",
      "amount": 1000,
      "cost_usd": 50,
      "timestamp": "2025-11-01T00:00:00Z",
      "description": "Pro package purchase"
    },
    {
      "id": 2,
      "type": "usage",
      "amount": -10,
      "timestamp": "2025-11-09T10:00:00Z",
      "description": "GPT-4 chat message"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Gift Credits

**POST** `/api/credits/gift`

Gift credits to another user.

**Request:**
```json
{
  "recipient_email": "friend@example.com",
  "amount": 100,
  "message": "Happy birthday!"
}
```

**Response:**
```json
{
  "gift_id": "gift_123",
  "status": "sent",
  "recipient": "friend@example.com",
  "amount": 100
}
```

---

## 📄 Document Analyzer

### Create Analysis

**POST** `/api/doc-analyzer/analyze`

Analyze API documentation.

**Request (URL):**
```json
{
  "source_type": "url",
  "source_url": "https://api.example.com/openapi.json",
  "format": "openapi3"
}
```

**Request (File Upload):**
```http
POST /api/doc-analyzer/analyze
Content-Type: multipart/form-data

file: [binary data]
format: openapi3
```

**Response:**
```json
{
  "analysis_id": "analysis_123",
  "status": "processing",
  "estimated_time_seconds": 30
}
```

### Get Analysis Result

**GET** `/api/doc-analyzer/analyses/{analysis_id}`

Get analysis results.

**Response:**
```json
{
  "id": "analysis_123",
  "status": "completed",
  "created_at": "2025-11-09T10:00:00Z",
  "completed_at": "2025-11-09T10:00:25Z",
  "results": {
    "endpoints": [
      {
        "path": "/users",
        "method": "GET",
        "summary": "List users",
        "parameters": [...],
        "responses": {...}
      }
    ],
    "authentication": ["bearer", "api_key"],
    "security_issues": [],
    "statistics": {
      "total_endpoints": 45,
      "total_schemas": 23
    }
  }
}
```

### Export to Google Sheets

**POST** `/api/doc-analyzer/export/sheets`

Export analysis to Google Sheets.

**Request:**
```json
{
  "analysis_id": "analysis_123",
  "spreadsheet_name": "API Documentation Analysis",
  "include_examples": true
}
```

**Response:**
```json
{
  "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
  "sheets_created": ["Endpoints", "Schemas", "Security"]
}
```

---

## 📊 Monitoring & Analytics

### Get System Stats

**GET** `/api/monitoring/stats`

Get system-wide statistics.

**Response:**
```json
{
  "total_users": 1250,
  "active_users_24h": 342,
  "total_workflows": 5600,
  "workflows_executed_24h": 12450,
  "total_ai_calls_24h": 45780,
  "credits_consumed_24h": 125000,
  "uptime_percentage": 99.98
}
```

### Get User Analytics

**GET** `/api/dashboard/stats`

Get current user's analytics.

**Response:**
```json
{
  "projects_count": 5,
  "workflows_count": 12,
  "total_executions": 1250,
  "executions_today": 45,
  "credits_used_total": 5000,
  "credits_used_today": 120,
  "favorite_model": "gpt-4",
  "most_active_workflow": {
    "id": 1,
    "name": "Daily Report"
  }
}
```

### Get Model Rankings

**GET** `/api/rankings`

Get AI model performance rankings.

**Response:**
```json
{
  "rankings": [
    {
      "model": "gpt-4",
      "score": 9.5,
      "total_uses": 125000,
      "avg_response_time_ms": 2500,
      "user_satisfaction": 4.8
    }
  ],
  "updated_at": "2025-11-09T10:00:00Z"
}
```

---

## ⚠️ Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "not-an-email"
    }
  },
  "request_id": "req_abc123"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily down |

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `INVALID_CREDENTIALS` | Login failed | Check email/password |
| `INSUFFICIENT_CREDITS` | Not enough credits | Purchase more credits |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry |
| `INVALID_INPUT` | Validation failed | Check request format |
| `RESOURCE_NOT_FOUND` | Resource doesn't exist | Verify ID |
| `WORKFLOW_EXECUTION_FAILED` | Workflow error | Check workflow logs |

---

## 🚦 Rate Limiting

### Rate Limit Headers

Every response includes rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699548000
```

### Rate Limits by Plan

| Plan | Requests/Hour | Requests/Minute |
|------|--------------|----------------|
| Free | 60 | 10 |
| Pro | 600 | 60 |
| Business | 6000 | 600 |
| Enterprise | Custom | Custom |

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "retry_after": 45
  }
}
```

---

## 🪝 Webhooks

### Webhook URLs

Each workflow can have a unique webhook URL:

```
https://your-domain.com/webhooks/{workflow_id}/{secret}
```

### Webhook Security

Webhooks include signature verification:

**Header:**
```
X-Webhook-Signature: sha256=abc123...
```

**Verification (Python):**
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, f"sha256={expected}")
```

### Webhook Payload Format

```json
{
  "event": "workflow.executed",
  "timestamp": "2025-11-09T10:30:00Z",
  "workflow_id": 1,
  "execution_id": "exec_123",
  "status": "completed",
  "data": {
    "result": {...}
  }
}
```

---

## 🔧 SDKs & Code Examples

### JavaScript/TypeScript

```typescript
import { APIClient } from '@your-platform/sdk';

const client = new APIClient({
  baseURL: 'https://your-domain.com/api',
  credentials: 'include' // Important for cookies
});

// Login
await client.auth.login({
  email: 'user@example.com',
  password: 'password123'
});

// Send AI message
const response = await client.ai.chat({
  message: 'Hello AI!',
  model: 'gpt-4'
});

console.log(response.response);
```

### Python

```python
from your_platform import Client

client = Client(base_url='https://your-domain.com/api')

# Login
client.auth.login(
    email='user@example.com',
    password='password123'
)

# Send AI message
response = client.ai.chat(
    message='Hello AI!',
    model='gpt-4'
)

print(response.response)
```

---

## 📝 Changelog

### v2.0.0 (2025-11-09)
- **BREAKING**: Changed to httpOnly cookie authentication
- Added 12 new router endpoints
- Enhanced security (strict SameSite)
- Improved error messages
- Added Google Sheets export

### v1.5.0
- Added document analyzer
- Workflow visual builder
- Integration improvements

### v1.0.0
- Initial API release

---

## 🆘 Support

**API Issues**: api-support@your-platform.com
**Documentation**: docs@your-platform.com
**Status Page**: https://status.your-platform.com

---

**API Version**: 2.0.0
**Documentation Version**: 2.0.0
**Last Updated**: 2025-11-09

For interactive API exploration, visit: https://your-domain.com/api/docs

---

END OF API DOCUMENTATION
