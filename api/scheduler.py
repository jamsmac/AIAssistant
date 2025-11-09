"""
Workflow Scheduler Service
Manages scheduled workflow executions using APScheduler
"""

import logging
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from agents.database import HistoryDatabase, get_db
from agents.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)

class WorkflowScheduler:
    """Manages scheduled workflow executions"""

    def __init__(self, db: Optional[HistoryDatabase] = None):
        """
        Initialize workflow scheduler

        Args:
            db: Database instance (optional, will use default if not provided)
        """
        self.db = db or get_db()
        self.workflow_engine = WorkflowEngine()

        # Configure APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(10)
        }
        job_defaults = {
            'coalesce': True,  # Combine multiple missed runs into one
            'max_instances': 3,  # Max concurrent instances of same job
            'misfire_grace_time': 300  # 5 minutes grace period
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )

        logger.info("WorkflowScheduler initialized")

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Workflow scheduler started")
        else:
            logger.warning("Scheduler already running")

    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Workflow scheduler shutdown")

    def load_scheduled_workflows(self):
        """
        Load all workflows with schedule triggers and add them to scheduler

        Returns:
            int: Number of workflows loaded
        """
        try:
            # Get all workflows with schedule trigger
            workflows = self.db.get_workflows_by_trigger_type("schedule")

            loaded_count = 0
            for workflow in workflows:
                if not workflow.get('enabled'):
                    logger.debug(f"Skipping disabled workflow {workflow['id']}: {workflow['name']}")
                    continue

                try:
                    self.add_workflow_to_scheduler(workflow)
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"Failed to schedule workflow {workflow['id']}: {e}")

            logger.info(f"Loaded {loaded_count} scheduled workflows")
            return loaded_count

        except Exception as e:
            logger.error(f"Error loading scheduled workflows: {e}")
            return 0

    def add_workflow_to_scheduler(self, workflow: Dict):
        """
        Add a single workflow to the scheduler

        Args:
            workflow: Workflow dict with id, name, trigger_json
        """
        workflow_id = workflow['id']
        workflow_name = workflow['name']

        # Parse trigger configuration
        trigger_json = workflow.get('trigger_json', '{}')
        trigger_config = json.loads(trigger_json) if isinstance(trigger_json, str) else trigger_json

        schedule_config = trigger_config.get('config', {}).get('schedule', {})
        schedule_type = schedule_config.get('type')

        # Create appropriate trigger
        trigger = None
        job_id = f"workflow_{workflow_id}"

        if schedule_type == 'cron':
            # Cron schedule: { "minute": "0", "hour": "9", "day_of_week": "mon-fri" }
            cron_config = schedule_config.get('cron', {})
            trigger = CronTrigger(
                minute=cron_config.get('minute', '*'),
                hour=cron_config.get('hour', '*'),
                day=cron_config.get('day', '*'),
                month=cron_config.get('month', '*'),
                day_of_week=cron_config.get('day_of_week', '*'),
                timezone='UTC'
            )
            logger.info(f"Scheduling cron workflow {workflow_id}: {workflow_name} - {cron_config}")

        elif schedule_type == 'interval':
            # Interval schedule: { "hours": 2 } or { "minutes": 30 }
            interval_config = schedule_config.get('interval', {})
            trigger = IntervalTrigger(
                weeks=interval_config.get('weeks', 0),
                days=interval_config.get('days', 0),
                hours=interval_config.get('hours', 0),
                minutes=interval_config.get('minutes', 0),
                seconds=interval_config.get('seconds', 0),
                timezone='UTC'
            )
            logger.info(f"Scheduling interval workflow {workflow_id}: {workflow_name} - {interval_config}")

        elif schedule_type == 'date':
            # One-time schedule: { "run_date": "2025-11-15 09:00:00" }
            run_date = schedule_config.get('date', {}).get('run_date')
            if run_date:
                # Parse date string
                if isinstance(run_date, str):
                    run_date = datetime.fromisoformat(run_date)
                trigger = DateTrigger(run_date=run_date, timezone='UTC')
                logger.info(f"Scheduling one-time workflow {workflow_id}: {workflow_name} - {run_date}")
            else:
                logger.warning(f"Date schedule for workflow {workflow_id} missing run_date")
                return

        else:
            logger.warning(f"Unknown schedule type '{schedule_type}' for workflow {workflow_id}")
            return

        # Add job to scheduler
        self.scheduler.add_job(
            func=self._execute_scheduled_workflow,
            trigger=trigger,
            id=job_id,
            name=workflow_name,
            args=[workflow_id],
            replace_existing=True
        )

        logger.info(f"Added workflow {workflow_id} to scheduler with trigger {schedule_type}")

    def remove_workflow_from_scheduler(self, workflow_id: int):
        """
        Remove workflow from scheduler

        Args:
            workflow_id: Workflow ID to remove
        """
        job_id = f"workflow_{workflow_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed workflow {workflow_id} from scheduler")
        except Exception as e:
            logger.debug(f"Workflow {workflow_id} not in scheduler: {e}")

    def _execute_scheduled_workflow(self, workflow_id: int):
        """
        Execute workflow (called by scheduler)

        Args:
            workflow_id: Workflow ID to execute
        """
        logger.info(f"Executing scheduled workflow {workflow_id}")

        try:
            # Execute workflow with schedule trigger context
            context = {
                'trigger_type': 'schedule',
                'triggered_at': datetime.utcnow().isoformat(),
                'trigger_source': 'scheduler'
            }

            result = self.workflow_engine.execute(workflow_id, context)

            if result.get('success'):
                logger.info(f"Workflow {workflow_id} executed successfully")
            else:
                logger.error(f"Workflow {workflow_id} execution failed: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error executing scheduled workflow {workflow_id}: {e}", exc_info=True)

    def get_next_run_time(self, workflow_id: int) -> Optional[datetime]:
        """
        Get next scheduled run time for a workflow

        Args:
            workflow_id: Workflow ID

        Returns:
            Next run datetime or None if not scheduled
        """
        job_id = f"workflow_{workflow_id}"
        job = self.scheduler.get_job(job_id)

        if job and job.next_run_time:
            return job.next_run_time

        return None

    def pause_workflow(self, workflow_id: int):
        """
        Pause scheduled workflow

        Args:
            workflow_id: Workflow ID to pause
        """
        job_id = f"workflow_{workflow_id}"
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused workflow {workflow_id}")
        except Exception as e:
            logger.error(f"Failed to pause workflow {workflow_id}: {e}")

    def resume_workflow(self, workflow_id: int):
        """
        Resume paused workflow

        Args:
            workflow_id: Workflow ID to resume
        """
        job_id = f"workflow_{workflow_id}"
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed workflow {workflow_id}")
        except Exception as e:
            logger.error(f"Failed to resume workflow {workflow_id}: {e}")

    def get_all_jobs(self) -> List[Dict]:
        """
        Get all scheduled jobs

        Returns:
            List of job information dicts
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs


# Global scheduler instance
_scheduler_instance: Optional[WorkflowScheduler] = None


def get_scheduler() -> WorkflowScheduler:
    """Get global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = WorkflowScheduler()
    return _scheduler_instance


def start_scheduler():
    """Start the global scheduler and load workflows"""
    scheduler = get_scheduler()
    scheduler.start()
    scheduler.load_scheduled_workflows()
    return scheduler


def shutdown_scheduler():
    """Shutdown the global scheduler"""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.shutdown()
        _scheduler_instance = None
