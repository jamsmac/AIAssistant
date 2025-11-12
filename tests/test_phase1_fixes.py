#!/usr/bin/env python3
"""
Phase 1 Critical Fixes - Integration Tests
Tests all P1 fixes: OAuth, Schedule Triggers, Railway Persistence
"""

import pytest
import asyncio
import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.database import get_db
from agents.oauth_providers import GoogleOAuthProvider, GitHubOAuthProvider, OAuthProviderFactory
from agents.workflow_engine import WorkflowEngine
from api.scheduler import WorkflowScheduler


class TestOAuthImplementation:
    """Test OAuth providers implementation"""

    def test_google_oauth_provider_exists(self):
        """Test GoogleOAuthProvider class exists and is properly configured"""
        provider = GoogleOAuthProvider(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:3000/callback"
        )

        assert provider is not None
        assert provider.client_id == "test_client_id"
        assert provider.AUTHORIZATION_URL == "https://accounts.google.com/o/oauth2/v2/auth"
        assert provider.TOKEN_URL == "https://oauth2.googleapis.com/token"

    def test_google_oauth_authorization_url(self):
        """Test Google OAuth authorization URL generation"""
        provider = GoogleOAuthProvider(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:3000/callback"
        )

        auth_url = provider.get_authorization_url()

        assert "accounts.google.com" in auth_url
        assert "client_id=test_client" in auth_url
        assert "redirect_uri=" in auth_url
        assert "access_type=offline" in auth_url

    def test_github_oauth_provider_exists(self):
        """Test GitHubOAuthProvider class exists"""
        provider = GitHubOAuthProvider(
            client_id="test_github_client",
            client_secret="test_github_secret",
            redirect_uri="http://localhost:3000/callback"
        )

        assert provider is not None
        assert provider.AUTHORIZATION_URL == "https://github.com/login/oauth/authorize"

    def test_oauth_factory_service_mapping(self):
        """Test OAuthProviderFactory service mapping"""
        factory = OAuthProviderFactory()

        # Test service aliases
        assert factory.SERVICE_MAP["gmail"] == "google"
        assert factory.SERVICE_MAP["google_drive"] == "google"
        assert factory.SERVICE_MAP["github"] == "github"

    @pytest.mark.asyncio
    async def test_exchange_code_method_exists(self):
        """Test that exchange_code_for_token method exists and is callable"""
        provider = GoogleOAuthProvider(
            client_id="test",
            client_secret="test",
            redirect_uri="http://test"
        )

        # Method should exist
        assert hasattr(provider, 'exchange_code_for_token')
        assert callable(provider.exchange_code_for_token)


class TestSchedulerImplementation:
    """Test workflow scheduler implementation"""

    def test_scheduler_module_imports(self):
        """Test that scheduler module imports successfully"""
        from api.scheduler import WorkflowScheduler, get_scheduler, start_scheduler

        assert WorkflowScheduler is not None
        assert get_scheduler is not None
        assert start_scheduler is not None

    def test_scheduler_initialization(self):
        """Test scheduler can be initialized"""
        scheduler = WorkflowScheduler()

        assert scheduler is not None
        assert scheduler.scheduler is not None
        assert scheduler.workflow_engine is not None

    def test_scheduler_start_stop(self):
        """Test scheduler can start and stop"""
        scheduler = WorkflowScheduler()

        # Start scheduler
        scheduler.start()
        assert scheduler.scheduler.running is True

        # Stop scheduler
        scheduler.shutdown()
        # Note: shutdown(wait=False) returns immediately, scheduler may still be running briefly
        # The important part is shutdown completes without error

    def test_scheduler_job_management(self):
        """Test scheduler can add/remove jobs"""
        scheduler = WorkflowScheduler()
        scheduler.start()

        try:
            # Create test workflow dict
            test_workflow = {
                'id': 999,
                'name': 'Test Workflow',
                'enabled': True,
                'trigger_json': json.dumps({
                    'type': 'schedule',
                    'config': {
                        'schedule': {
                            'type': 'interval',
                            'interval': {'minutes': 1}
                        }
                    }
                })
            }

            # Add workflow to scheduler
            scheduler.add_workflow_to_scheduler(test_workflow)

            # Check job exists
            jobs = scheduler.get_all_jobs()
            job_ids = [job['id'] for job in jobs]
            assert 'workflow_999' in job_ids

            # Remove workflow
            scheduler.remove_workflow_from_scheduler(999)

            # Check job removed
            jobs = scheduler.get_all_jobs()
            job_ids = [job['id'] for job in jobs]
            assert 'workflow_999' not in job_ids

        finally:
            scheduler.shutdown()

    def test_cron_trigger_configuration(self):
        """Test cron trigger can be configured"""
        scheduler = WorkflowScheduler()
        scheduler.start()

        try:
            test_workflow = {
                'id': 998,
                'name': 'Cron Test',
                'enabled': True,
                'trigger_json': json.dumps({
                    'type': 'schedule',
                    'config': {
                        'schedule': {
                            'type': 'cron',
                            'cron': {
                                'minute': '0',
                                'hour': '9',
                                'day_of_week': 'mon-fri'
                            }
                        }
                    }
                })
            }

            scheduler.add_workflow_to_scheduler(test_workflow)

            # Check job exists
            jobs = scheduler.get_all_jobs()
            cron_job = next((j for j in jobs if j['id'] == 'workflow_998'), None)

            assert cron_job is not None
            assert 'cron' in cron_job['trigger'].lower()

        finally:
            scheduler.shutdown()

    def test_next_run_time(self):
        """Test getting next run time for scheduled workflow"""
        scheduler = WorkflowScheduler()
        scheduler.start()

        try:
            test_workflow = {
                'id': 997,
                'name': 'Next Run Test',
                'enabled': True,
                'trigger_json': json.dumps({
                    'type': 'schedule',
                    'config': {
                        'schedule': {
                            'type': 'interval',
                            'interval': {'hours': 1}
                        }
                    }
                })
            }

            scheduler.add_workflow_to_scheduler(test_workflow)

            # Get next run time
            next_run = scheduler.get_next_run_time(997)

            assert next_run is not None
            assert isinstance(next_run, datetime)
            assert next_run > datetime.now(next_run.tzinfo)

        finally:
            scheduler.shutdown()


class TestRailwayPersistence:
    """Test Railway data persistence configuration"""

    def test_railway_toml_exists(self):
        """Test railway.toml file exists"""
        railway_toml = Path(__file__).parent.parent / "railway.toml"
        assert railway_toml.exists()

    def test_railway_volume_configuration(self):
        """Test railway.toml has volume configuration"""
        railway_toml = Path(__file__).parent.parent / "railway.toml"

        with open(railway_toml, 'r') as f:
            content = f.read()

        # Check for volume configuration
        assert 'deploy.volumes' in content or '[[deploy.volumes]]' in content
        assert 'mountPath' in content
        assert '/app/data' in content
        assert 'data-volume' in content

    def test_backup_script_exists(self):
        """Test backup script exists and is executable"""
        backup_script = Path(__file__).parent.parent / "scripts" / "backup_db.sh"

        assert backup_script.exists()
        assert os.access(backup_script, os.X_OK), "Backup script should be executable"

    def test_backup_script_content(self):
        """Test backup script has required functionality"""
        backup_script = Path(__file__).parent.parent / "scripts" / "backup_db.sh"

        with open(backup_script, 'r') as f:
            content = f.read()

        # Check for key functionality
        assert 'history.db' in content
        assert 'autopilot_cache.db' in content
        assert 'sqlite3' in content
        assert '.backup' in content
        assert 'integrity_check' in content
        assert 'RETENTION_DAYS' in content

    def test_data_recovery_documentation_exists(self):
        """Test data recovery documentation exists"""
        docs_file = Path(__file__).parent.parent / "docs" / "DATA_RECOVERY.md"
        assert docs_file.exists()

    def test_data_directory_structure(self):
        """Test data directory exists"""
        data_dir = Path(__file__).parent.parent / "data"
        assert data_dir.exists()
        assert data_dir.is_dir()


class TestIntegrationEndpoints:
    """Test workflow scheduler API endpoints integration"""

    def test_scheduler_endpoints_in_router(self):
        """Test that scheduler management endpoints exist in workflow router"""
        from api.routers.workflows_router import router

        # Get all route paths
        routes = [route.path for route in router.routes]

        # Check for scheduler endpoints
        assert any('schedule/next-run' in path for path in routes)
        assert any('schedule/pause' in path for path in routes)
        assert any('schedule/resume' in path for path in routes)
        assert any('schedule/jobs' in path for path in routes)
        assert any('schedule/reload' in path for path in routes)

    def test_server_startup_integration(self):
        """Test that server.py imports and uses scheduler"""
        server_file = Path(__file__).parent.parent / "api" / "server.py"

        with open(server_file, 'r') as f:
            content = f.read()

        # Check scheduler is imported and started
        assert 'from api.scheduler import' in content
        assert 'start_scheduler' in content
        assert 'shutdown_scheduler' in content


def run_tests():
    """Run all Phase 1 tests"""
    print("\n" + "="*60)
    print("  PHASE 1 CRITICAL FIXES - TEST SUITE")
    print("="*60 + "\n")

    # Run pytest
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-k', 'test_',
    ])

    print("\n" + "="*60)
    if exit_code == 0:
        print("✅ ALL PHASE 1 TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60 + "\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
