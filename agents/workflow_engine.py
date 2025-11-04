"""
Workflow Execution Engine

Supports triggers: manual, schedule, webhook, email_received, record_created
Supports actions: send_email, create_record, call_webhook, run_ai_agent, send_notification,
                  update_record, delete_record, send_telegram, create_project, execute_workflow
"""

import sqlite3
import json
import logging
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "history.db"


class WorkflowEngine:
    """Workflow execution engine with trigger and action support"""

    def __init__(self, db_path: str = str(DB_PATH)):
        """
        Initialize workflow engine

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        # MCP client will be initialized when needed
        self.mcp_client = None

        self.logger.info("WorkflowEngine initialized")

    def execute(self, workflow_id: int, context: Optional[Dict] = None) -> Dict:
        """
        Execute workflow by ID

        Args:
            workflow_id: Workflow ID to execute
            context: Optional context data (e.g., webhook payload, record data)

        Returns:
            Dict with execution results:
            {
                "success": bool,
                "workflow_id": int,
                "execution_id": int,
                "results": List[Dict],
                "error": Optional[str]
            }
        """
        execution_id = None

        try:
            # Load workflow from database
            workflow = self._load_workflow(workflow_id)

            if not workflow:
                return {
                    "success": False,
                    "workflow_id": workflow_id,
                    "error": "Workflow not found"
                }

            # Check if enabled
            if not workflow.get('enabled'):
                return {
                    "success": False,
                    "workflow_id": workflow_id,
                    "error": "Workflow is disabled"
                }

            self.logger.info(f"Executing workflow {workflow_id}: {workflow['name']}")

            # Parse actions
            actions = json.loads(workflow['actions_json'])

            # Initialize context if not provided
            if context is None:
                context = {}

            # Add workflow info to context
            context['workflow'] = {
                'id': workflow_id,
                'name': workflow['name'],
                'trigger_type': workflow['trigger_type']
            }

            # Execute each action sequentially
            results = []
            for idx, action in enumerate(actions):
                self.logger.info(f"Executing action {idx + 1}/{len(actions)}: {action.get('type')}")

                try:
                    result = self.execute_action(action, context)
                    results.append(result)

                    # Add action result to context for next actions
                    context[f'action_{idx}_result'] = result.get('result')

                except Exception as e:
                    self.logger.error(f"Action {idx + 1} failed: {e}")
                    results.append({
                        "success": False,
                        "action_type": action.get('type'),
                        "error": str(e)
                    })
                    # Continue with next action (don't stop workflow)

            # Log execution
            execution_id = self._log_execution(
                workflow_id=workflow_id,
                status='completed',
                result_json=json.dumps(results),
                error=None
            )

            return {
                "success": True,
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "results": results
            }

        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} execution failed: {e}")

            # Log failed execution
            if execution_id is None:
                execution_id = self._log_execution(
                    workflow_id=workflow_id,
                    status='failed',
                    result_json=None,
                    error=str(e)
                )

            return {
                "success": False,
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "error": str(e)
            }

    def execute_action(self, action: Dict, context: Dict) -> Dict:
        """
        Execute single action

        Args:
            action: Action configuration
                {
                    "type": "send_email",
                    "config": {"to": "...", "subject": "...", "body": "..."}
                }
            context: Execution context with variables

        Returns:
            Dict with result: {"success": bool, "result": Any, "error": Optional[str]}
        """
        action_type = action.get('type')
        config = action.get('config', {})

        # Parse variables in config
        parsed_config = self._parse_config_variables(config, context)

        try:
            # Route to appropriate action handler
            if action_type == 'send_email':
                return self._action_send_email(parsed_config)

            elif action_type == 'create_record':
                return self._action_create_record(parsed_config)

            elif action_type == 'call_webhook':
                return self._action_call_webhook(parsed_config)

            elif action_type == 'run_ai_agent':
                return self._action_run_ai_agent(parsed_config)

            elif action_type == 'send_notification':
                return self._action_send_notification(parsed_config)

            elif action_type == 'update_record':
                return self._action_update_record(parsed_config)

            elif action_type == 'delete_record':
                return self._action_delete_record(parsed_config)

            elif action_type == 'send_telegram':
                return self._action_send_telegram(parsed_config)

            elif action_type == 'create_project':
                return self._action_create_project(parsed_config)

            elif action_type == 'execute_workflow':
                return self._action_execute_workflow(parsed_config, context)

            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}"
                }

        except Exception as e:
            self.logger.error(f"Action {action_type} failed: {e}")
            return {
                "success": False,
                "action_type": action_type,
                "error": str(e)
            }

    def parse_variables(self, text: str, context: Dict) -> str:
        """
        Replace {{variables}} in text with values from context

        Supports nested access: {{user.name}}, {{data.items.0.title}}

        Args:
            text: Text with {{variable}} placeholders
            context: Dict with variable values

        Returns:
            Text with variables replaced

        Examples:
            >>> parse_variables("Hello {{user.name}}", {"user": {"name": "John"}})
            "Hello John"

            >>> parse_variables("Count: {{count}}", {"count": 5})
            "Count: 5"
        """
        if not isinstance(text, str):
            return text

        # Find all {{variable}} patterns
        pattern = r'\{\{([^}]+)\}\}'

        def replace_var(match):
            var_path = match.group(1).strip()
            value = self._get_nested_value(context, var_path)
            return str(value) if value is not None else ''

        return re.sub(pattern, replace_var, text)

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """
        Get value from nested dict using dot notation

        Args:
            data: Dict to search
            path: Dot-separated path (e.g., "user.name" or "items.0.title")

        Returns:
            Value at path or None if not found
        """
        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list):
                try:
                    index = int(key)
                    value = value[index] if 0 <= index < len(value) else None
                except (ValueError, IndexError):
                    return None
            else:
                return None

            if value is None:
                return None

        return value

    def _parse_config_variables(self, config: Dict, context: Dict) -> Dict:
        """Parse all string values in config for variables"""
        parsed = {}

        for key, value in config.items():
            if isinstance(value, str):
                parsed[key] = self.parse_variables(value, context)
            elif isinstance(value, dict):
                parsed[key] = self._parse_config_variables(value, context)
            elif isinstance(value, list):
                parsed[key] = [
                    self.parse_variables(item, context) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                parsed[key] = value

        return parsed

    # ========== ACTION HANDLERS ==========

    def _action_send_email(self, config: Dict) -> Dict:
        """Send email via Gmail MCP"""
        to = config.get('to')
        subject = config.get('subject')
        body = config.get('body', '')

        if not to or not subject:
            return {"success": False, "error": "to and subject required"}

        self.logger.info(f"send_email action: to={to}, subject={subject}")

        # Initialize MCP client if needed
        if not self.mcp_client:
            try:
                from agents.mcp_client import MCPClient
                self.mcp_client = MCPClient()
            except Exception as e:
                self.logger.warning(f"MCP client not available: {e}")
                # Fallback to simulation
                return {
                    "success": True,
                    "action_type": "send_email",
                    "result": {
                        "to": to,
                        "subject": subject,
                        "status": "sent (simulated - MCP not available)"
                    }
                }

        # Try to send via MCP (requires connection)
        try:
            # Note: In production, Gmail token should be loaded from user's integration settings
            # For MVP, we simulate since connection requires OAuth tokens
            self.logger.info("Gmail integration requires OAuth tokens - simulating send")
            return {
                "success": True,
                "action_type": "send_email",
                "result": {
                    "to": to,
                    "subject": subject,
                    "status": "sent (simulated - OAuth required)"
                }
            }
        except Exception as e:
            self.logger.error(f"Email send error: {e}")
            return {
                "success": False,
                "action_type": "send_email",
                "error": str(e)
            }

    def _action_create_record(self, config: Dict) -> Dict:
        """Create record in database"""
        database_id = config.get('database_id')
        data = config.get('data', {})

        if not database_id:
            return {"success": False, "error": "database_id required"}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO database_records (database_id, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (database_id, json.dumps(data), datetime.now().isoformat(), datetime.now().isoformat()))

            record_id = cursor.lastrowid
            conn.commit()

        self.logger.info(f"Created record {record_id} in database {database_id}")

        return {
            "success": True,
            "action_type": "create_record",
            "result": {
                "record_id": record_id,
                "database_id": database_id
            }
        }

    def _action_call_webhook(self, config: Dict) -> Dict:
        """Call external webhook via HTTP POST"""
        url = config.get('url')
        payload = config.get('payload', {})
        headers = config.get('headers', {})

        if not url:
            return {"success": False, "error": "url required"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            self.logger.info(f"Webhook called: {url} - Status {response.status_code}")

            return {
                "success": True,
                "action_type": "call_webhook",
                "result": {
                    "status_code": response.status_code,
                    "response": response.text[:500]  # Limit response size
                }
            }
        except Exception as e:
            self.logger.error(f"Webhook call failed: {e}")
            return {
                "success": False,
                "action_type": "call_webhook",
                "error": str(e)
            }

    def _action_run_ai_agent(self, config: Dict) -> Dict:
        """Execute AI Router with prompt"""
        prompt = config.get('prompt')
        task_type = config.get('task_type', 'general')

        if not prompt:
            return {"success": False, "error": "prompt required"}

        # TODO: Implement actual AI Router integration
        self.logger.info(f"run_ai_agent: task_type={task_type}, prompt={prompt[:50]}...")

        return {
            "success": True,
            "action_type": "run_ai_agent",
            "result": {
                "response": f"AI response to: {prompt[:50]}... (simulated)",
                "task_type": task_type
            }
        }

    def _action_send_notification(self, config: Dict) -> Dict:
        """Send notification (log message for now)"""
        message = config.get('message', 'No message')
        level = config.get('level', 'info')

        if level == 'error':
            self.logger.error(f"NOTIFICATION: {message}")
        elif level == 'warning':
            self.logger.warning(f"NOTIFICATION: {message}")
        else:
            self.logger.info(f"NOTIFICATION: {message}")

        return {
            "success": True,
            "action_type": "send_notification",
            "result": {
                "message": message,
                "level": level
            }
        }

    def _action_update_record(self, config: Dict) -> Dict:
        """Update record in database"""
        record_id = config.get('record_id')
        database_id = config.get('database_id')
        data = config.get('data', {})

        if not record_id or not database_id:
            return {"success": False, "error": "record_id and database_id required"}

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE database_records
                SET data_json = ?, updated_at = ?
                WHERE id = ? AND database_id = ?
            """, (json.dumps(data), datetime.now().isoformat(), record_id, database_id))
            conn.commit()

        self.logger.info(f"Updated record {record_id} in database {database_id}")

        return {
            "success": True,
            "action_type": "update_record",
            "result": {
                "record_id": record_id,
                "database_id": database_id
            }
        }

    def _action_delete_record(self, config: Dict) -> Dict:
        """Delete record from database"""
        record_id = config.get('record_id')
        database_id = config.get('database_id')

        if not record_id or not database_id:
            return {"success": False, "error": "record_id and database_id required"}

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM database_records
                WHERE id = ? AND database_id = ?
            """, (record_id, database_id))
            conn.commit()

        self.logger.info(f"Deleted record {record_id} from database {database_id}")

        return {
            "success": True,
            "action_type": "delete_record",
            "result": {
                "record_id": record_id,
                "database_id": database_id
            }
        }

    def _action_send_telegram(self, config: Dict) -> Dict:
        """Send Telegram message via MCP"""
        chat_id = config.get('chat_id')
        message = config.get('message')

        if not chat_id or not message:
            return {"success": False, "error": "chat_id and message required"}

        self.logger.info(f"send_telegram: chat_id={chat_id}, message={message[:50]}...")

        # Initialize MCP client if needed
        if not self.mcp_client:
            try:
                from agents.mcp_client import MCPClient
                self.mcp_client = MCPClient()
            except Exception as e:
                self.logger.warning(f"MCP client not available: {e}")
                # Fallback to simulation
                return {
                    "success": True,
                    "action_type": "send_telegram",
                    "result": {
                        "chat_id": chat_id,
                        "status": "sent (simulated - MCP not available)"
                    }
                }

        # Try to send via MCP (requires connection)
        try:
            # Note: In production, Telegram bot token should be loaded from user's integration settings
            # For MVP, we simulate since connection requires bot token
            self.logger.info("Telegram integration requires bot token - simulating send")
            return {
                "success": True,
                "action_type": "send_telegram",
                "result": {
                    "chat_id": chat_id,
                    "status": "sent (simulated - bot token required)"
                }
            }
        except Exception as e:
            self.logger.error(f"Telegram send error: {e}")
            return {
                "success": False,
                "action_type": "send_telegram",
                "error": str(e)
            }

    def _action_create_project(self, config: Dict) -> Dict:
        """Create new project"""
        user_id = config.get('user_id')
        name = config.get('name')
        description = config.get('description')

        if not user_id or not name:
            return {"success": False, "error": "user_id and name required"}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO projects (user_id, name, description, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, name, description, datetime.now().isoformat()))

            project_id = cursor.lastrowid
            conn.commit()

        self.logger.info(f"Created project {project_id}: {name}")

        return {
            "success": True,
            "action_type": "create_project",
            "result": {
                "project_id": project_id,
                "name": name
            }
        }

    def _action_execute_workflow(self, config: Dict, context: Dict) -> Dict:
        """Execute another workflow (chain workflows)"""
        workflow_id = config.get('workflow_id')

        if not workflow_id:
            return {"success": False, "error": "workflow_id required"}

        # Prevent infinite loops
        if context.get('workflow', {}).get('id') == workflow_id:
            return {"success": False, "error": "Cannot execute self (infinite loop prevention)"}

        self.logger.info(f"Chaining to workflow {workflow_id}")

        # Execute the other workflow
        return self.execute(workflow_id, context)

    # ========== DATABASE HELPERS ==========

    def _load_workflow(self, workflow_id: int) -> Optional[Dict]:
        """Load workflow from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows WHERE id = ?
            """, (workflow_id,))

            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def _log_execution(self, workflow_id: int, status: str,
                      result_json: Optional[str], error: Optional[str]) -> int:
        """Log workflow execution to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO workflow_executions
                (workflow_id, status, result_json, error, executed_at)
                VALUES (?, ?, ?, ?, ?)
            """, (workflow_id, status, result_json, error, datetime.now().isoformat()))

            execution_id = cursor.lastrowid
            conn.commit()

        return execution_id
