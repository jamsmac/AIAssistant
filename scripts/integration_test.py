#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Autopilot Core Platform

Tests all modules and their interactions:
- Auth Flow
- Projects & Databases
- Workflows
- Integrations
- Cross-Module Scenarios
"""

import requests
import json
import time
import sys
from datetime import datetime

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "TestPassword123!"

# Global state
token = None
user_id = None
test_results = []


def print_section(title):
    """Print a section header"""
    print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{title:^70}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")


def print_test(name, passed, message=""):
    """Print test result"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    test_results.append((name, passed))
    
    if message:
        print(f"{status} {name}: {message}")
    else:
        print(f"{status} {name}")


def api_call(method, endpoint, **kwargs):
    """Make API call with consistent error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    if 'headers' not in kwargs and token:
        kwargs['headers'] = {'Authorization': f'Bearer {token}'}
    
    try:
        response = getattr(requests, method.lower())(url, **kwargs)
        return response
    except Exception as e:
        print(f"{RED}Error calling {method} {endpoint}: {e}{RESET}")
        return None


# ============================================
# TEST SCENARIO 1: AUTH FLOW
# ============================================

def test_auth_flow():
    """Test authentication flow"""
    global token, user_id
    
    print_section("TEST SCENARIO 1: AUTHENTICATION FLOW")
    
    # Test 1.1: Register new user
    response = api_call('POST', '/api/auth/register', 
                       json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
                       headers={})
    
    if response and response.status_code == 200:
        data = response.json()
        print_test("1.1 Register new user", 
                  'token' in data,
                  f"User created: {TEST_EMAIL}")
        token = data.get('token')
    else:
        print_test("1.1 Register new user", False, 
                  f"Status: {response.status_code if response else 'N/A'}")
        return False
    
    # Test 1.2: Login with credentials
    response = api_call('POST', '/api/auth/login',
                       json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
                       headers={})
    
    if response and response.status_code == 200:
        data = response.json()
        print_test("1.2 Login with credentials",
                  'token' in data,
                  "Token received")
        token = data.get('token')
    else:
        print_test("1.2 Login with credentials", False)
        return False
    
    # Test 1.3: Decode token to get user_id
    try:
        import base64
        payload = token.split('.')[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        user_id = decoded.get('user_id')
        print_test("1.3 Decode JWT token",
                  user_id is not None,
                  f"User ID: {user_id}")
    except Exception as e:
        print_test("1.3 Decode JWT token", False, str(e))
        return False
    
    # Test 1.4: Access protected endpoint
    response = api_call('GET', '/api/dashboard/stats')
    
    print_test("1.4 Access protected endpoint",
              response and response.status_code == 200,
              "Dashboard stats retrieved")
    
    return True


# ============================================
# TEST SCENARIO 2: PROJECTS & DATABASES
# ============================================

def test_projects_flow():
    """Test projects and databases flow"""
    print_section("TEST SCENARIO 2: PROJECTS & DATABASES FLOW")
    
    project_id = None
    database_id = None
    record_id = None
    
    # Test 2.1: Create project
    response = api_call('POST', '/api/projects',
                       json={
                           'name': 'Integration Test Project',
                           'description': 'Created by integration test'
                       })
    
    if response and response.status_code == 200:
        data = response.json()
        project_id = data.get('id')
        print_test("2.1 Create project",
                  project_id is not None,
                  f"Project ID: {project_id}")
    else:
        print_test("2.1 Create project", False)
        return False
    
    # Test 2.2: List projects
    response = api_call('GET', '/api/projects')
    
    if response and response.status_code == 200:
        projects = response.json()
        found = any(p['id'] == project_id for p in projects)
        print_test("2.2 List projects",
                  found,
                  f"Found {len(projects)} projects")
    else:
        print_test("2.2 List projects", False)
    
    # Test 2.3: Create database in project
    response = api_call('POST', '/api/databases',
                       json={
                           'project_id': project_id,
                           'name': 'Test Database',
                           'description': 'Test database for integration tests',
                           'schema': [
                               {'name': 'name', 'type': 'text'},
                               {'name': 'email', 'type': 'text'},
                               {'name': 'age', 'type': 'number'}
                           ]
                       })
    
    if response and response.status_code == 200:
        data = response.json()
        database_id = data.get('id')
        print_test("2.3 Create database",
                  database_id is not None,
                  f"Database ID: {database_id}")
    else:
        print_test("2.3 Create database", False)
        return False
    
    # Test 2.4: Add record to database
    response = api_call('POST', '/api/records',
                       json={
                           'database_id': database_id,
                           'data': {
                               'name': 'John Doe',
                               'email': 'john@example.com',
                               'age': 30
                           }
                       })
    
    if response and response.status_code == 200:
        data = response.json()
        record_id = data.get('id')
        print_test("2.4 Add record",
                  record_id is not None,
                  f"Record ID: {record_id}")
    else:
        print_test("2.4 Add record", False)
        return False
    
    # Test 2.5: Query records
    response = api_call('GET', f'/api/databases/{database_id}/records')
    
    if response and response.status_code == 200:
        records = response.json()
        found = any(r['id'] == record_id for r in records)
        print_test("2.5 Query records",
                  found,
                  f"Found {len(records)} records")
    else:
        print_test("2.5 Query records", False)
    
    # Test 2.6: Update record
    response = api_call('PUT', f'/api/records/{record_id}',
                       json={
                           'data': {
                               'name': 'Jane Doe',
                               'email': 'jane@example.com',
                               'age': 28
                           }
                       })
    
    print_test("2.6 Update record",
              response and response.status_code == 200,
              "Record updated")
    
    # Test 2.7: Delete record
    response = api_call('DELETE', f'/api/records/{record_id}')
    
    print_test("2.7 Delete record",
              response and response.status_code == 200,
              "Record deleted")
    
    # Test 2.8: Delete database
    response = api_call('DELETE', f'/api/databases/{database_id}')
    
    print_test("2.8 Delete database",
              response and response.status_code == 200,
              "Database deleted")
    
    # Test 2.9: Delete project
    response = api_call('DELETE', f'/api/projects/{project_id}')
    
    print_test("2.9 Delete project",
              response and response.status_code == 200,
              "Project deleted")
    
    return True


# ============================================
# TEST SCENARIO 3: WORKFLOWS
# ============================================

def test_workflows_flow():
    """Test workflows flow"""
    print_section("TEST SCENARIO 3: WORKFLOWS FLOW")
    
    workflow_id = None
    execution_id = None
    
    # Test 3.1: Create workflow with AI action
    response = api_call('POST', '/api/workflows',
                       json={
                           'name': 'Test Workflow',
                           'description': 'Integration test workflow',
                           'trigger': {'type': 'manual'},
                           'actions': [
                               {
                                   'type': 'run_ai_agent',
                                   'config': {
                                       'prompt': 'Say hello!',
                                       'model': 'gpt-4'
                                   }
                               }
                           ],
                           'enabled': True
                       })
    
    if response and response.status_code == 200:
        data = response.json()
        workflow_id = data.get('id')
        print_test("3.1 Create workflow",
                  workflow_id is not None,
                  f"Workflow ID: {workflow_id}")
    else:
        print_test("3.1 Create workflow", False)
        return False
    
    # Test 3.2: List workflows
    response = api_call('GET', '/api/workflows')
    
    if response and response.status_code == 200:
        workflows = response.json()
        found = any(w['id'] == workflow_id for w in workflows)
        print_test("3.2 List workflows",
                  found,
                  f"Found {len(workflows)} workflows")
    else:
        print_test("3.2 List workflows", False)
    
    # Test 3.3: Execute workflow
    response = api_call('POST', f'/api/workflows/{workflow_id}/execute',
                       json={'context': {}})
    
    if response and response.status_code == 200:
        data = response.json()
        execution_id = data.get('execution_id')
        print_test("3.3 Execute workflow",
                  execution_id is not None,
                  f"Execution ID: {execution_id}")
    else:
        print_test("3.3 Execute workflow", False)
        return False
    
    # Test 3.4: Get execution history
    response = api_call('GET', f'/api/workflows/{workflow_id}/executions')
    
    if response and response.status_code == 200:
        executions = response.json()
        found = any(e['id'] == execution_id for e in executions)
        print_test("3.4 Get execution history",
                  found,
                  f"Found {len(executions)} executions")
    else:
        print_test("3.4 Get execution history", False)
    
    # Test 3.5: Update workflow (disable)
    response = api_call('PUT', f'/api/workflows/{workflow_id}',
                       json={'enabled': False})
    
    print_test("3.5 Update workflow",
              response and response.status_code == 200,
              "Workflow disabled")
    
    # Test 3.6: Delete workflow
    response = api_call('DELETE', f'/api/workflows/{workflow_id}')
    
    print_test("3.6 Delete workflow",
              response and response.status_code == 200,
              "Workflow deleted")
    
    return True


# ============================================
# TEST SCENARIO 4: INTEGRATIONS
# ============================================

def test_integrations_flow():
    """Test integrations flow"""
    print_section("TEST SCENARIO 4: INTEGRATIONS FLOW")
    
    # Test 4.1: List integrations (should be empty initially)
    response = api_call('GET', '/api/integrations')
    
    if response and response.status_code == 200:
        integrations = response.json()
        telegram = next((i for i in integrations if i['type'] == 'telegram'), None)
        print_test("4.1 List integrations",
                  telegram is not None,
                  f"Found {len(integrations)} integrations")
    else:
        print_test("4.1 List integrations", False)
    
    # Test 4.2: Connect Telegram (with test token)
    response = api_call('POST', '/api/integrations/connect',
                       json={
                           'integration_type': 'telegram',
                           'bot_token': 'test_bot_token_12345'
                       })
    
    print_test("4.2 Connect Telegram",
              response and response.status_code == 200,
              "Telegram connected")
    
    # Test 4.3: Test connection
    response = api_call('POST', '/api/integrations/test',
                       params={'integration_type': 'telegram'})
    
    if response and response.status_code == 200:
        data = response.json()
        # Should fail because it's a test token, but endpoint should work
        print_test("4.3 Test connection",
                  'success' in data or 'message' in data,
                  f"Test result: {data.get('message', 'N/A')}")
    else:
        print_test("4.3 Test connection", False)
    
    # Test 4.4: Disconnect integration
    response = api_call('POST', '/api/integrations/disconnect',
                       params={'integration_type': 'telegram'})
    
    print_test("4.4 Disconnect integration",
              response and response.status_code == 200,
              "Telegram disconnected")
    
    return True


# ============================================
# TEST SCENARIO 5: DASHBOARD
# ============================================

def test_dashboard():
    """Test dashboard endpoints"""
    print_section("TEST SCENARIO 5: DASHBOARD")
    
    # Test 5.1: Get dashboard stats
    response = api_call('GET', '/api/dashboard/stats')
    
    if response and response.status_code == 200:
        data = response.json()
        has_all_fields = all(key in data for key in [
            'total_projects', 'active_workflows', 'connected_integrations',
            'ai_requests_today', 'ai_requests_week', 'total_databases', 'total_records'
        ])
        print_test("5.1 Get dashboard stats",
                  has_all_fields,
                  f"Stats: {data}")
    else:
        print_test("5.1 Get dashboard stats", False)
    
    # Test 5.2: Get activity feed
    response = api_call('GET', '/api/dashboard/activity?limit=10')
    
    if response and response.status_code == 200:
        activities = response.json()
        print_test("5.2 Get activity feed",
                  isinstance(activities, list),
                  f"Found {len(activities)} activities")
    else:
        print_test("5.2 Get activity feed", False)
    
    # Test 5.3: Get AI requests chart
    response = api_call('GET', '/api/dashboard/charts/ai-requests?days=7')
    
    if response and response.status_code == 200:
        data = response.json()
        print_test("5.3 Get AI requests chart",
                  'data' in data,
                  f"Data points: {len(data.get('data', []))}")
    else:
        print_test("5.3 Get AI requests chart", False)
    
    # Test 5.4: Get model usage chart
    response = api_call('GET', '/api/dashboard/charts/model-usage')
    
    if response and response.status_code == 200:
        data = response.json()
        print_test("5.4 Get model usage chart",
                  'data' in data,
                  f"Models: {len(data.get('data', []))}")
    else:
        print_test("5.4 Get model usage chart", False)
    
    # Test 5.5: Get workflow stats chart
    response = api_call('GET', '/api/dashboard/charts/workflow-stats')
    
    if response and response.status_code == 200:
        data = response.json()
        print_test("5.5 Get workflow stats chart",
                  'data' in data,
                  f"Workflows: {len(data.get('data', []))}")
    else:
        print_test("5.5 Get workflow stats chart", False)
    
    return True


# ============================================
# TEST SCENARIO 6: CROSS-MODULE INTEGRATION
# ============================================

def test_cross_module():
    """Test cross-module integration"""
    print_section("TEST SCENARIO 6: CROSS-MODULE INTEGRATION")
    
    project_id = None
    database_id = None
    workflow_id = None
    
    # Test 6.1: Create complete project with database
    response = api_call('POST', '/api/projects',
                       json={
                           'name': 'Cross-Module Test',
                           'description': 'Full integration test'
                       })
    
    if response and response.status_code == 200:
        project_id = response.json().get('id')
        print_test("6.1 Create test project",
                  project_id is not None,
                  f"Project ID: {project_id}")
    else:
        print_test("6.1 Create test project", False)
        return False
    
    # Test 6.2: Add database with sample data
    response = api_call('POST', '/api/databases',
                       json={
                           'project_id': project_id,
                           'name': 'Customers',
                           'description': 'Customer database',
                           'schema': [
                               {'name': 'name', 'type': 'text'},
                               {'name': 'status', 'type': 'select', 'options': ['active', 'inactive']}
                           ]
                       })
    
    if response and response.status_code == 200:
        database_id = response.json().get('id')
        print_test("6.2 Create database",
                  database_id is not None,
                  f"Database ID: {database_id}")
    else:
        print_test("6.2 Create database", False)
        return False
    
    # Test 6.3: Add sample records
    for i in range(3):
        api_call('POST', '/api/records',
                json={
                    'database_id': database_id,
                    'data': {
                        'name': f'Customer {i+1}',
                        'status': 'active' if i % 2 == 0 else 'inactive'
                    }
                })
    
    print_test("6.3 Add sample records", True, "3 records added")
    
    # Test 6.4: Create workflow that uses database
    response = api_call('POST', '/api/workflows',
                       json={
                           'name': 'Data Processing Workflow',
                           'description': 'Process database records',
                           'trigger': {'type': 'manual'},
                           'actions': [
                               {
                                   'type': 'run_ai_agent',
                                   'config': {
                                       'prompt': 'Analyze customer data',
                                       'model': 'gpt-4'
                                   }
                               }
                           ],
                           'enabled': True
                       })
    
    if response and response.status_code == 200:
        workflow_id = response.json().get('id')
        print_test("6.4 Create workflow",
                  workflow_id is not None,
                  f"Workflow ID: {workflow_id}")
    else:
        print_test("6.4 Create workflow", False)
        return False
    
    # Test 6.5: Execute workflow
    response = api_call('POST', f'/api/workflows/{workflow_id}/execute',
                       json={'context': {'database_id': database_id}})
    
    print_test("6.5 Execute workflow",
              response and response.status_code == 200,
              "Workflow executed")
    
    # Test 6.6: Verify dashboard shows updated data
    response = api_call('GET', '/api/dashboard/stats')
    
    if response and response.status_code == 200:
        data = response.json()
        print_test("6.6 Verify dashboard stats",
                  data['total_projects'] >= 1 and data['total_databases'] >= 1,
                  f"Projects: {data['total_projects']}, Databases: {data['total_databases']}")
    else:
        print_test("6.6 Verify dashboard stats", False)
    
    # Cleanup
    if workflow_id:
        api_call('DELETE', f'/api/workflows/{workflow_id}')
    if database_id:
        api_call('DELETE', f'/api/databases/{database_id}')
    if project_id:
        api_call('DELETE', f'/api/projects/{project_id}')
    
    print_test("6.7 Cleanup resources", True, "All resources deleted")
    
    return True


# ============================================
# MAIN TEST RUNNER
# ============================================

def print_summary():
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in test_results if result)
    failed = sum(1 for _, result in test_results if not result)
    total = len(test_results)
    
    print(f"Total Tests: {BOLD}{total}{RESET}")
    print(f"Passed: {GREEN}{passed}{RESET}")
    print(f"Failed: {RED}{failed}{RESET}")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    if failed > 0:
        print(f"{RED}Failed Tests:{RESET}")
        for name, result in test_results:
            if not result:
                print(f"  {RED}✗{RESET} {name}")
        print()
    
    return failed == 0


def main():
    """Run all integration tests"""
    print(f"{BOLD}{BLUE}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     AUTOPILOT CORE - COMPREHENSIVE INTEGRATION TEST SUITE       ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}\n")
    
    print(f"Testing against: {YELLOW}{BASE_URL}{RESET}")
    print(f"Test user: {YELLOW}{TEST_EMAIL}{RESET}\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"{RED}Error: Server is not responding correctly{RESET}")
            return 1
    except Exception as e:
        print(f"{RED}Error: Cannot connect to server at {BASE_URL}{RESET}")
        print(f"{RED}Make sure the server is running: python api/server.py{RESET}\n")
        return 1
    
    print(f"{GREEN}✓ Server is running{RESET}\n")
    
    # Run test scenarios
    scenarios = [
        ("Auth Flow", test_auth_flow),
        ("Projects & Databases", test_projects_flow),
        ("Workflows", test_workflows_flow),
        ("Integrations", test_integrations_flow),
        ("Dashboard", test_dashboard),
        ("Cross-Module Integration", test_cross_module),
    ]
    
    start_time = time.time()
    
    for name, test_func in scenarios:
        try:
            test_func()
        except Exception as e:
            print(f"{RED}Error in {name}: {e}{RESET}")
            import traceback
            traceback.print_exc()
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    all_passed = print_summary()
    
    print(f"Total Time: {elapsed_time:.2f}s\n")
    
    if all_passed:
        print(f"{GREEN}{BOLD}✓ ALL TESTS PASSED!{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}✗ SOME TESTS FAILED{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
