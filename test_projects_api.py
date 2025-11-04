#!/usr/bin/env python3
"""
Test script for Projects API endpoints
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
    # Step 1: Register or login
    print("\n🔐 Step 1: Authentication")

    # Try to register a new user
    register_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }

    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    if response.status_code == 200:
        print_response(response, "✅ Registration successful")
        token_data = response.json()
    else:
        # If registration fails (user exists), try login
        print("ℹ️  User exists, trying login...")
        response = requests.post(f"{BASE_URL}/api/auth/login", json=register_data)
        if response.status_code == 200:
            print_response(response, "✅ Login successful")
            token_data = response.json()
        else:
            print_response(response, "❌ Authentication failed")
            return

    token = token_data['token']
    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Create a project
    print("\n📦 Step 2: Create Project")
    project_data = {
        "name": "Test Project",
        "description": "A test project for API testing"
    }

    response = requests.post(f"{BASE_URL}/api/projects", json=project_data, headers=headers)
    print_response(response, "✅ Project Created" if response.status_code == 200 else "❌ Failed")

    if response.status_code != 200:
        return

    project_id = response.json()['id']
    print(f"\n✅ Project ID: {project_id}")

    # Step 3: List all projects
    print("\n📋 Step 3: List All Projects")
    response = requests.get(f"{BASE_URL}/api/projects", headers=headers)
    print_response(response, "✅ Projects List")

    # Step 4: Get specific project
    print(f"\n🔍 Step 4: Get Project {project_id}")
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=headers)
    print_response(response, "✅ Project Details")

    # Step 5: Update project
    print(f"\n✏️  Step 5: Update Project {project_id}")
    update_data = {
        "name": "Updated Test Project",
        "description": "Updated description"
    }
    response = requests.put(f"{BASE_URL}/api/projects/{project_id}", json=update_data, headers=headers)
    print_response(response, "✅ Project Updated" if response.status_code == 200 else "❌ Update Failed")

    # Step 6: Delete project
    print(f"\n🗑️  Step 6: Delete Project {project_id}")
    response = requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=headers)
    print_response(response, "✅ Project Deleted" if response.status_code == 200 else "❌ Delete Failed")

    # Step 7: Verify deletion
    print(f"\n✅ Step 7: Verify Deletion")
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=headers)
    print_response(response, "✅ Project Not Found (Expected)" if response.status_code == 404 else "⚠️ Unexpected")

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
