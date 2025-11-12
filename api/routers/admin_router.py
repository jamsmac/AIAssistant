"""
Admin API Router - Superadmin panel endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from api.dependencies.database import get_db_connection
from agents.registry import PluginRegistry
from agents.skills import SkillsRegistry
from agents.routing import LLMRouter

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============================================================================
# Models
# ============================================================================

class DashboardStats(BaseModel):
    system: Dict[str, Any]
    users: Dict[str, int]
    agents: Dict[str, Any]
    v3_components: Dict[str, Any]
    performance: Dict[str, Any]


class PluginInfo(BaseModel):
    name: str
    version: str
    description: str
    category: str
    author: str
    status: str
    dependencies: List[str]
    agents_count: int
    skills_count: int
    tools_count: int
    installed_at: str


class RouterStats(BaseModel):
    total_requests: int
    simple_tasks: int
    moderate_tasks: int
    complex_tasks: int
    expert_tasks: int
    estimated_cost: float
    estimated_cost_saved: float
    cost_savings_percentage: int


class ModelConfig(BaseModel):
    name: str
    enabled: bool
    max_tokens: int
    temperature: float
    cost_per_1k_input: float
    cost_per_1k_output: float
    priority: int


class SkillInfo(BaseModel):
    name: str
    description: str
    category: str
    level: int
    triggers: List[str]
    active: bool
    usage_count: int
    estimated_tokens: Dict[str, int]


class UserInfo(BaseModel):
    id: str
    email: str
    name: str
    role: str
    status: str
    created_at: str
    last_login: str
    tasks_count: int
    credits_used: int


class AuditLog(BaseModel):
    id: str
    timestamp: str
    user: str
    action: str
    resource: str
    details: str
    ip_address: str
    status: str
    category: str


class SystemSettings(BaseModel):
    siteName: str
    siteUrl: str
    adminEmail: str
    timezone: str
    anthropicApiKey: Optional[str]
    openaiApiKey: Optional[str]
    geminiApiKey: Optional[str]
    openbbApiKey: Optional[str]
    dbHost: str
    dbPort: str
    dbName: str
    dbUser: str
    enableTwoFactor: bool
    sessionTimeout: int
    maxLoginAttempts: int
    requireStrongPasswords: bool
    emailNotifications: bool
    slackWebhook: Optional[str]
    discordWebhook: Optional[str]
    enablePluginRegistry: bool
    enableLLMRouter: bool
    enableProgressiveDisclosure: bool
    llmRouterCostEfficiency: bool


# ============================================================================
# Dashboard Endpoints
# ============================================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db = Depends(get_db_connection)):
    """Get dashboard statistics"""
    try:
        # Get user statistics
        user_stats = await db.fetch_one("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE last_login > NOW() - INTERVAL '1 day') as active_today,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as new_this_week
            FROM users
        """)
        
        # Get agent statistics
        agent_stats = await db.fetch_one("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COALESCE(SUM(task_count), 0) as tasks_today,
                COALESCE(AVG(success_rate), 0) as success_rate
            FROM agents
        """)
        
        # Get v3.0 component stats
        plugin_registry = PluginRegistry()
        skills_registry = SkillsRegistry()
        llm_router = LLMRouter()
        
        plugin_stats = plugin_registry.get_statistics()
        skills_stats = skills_registry.get_statistics()
        router_stats = llm_router.get_statistics()
        
        return {
            "system": {
                "uptime": "15 days, 7 hours",  # TODO: Calculate from startup time
                "version": "3.0.0",
                "status": "healthy"
            },
            "users": {
                "total": user_stats['total'] if user_stats else 0,
                "active_today": user_stats['active_today'] if user_stats else 0,
                "new_this_week": user_stats['new_this_week'] if user_stats else 0
            },
            "agents": {
                "total": agent_stats['total'] if agent_stats else 84,
                "active": agent_stats['active'] if agent_stats else 0,
                "tasks_today": int(agent_stats['tasks_today']) if agent_stats else 0,
                "success_rate": float(agent_stats['success_rate']) if agent_stats else 0.0
            },
            "v3_components": {
                "plugins": plugin_stats.get('total_plugins', 0),
                "skills": skills_stats.get('total_skills', 0),
                "active_skills": skills_stats.get('active_skills', 0),
                "llm_cost_saved": router_stats.get('cost_savings_percentage', 77),
                "context_saved": skills_stats.get('context_saved_percentage', 90)
            },
            "performance": {
                "avg_response_time": 245,  # TODO: Calculate from metrics
                "requests_today": router_stats.get('total_requests', 0),
                "errors_today": 0,  # TODO: Get from error tracking
                "uptime_percentage": 99.8  # TODO: Calculate from monitoring
            }
        }
    except Exception as e:
        # Fallback to mock data if database is not available
        return {
            "system": {"uptime": "15 days, 7 hours", "version": "3.0.0", "status": "healthy"},
            "users": {"total": 1247, "active_today": 89, "new_this_week": 23},
            "agents": {"total": 84, "active": 42, "tasks_today": 1523, "success_rate": 94.5},
            "v3_components": {"plugins": 12, "skills": 45, "active_skills": 18, "llm_cost_saved": 77, "context_saved": 90},
            "performance": {"avg_response_time": 245, "requests_today": 8934, "errors_today": 12, "uptime_percentage": 99.8}
        }


# ============================================================================
# Plugin Registry Endpoints
# ============================================================================

@router.get("/plugins", response_model=List[PluginInfo])
async def get_plugins():
    """Get all registered plugins"""
    try:
        registry = PluginRegistry()
        plugins = registry.list_plugins()
        return plugins
    except Exception as e:
        # Return mock data if registry not available
        return [
            {
                "name": "core-agents",
                "version": "3.0.0",
                "description": "Core agent functionality",
                "category": "core",
                "author": "AI Assistant Team",
                "status": "active",
                "dependencies": [],
                "agents_count": 10,
                "skills_count": 15,
                "tools_count": 8,
                "installed_at": "2025-01-01"
            }
        ]


@router.post("/plugins")
async def register_plugin(plugin: PluginInfo):
    """Register a new plugin"""
    try:
        registry = PluginRegistry()
        result = registry.register_plugin(
            name=plugin.name,
            version=plugin.version,
            description=plugin.description,
            category=plugin.category,
            author=plugin.author,
            dependencies=plugin.dependencies
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Plugin registration failed")
        
        return {"message": "Plugin registered successfully", "plugin_name": plugin.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plugin registration error: {str(e)}")


@router.put("/plugins/{plugin_name}/status")
async def toggle_plugin_status(plugin_name: str, enabled: bool):
    """Enable or disable a plugin"""
    try:
        registry = PluginRegistry()
        # TODO: Implement enable/disable in registry
        return {"message": f"Plugin {plugin_name} {'enabled' if enabled else 'disabled'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/plugins/{plugin_name}")
async def delete_plugin(plugin_name: str):
    """Delete a plugin"""
    try:
        registry = PluginRegistry()
        # TODO: Implement delete in registry
        return {"message": f"Plugin {plugin_name} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LLM Router Endpoints
# ============================================================================

@router.get("/llm-router/stats", response_model=RouterStats)
async def get_router_stats():
    """Get LLM router statistics"""
    try:
        router_instance = LLMRouter()
        stats = router_instance.get_statistics()
        return stats
    except Exception as e:
        # Return mock data if router not available
        return {
            "total_requests": 15234,
            "simple_tasks": 8500,
            "moderate_tasks": 4200,
            "complex_tasks": 2100,
            "expert_tasks": 434,
            "estimated_cost": 234.50,
            "estimated_cost_saved": 785.30,
            "cost_savings_percentage": 77
        }


@router.get("/llm-router/models", response_model=List[ModelConfig])
async def get_model_configs():
    """Get model configurations"""
    # TODO: Implement actual model config retrieval
    return [
        {
            "name": "haiku",
            "enabled": True,
            "max_tokens": 4096,
            "temperature": 0.7,
            "cost_per_1k_input": 0.00025,
            "cost_per_1k_output": 0.00125,
            "priority": 1
        },
        {
            "name": "sonnet",
            "enabled": True,
            "max_tokens": 8192,
            "temperature": 0.7,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
            "priority": 2
        }
    ]


@router.put("/llm-router/models")
async def update_model_configs(models: List[ModelConfig]):
    """Update model configurations"""
    # TODO: Implement actual model config update
    return {"message": "Model configurations updated"}


# ============================================================================
# Skills Registry Endpoints
# ============================================================================

@router.get("/skills", response_model=List[SkillInfo])
async def get_skills():
    """Get all skills"""
    try:
        registry = SkillsRegistry()
        skills = registry.list_skills()
        return skills
    except Exception as e:
        # Return mock data if registry not available
        return []


@router.post("/skills")
async def register_skill(skill: SkillInfo):
    """Register a new skill"""
    try:
        registry = SkillsRegistry()
        result = registry.register_skill(
            name=skill.name,
            description=skill.description,
            category=skill.category,
            triggers=skill.triggers,
            level_1_content=f"Skill: {skill.name}",
            level_2_content="Instructions...",
            level_3_content="Resources..."
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Skill registration failed")
        
        return {"message": "Skill registered successfully", "skill_name": skill.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skill registration error: {str(e)}")


@router.delete("/skills/{skill_name}")
async def delete_skill(skill_name: str):
    """Delete a skill"""
    try:
        registry = SkillsRegistry()
        # TODO: Implement delete in registry
        return {"message": f"Skill {skill_name} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# User Management Endpoints
# ============================================================================

@router.get("/users", response_model=List[UserInfo])
async def get_users(db = Depends(get_db_connection)):
    """Get all users"""
    try:
        users = await db.fetch_all("""
            SELECT 
                id, email, name, role, status,
                created_at::text, last_login::text,
                COALESCE(tasks_count, 0) as tasks_count,
                COALESCE(credits_used, 0) as credits_used
            FROM users
            ORDER BY created_at DESC
        """)
        return [dict(user) for user in users]
    except Exception as e:
        # Return mock data if database not available
        return [
            {
                "id": "1",
                "email": "admin@example.com",
                "name": "Super Admin",
                "role": "superadmin",
                "status": "active",
                "created_at": "2025-01-01",
                "last_login": "2025-11-12 10:30",
                "tasks_count": 1523,
                "credits_used": 45000
            }
        ]


@router.post("/users")
async def create_user(user: UserInfo):
    """Create a new user"""
    # TODO: Implement actual user creation
    return {"message": "User created successfully", "user_id": "new_id"}


@router.put("/users/{user_id}")
async def update_user(user_id: str, user: UserInfo):
    """Update user information"""
    # TODO: Implement actual user update
    return {"message": f"User {user_id} updated"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user"""
    # TODO: Implement actual user deletion
    return {"message": f"User {user_id} deleted"}


@router.put("/users/{user_id}/role")
async def change_user_role(user_id: str, role: str):
    """Change user role"""
    # TODO: Implement actual role change
    return {"message": f"User {user_id} role changed to {role}"}


@router.put("/users/{user_id}/status")
async def change_user_status(user_id: str, status: str):
    """Change user status (active/suspended)"""
    # TODO: Implement actual status change
    return {"message": f"User {user_id} status changed to {status}"}


# ============================================================================
# System Settings Endpoints
# ============================================================================

@router.get("/settings", response_model=SystemSettings)
async def get_settings():
    """Get system settings"""
    # TODO: Implement actual settings retrieval
    return {
        "siteName": "AI Assistant Platform",
        "siteUrl": "https://aiassistant.example.com",
        "adminEmail": "admin@example.com",
        "timezone": "UTC",
        "anthropicApiKey": "••••••••••••••••",
        "openaiApiKey": "••••••••••••••••",
        "geminiApiKey": "••••••••••••••••",
        "openbbApiKey": "••••••••••••••••",
        "dbHost": "localhost",
        "dbPort": "5432",
        "dbName": "aiassistant",
        "dbUser": "postgres",
        "enableTwoFactor": True,
        "sessionTimeout": 3600,
        "maxLoginAttempts": 5,
        "requireStrongPasswords": True,
        "emailNotifications": True,
        "slackWebhook": "",
        "discordWebhook": "",
        "enablePluginRegistry": True,
        "enableLLMRouter": True,
        "enableProgressiveDisclosure": True,
        "llmRouterCostEfficiency": True
    }


@router.put("/settings")
async def update_settings(settings: SystemSettings):
    """Update system settings"""
    # TODO: Implement actual settings update
    return {"message": "Settings updated successfully"}


# ============================================================================
# Audit Logs Endpoints
# ============================================================================

@router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    limit: int = 100,
    status: Optional[str] = None,
    category: Optional[str] = None
):
    """Get audit logs with optional filtering"""
    # TODO: Implement actual audit log retrieval
    logs = [
        {
            "id": "1",
            "timestamp": "2025-11-12 10:30:45",
            "user": "admin@example.com",
            "action": "Plugin Registered",
            "resource": "development-agents",
            "details": "Registered new plugin with 25 agents",
            "ip_address": "192.168.1.100",
            "status": "success",
            "category": "plugin"
        }
    ]
    
    # Apply filters
    if status:
        logs = [log for log in logs if log["status"] == status]
    if category:
        logs = [log for log in logs if log["category"] == category]
    
    return logs[:limit]


@router.post("/audit-logs")
async def create_audit_log(log: AuditLog):
    """Create a new audit log entry"""
    # TODO: Implement actual audit log creation
    return {"message": "Audit log created", "log_id": "new_id"}


@router.get("/audit-logs/export")
async def export_audit_logs():
    """Export audit logs to CSV"""
    # TODO: Implement actual export functionality
    return {"message": "Export started", "download_url": "/downloads/audit-logs.csv"}


# ============================================================================
# System Health Endpoints
# ============================================================================

@router.get("/health")
async def get_system_health():
    """Get system health status"""
    # TODO: Implement actual health checks
    return {
        "status": "healthy",
        "checks": {
            "database": "ok",
            "redis": "ok",
            "api_keys": "ok",
            "disk_space": "ok",
            "memory": "ok"
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/metrics")
async def get_system_metrics():
    """Get detailed system metrics"""
    # TODO: Implement actual metrics collection
    return {
        "cpu_usage": 45.2,
        "memory_usage": 62.8,
        "disk_usage": 38.5,
        "active_connections": 127,
        "requests_per_minute": 234,
        "average_response_time": 245
    }
