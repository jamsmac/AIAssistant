"""
Workflow Scheduler - Manages scheduled workflow executions
Uses APScheduler for background job scheduling
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job
import sqlite3
from pathlib import Path

from workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "history.db"


class WorkflowScheduler:
    """
    Manages scheduled workflow executions using APScheduler

    Features:
    - Loads active scheduled workflows from database
    - Registers them with APScheduler
    - Executes workflows at specified times
    - Supports cron expressions and intervals
    """

    def __init__(self, db_path: str = str(DB_PATH)):
        """Initialize workflow scheduler"""
        self.db_path = db_path
        self.workflow_engine = WorkflowEngine(db_path)

        # Initialize APScheduler
        self.scheduler = BackgroundScheduler()
        self.logger = logging.getLogger(__name__)

        # Track registered jobs: {workflow_id: job}
        self.jobs: Dict[int, Job] = {}

        self.logger.info("WorkflowScheduler initialized")

    def start(self):
        """Start the scheduler and load active workflows"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Scheduler started")

            # Load and register all active scheduled workflows
            self.load_scheduled_workflows()

    def shutdown(self):
        """Gracefully shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            self.logger.info("Scheduler stopped")

    def load_scheduled_workflows(self):
        """Load all active workflows with schedule triggers from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all active workflows with schedule trigger
            cursor.execute("""
                SELECT id, user_id, name, trigger_type, trigger_config, actions_json, enabled
                FROM workflows
                WHERE trigger_type = 'schedule' AND enabled = 1
            """)

            workflows = cursor.fetchall()
            conn.close()

            self.logger.info(f"Found {len(workflows)} active scheduled workflows")

            # Register each workflow
            for workflow in workflows:
                self.register_workflow(dict(workflow))

        except Exception as e:
            self.logger.error(f"Error loading scheduled workflows: {e}")

    def register_workflow(self, workflow: Dict):
        """
        Register a workflow with the scheduler

        Args:
            workflow: Workflow dict with id, trigger_config, etc.
        """
        workflow_id = workflow['id']

        # Remove existing job if any
        if workflow_id in self.jobs:
            self.unregister_workflow(workflow_id)

        try:
            # Parse trigger configuration
            trigger_config = workflow.get('trigger_config')
            if not trigger_config:
                self.logger.warning(f"Workflow {workflow_id} has no trigger_config")
                return

            # Parse trigger (can be string or dict)
            if isinstance(trigger_config, str):
                import json
                trigger_config = json.loads(trigger_config)

            # Create appropriate trigger
            trigger = self._create_trigger(trigger_config)

            if not trigger:
                self.logger.warning(f"Could not create trigger for workflow {workflow_id}")
                return

            # Add job to scheduler
            job = self.scheduler.add_job(
                func=self._execute_workflow,
                trigger=trigger,
                args=[workflow_id],
                id=f"workflow_{workflow_id}",
                name=f"Workflow: {workflow['name']}",
                replace_existing=True
            )

            self.jobs[workflow_id] = job

            next_run = job.next_run_time
            self.logger.info(f"Registered workflow {workflow_id} ('{workflow['name']}'). Next run: {next_run}")

        except Exception as e:
            self.logger.error(f"Error registering workflow {workflow_id}: {e}")

    def unregister_workflow(self, workflow_id: int):
        """
        Unregister a workflow from the scheduler

        Args:
            workflow_id: ID of workflow to unregister
        """
        try:
            job_id = f"workflow_{workflow_id}"

            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                self.logger.info(f"Unregistered workflow {workflow_id}")

            if workflow_id in self.jobs:
                del self.jobs[workflow_id]

        except Exception as e:
            self.logger.error(f"Error unregistering workflow {workflow_id}: {e}")

    def _create_trigger(self, trigger_config: Dict):
        """
        Create APScheduler trigger from config

        Supports:
        - Cron expressions: {"type": "cron", "expression": "0 9 * * *"}
        - Intervals: {"type": "interval", "minutes": 30}

        Args:
            trigger_config: Trigger configuration dict

        Returns:
            APScheduler trigger object or None
        """
        trigger_type = trigger_config.get('type', 'interval')

        try:
            if trigger_type == 'cron':
                # Cron expression
                expression = trigger_config.get('expression')
                if expression:
                    return CronTrigger.from_crontab(expression)
                else:
                    self.logger.error("Cron trigger missing 'expression'")
                    return None

            elif trigger_type == 'interval':
                # Interval trigger (seconds, minutes, hours, days)
                kwargs = {}

                for unit in ['seconds', 'minutes', 'hours', 'days', 'weeks']:
                    if unit in trigger_config:
                        kwargs[unit] = trigger_config[unit]

                if kwargs:
                    return IntervalTrigger(**kwargs)
                else:
                    self.logger.error("Interval trigger missing time units")
                    return None

            else:
                self.logger.error(f"Unknown trigger type: {trigger_type}")
                return None

        except Exception as e:
            self.logger.error(f"Error creating trigger: {e}")
            return None

    def _execute_workflow(self, workflow_id: int):
        """
        Execute a workflow (called by scheduler)

        Args:
            workflow_id: ID of workflow to execute
        """
        try:
            self.logger.info(f"Scheduler executing workflow {workflow_id}")

            # Execute through workflow engine
            result = self.workflow_engine.execute(workflow_id, context={
                'triggered_by': 'schedule',
                'triggered_at': datetime.now().isoformat()
            })

            if result.get('success'):
                self.logger.info(f"Workflow {workflow_id} executed successfully")
            else:
                self.logger.error(f"Workflow {workflow_id} failed: {result.get('error')}")

        except Exception as e:
            self.logger.error(f"Error executing workflow {workflow_id}: {e}")

    def get_scheduled_jobs(self) -> List[Dict]:
        """
        Get list of all scheduled jobs

        Returns:
            List of job info dicts
        """
        jobs = []

        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })

        return jobs

    def pause_workflow(self, workflow_id: int):
        """Pause a scheduled workflow"""
        job_id = f"workflow_{workflow_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.pause_job(job_id)
            self.logger.info(f"Paused workflow {workflow_id}")

    def resume_workflow(self, workflow_id: int):
        """Resume a paused workflow"""
        job_id = f"workflow_{workflow_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.resume_job(job_id)
            self.logger.info(f"Resumed workflow {workflow_id}")


# Global scheduler instance
_scheduler_instance: Optional[WorkflowScheduler] = None


def get_scheduler(db_path: str = str(DB_PATH)) -> WorkflowScheduler:
    """Get or create global scheduler instance"""
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = WorkflowScheduler(db_path)

    return _scheduler_instance


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Global workflow scheduler started")


def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler_instance

    if _scheduler_instance:
        _scheduler_instance.shutdown()
        _scheduler_instance = None
        logger.info("Global workflow scheduler stopped")
