#!/usr/bin/env python3
"""
Test script for Workflows API endpoints
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_response(response, title="Response"):
    """Pretty print response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

def main():
    # Step 1: Login
    print("\n🔐 Step 1: Authentication")
    login_data = {"email": "test@example.com", "password": "testpassword123"}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)

    if response.status_code != 200:
        print_response(response, "❌ Login failed")
        return

    print_response(response, "✅ Login successful")
    token = response.json()['token']
    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Create Workflow
    print("\n📋 Step 2: Create Workflow")
    workflow_data = {
        "name": "Test Notification Workflow",
        "trigger": {
            "type": "manual",
            "config": {}
        },
        "actions": [
            {
                "type": "send_notification",
                "config": {
                    "message": "Test notification from API",
                    "level": "info"
                }
            }
        ],
        "enabled": True
    }
    response = requests.post(f"{BASE_URL}/api/workflows", json=workflow_data, headers=headers)
    print_response(response, "✅ Workflow Created" if response.status_code == 200 else "❌ Failed")

    if response.status_code != 200:
        return

    workflow_id = response.json()['id']
    print(f"\n✅ Workflow ID: {workflow_id}")

    # Step 3: List Workflows
    print(f"\n📋 Step 3: List Workflows")
    response = requests.get(f"{BASE_URL}/api/workflows", headers=headers)
    print_response(response, "✅ Workflows List")

    # Step 4: Get Specific Workflow
    print(f"\n🔍 Step 4: Get Workflow {workflow_id}")
    response = requests.get(f"{BASE_URL}/api/workflows/{workflow_id}", headers=headers)
    print_response(response, "✅ Workflow Details")

    # Step 5: Execute Workflow
    print(f"\n▶️  Step 5: Execute Workflow {workflow_id}")
    response = requests.post(f"{BASE_URL}/api/workflows/{workflow_id}/execute", json={}, headers=headers)
    print_response(response, "✅ Workflow Executed" if response.status_code == 200 else "❌ Failed")

    execution_id = None
    if response.status_code == 200:
        execution_id = response.json()['id']
        print(f"\n✅ Execution ID: {execution_id}")

    # Step 6: List Executions
    print(f"\n📋 Step 6: List Executions for Workflow {workflow_id}")
    response = requests.get(f"{BASE_URL}/api/workflows/{workflow_id}/executions", headers=headers)
    print_response(response, "✅ Executions List")

    # Step 7: Create More Complex Workflow
    print("\n📋 Step 7: Create Complex Workflow")
    complex_workflow = {
        "name": "Multi-Action Test Workflow",
        "trigger": {
            "type": "webhook",
            "config": {"url": "https://example.com/webhook"}
        },
        "actions": [
            {
                "type": "send_notification",
                "config": {
                    "message": "Starting workflow execution",
                    "level": "info"
                }
            },
            {
                "type": "call_webhook",
                "config": {
                    "url": "https://httpbin.org/post",
                    "payload": {"test": "data"}
                }
            },
            {
                "type": "send_notification",
                "config": {
                    "message": "Workflow completed",
                    "level": "info"
                }
            }
        ],
        "enabled": True
    }
    response = requests.post(f"{BASE_URL}/api/workflows", json=complex_workflow, headers=headers)
    print_response(response, "✅ Complex Workflow Created" if response.status_code == 200 else "❌ Failed")

    complex_workflow_id = None
    if response.status_code == 200:
        complex_workflow_id = response.json()['id']

    # Step 8: Execute Complex Workflow
    if complex_workflow_id:
        print(f"\n▶️  Step 8: Execute Complex Workflow {complex_workflow_id}")
        response = requests.post(f"{BASE_URL}/api/workflows/{complex_workflow_id}/execute", json={}, headers=headers)
        print_response(response, "✅ Complex Workflow Executed" if response.status_code == 200 else "❌ Failed")

    # Step 9: Update Workflow
    print(f"\n✏️  Step 9: Update Workflow {workflow_id}")
    update_data = {
        "name": "Updated Test Workflow",
        "enabled": False
    }
    response = requests.put(f"{BASE_URL}/api/workflows/{workflow_id}", json=update_data, headers=headers)
    print_response(response, "✅ Workflow Updated" if response.status_code == 200 else "❌ Failed")

    # Step 10: Try to Execute Disabled Workflow
    print(f"\n❌ Step 10: Try to Execute Disabled Workflow")
    response = requests.post(f"{BASE_URL}/api/workflows/{workflow_id}/execute", json={}, headers=headers)
    print_response(response, "✅ Correctly Rejected" if response.status_code == 400 else "⚠️ Unexpected")

    # Step 11: Delete Workflow
    print(f"\n🗑️  Step 11: Delete Workflow {workflow_id}")
    response = requests.delete(f"{BASE_URL}/api/workflows/{workflow_id}", headers=headers)
    print_response(response, "✅ Workflow Deleted" if response.status_code == 200 else "❌ Failed")

    # Step 12: Verify Deletion
    print(f"\n✅ Step 12: Verify Deletion")
    response = requests.get(f"{BASE_URL}/api/workflows/{workflow_id}", headers=headers)
    print_response(response, "✅ Not Found (Expected)" if response.status_code == 404 else "⚠️ Unexpected")

    # Step 13: Delete Complex Workflow
    if complex_workflow_id:
        print(f"\n🗑️  Step 13: Delete Complex Workflow {complex_workflow_id}")
        response = requests.delete(f"{BASE_URL}/api/workflows/{complex_workflow_id}", headers=headers)
        print_response(response, "✅ Workflow Deleted" if response.status_code == 200 else "❌ Failed")

    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED!")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
