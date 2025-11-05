"""
Integrations Router - Handles external service integrations
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.database import HistoryDatabase, get_db
from agents.auth import get_current_user
from agents.oauth_providers import OAuthProviderFactory
from agents.mcp_client import MCPClient

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

# Initialize services
db = get_db()
oauth_factory = OAuthProviderFactory()
mcp_client = MCPClient()

# Pydantic models
class IntegrationInfo(BaseModel):
    service: str
    name: str
    description: str
    icon: str
    connected: bool
    connected_at: Optional[str] = None
    account_info: Optional[Dict[str, Any]] = None

class ConnectRequest(BaseModel):
    service: str
    redirect_uri: Optional[str] = None

class DisconnectRequest(BaseModel):
    service: str

class TestRequest(BaseModel):
    service: str
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

# Get available integrations
@router.get("/", response_model=List[IntegrationInfo])
async def get_integrations(current_user: dict = Depends(get_current_user)):
    """Get all available integrations and their status"""

    # Define available integrations
    available_integrations = [
        {
            "service": "gmail",
            "name": "Gmail",
            "description": "Send and receive emails, manage labels",
            "icon": "gmail"
        },
        {
            "service": "google_drive",
            "name": "Google Drive",
            "description": "Access and manage files in Google Drive",
            "icon": "google-drive"
        },
        {
            "service": "slack",
            "name": "Slack",
            "description": "Send messages and notifications to Slack",
            "icon": "slack"
        },
        {
            "service": "telegram",
            "name": "Telegram",
            "description": "Send messages via Telegram bot",
            "icon": "telegram"
        },
        {
            "service": "github",
            "name": "GitHub",
            "description": "Access repositories, issues, and pull requests",
            "icon": "github"
        },
        {
            "service": "notion",
            "name": "Notion",
            "description": "Create and manage Notion pages",
            "icon": "notion"
        }
    ]

    # Get user's connected integrations
    user_tokens = db.get_user_integration_tokens(current_user['id'])
    connected_services = {token['service']: token for token in user_tokens}

    result = []
    for integration in available_integrations:
        service = integration['service']
        is_connected = service in connected_services

        result.append(IntegrationInfo(
            service=service,
            name=integration['name'],
            description=integration['description'],
            icon=integration['icon'],
            connected=is_connected,
            connected_at=connected_services[service]['created_at'] if is_connected else None,
            account_info=json.loads(connected_services[service]['account_info']) if is_connected and connected_services[service].get('account_info') else None
        ))

    return result

@router.get("/connected", response_model=List[IntegrationInfo])
async def get_connected_integrations(current_user: dict = Depends(get_current_user)):
    """Get only connected integrations"""
    all_integrations = await get_integrations(current_user)
    return [i for i in all_integrations if i.connected]

# OAuth flow endpoints
@router.post("/connect")
async def connect_integration(
    request: ConnectRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start OAuth flow for a service"""
    try:
        # Special handling for Telegram (no OAuth, just bot token)
        if request.service == "telegram":
            # For Telegram, we expect the bot token to be in environment
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                raise HTTPException(
                    status_code=400,
                    detail="Telegram bot token not configured"
                )

            # Save token
            db.save_integration_token(
                user_id=current_user['id'],
                service="telegram",
                access_token=bot_token,
                account_info=json.dumps({"type": "bot"})
            )

            return {"message": "Telegram connected successfully"}

        # OAuth flow for other services
        provider = oauth_factory.get_provider(request.service)
        if not provider:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown service: {request.service}"
            )

        # Generate OAuth URL
        auth_url = provider.get_auth_url(
            redirect_uri=request.redirect_uri or f"{os.getenv('API_URL')}/api/integrations/callback",
            state=f"{current_user['id']}:{request.service}"
        )

        return {"auth_url": auth_url}

    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail=f"OAuth provider for {request.service} not yet implemented"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    error: Optional[str] = None
):
    """OAuth callback endpoint"""
    if error:
        return RedirectResponse(url=f"/integrations?error={error}")

    try:
        # Parse state
        user_id, service = state.split(":")
        user_id = int(user_id)

        # Get OAuth provider
        provider = oauth_factory.get_provider(service)
        if not provider:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown service: {service}"
            )

        # Exchange code for tokens
        tokens = await provider.exchange_code(
            code=code,
            redirect_uri=f"{os.getenv('API_URL')}/api/integrations/callback"
        )

        # Get account info
        account_info = await provider.get_account_info(tokens['access_token'])

        # Save tokens
        db.save_integration_token(
            user_id=user_id,
            service=service,
            access_token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token'),
            expires_at=tokens.get('expires_at'),
            account_info=json.dumps(account_info)
        )

        # Redirect to frontend
        return RedirectResponse(url="/integrations?connected=true")

    except Exception as e:
        return RedirectResponse(url=f"/integrations?error={str(e)}")

@router.post("/disconnect")
async def disconnect_integration(
    request: DisconnectRequest,
    current_user: dict = Depends(get_current_user)
):
    """Disconnect an integration"""
    db.delete_integration_token(
        user_id=current_user['id'],
        service=request.service
    )

    return {"message": f"{request.service} disconnected successfully"}

@router.post("/test")
async def test_integration(
    request: TestRequest,
    current_user: dict = Depends(get_current_user)
):
    """Test an integration connection"""
    # Get user's token for the service
    token = db.get_integration_token(
        user_id=current_user['id'],
        service=request.service
    )

    if not token:
        raise HTTPException(
            status_code=400,
            detail=f"Not connected to {request.service}"
        )

    try:
        # Test based on service
        if request.service == "gmail":
            # Test by getting user profile
            provider = oauth_factory.get_provider("gmail")
            profile = await provider.get_account_info(token['access_token'])
            return {"success": True, "profile": profile}

        elif request.service == "telegram":
            # Test by getting bot info
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.telegram.org/bot{token['access_token']}/getMe"
                )
                data = response.json()
                if data['ok']:
                    return {"success": True, "bot": data['result']}
                else:
                    raise Exception(data.get('description', 'Unknown error'))

        elif request.service == "slack":
            # Test Slack connection
            return {"success": True, "message": "Slack integration test not implemented"}

        else:
            return {"success": False, "message": f"Test not implemented for {request.service}"}

    except Exception as e:
        return {"success": False, "error": str(e)}

# MCP endpoints
@router.get("/mcp/servers")
async def get_mcp_servers(current_user: dict = Depends(get_current_user)):
    """Get available MCP servers"""
    servers = await mcp_client.list_servers()
    return {"servers": servers}

@router.post("/mcp/connect")
async def connect_mcp_server(
    server_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Connect to an MCP server"""
    try:
        result = await mcp_client.connect(server_name)
        return {"success": True, "server": server_name, "capabilities": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/execute")
async def execute_mcp_command(
    server_name: str,
    command: str,
    params: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Execute a command on an MCP server"""
    try:
        result = await mcp_client.execute(server_name, command, params)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Webhook endpoints for external services
@router.post("/webhooks/{service}")
async def receive_webhook(
    service: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Receive webhooks from external services"""
    try:
        # Get webhook data
        data = await request.json()

        # Verify webhook signature if needed
        # TODO: Implement signature verification for each service

        # Process webhook in background
        background_tasks.add_task(
            process_webhook,
            service,
            data
        )

        return {"received": True}

    except Exception as e:
        # Log error but return success to avoid retries
        print(f"Webhook error for {service}: {e}")
        return {"received": True}

async def process_webhook(service: str, data: Dict[str, Any]):
    """Process webhook data in background"""
    try:
        # Find workflows triggered by this webhook
        workflows = db.get_workflows_by_trigger_type("webhook")

        for workflow in workflows:
            trigger_config = json.loads(workflow['trigger_json'])

            # Check if this webhook matches the workflow trigger
            if trigger_config.get('config', {}).get('service') == service:
                # Execute workflow with webhook data
                from agents.workflow_engine import WorkflowEngine
                engine = WorkflowEngine(db)

                execution_id = db.create_workflow_execution(
                    workflow_id=workflow['id'],
                    status="pending",
                    input_data=json.dumps(data)
                )

                await engine.execute_workflow(
                    workflow['id'],
                    execution_id,
                    data
                )

    except Exception as e:
        print(f"Error processing webhook for {service}: {e}")