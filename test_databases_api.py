#!/usr/bin/env python3
"""
Test script for Databases and Records API endpoints
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

    # Step 2: Create Project
    print("\n📦 Step 2: Create Project")
    project_data = {
        "name": "Test Database Project",
        "description": "Project for testing databases"
    }
    response = requests.post(f"{BASE_URL}/api/projects", json=project_data, headers=headers)
    print_response(response, "✅ Project Created" if response.status_code == 200 else "❌ Failed")

    if response.status_code != 200:
        return

    project_id = response.json()['id']
    print(f"\n✅ Project ID: {project_id}")

    # Step 3: Create Database with Schema
    print("\n🗄️  Step 3: Create Database")
    database_data = {
        "project_id": project_id,
        "name": "Contacts",
        "schema": {
            "columns": [
                {"name": "name", "type": "text", "required": True},
                {"name": "email", "type": "text", "required": True},
                {"name": "age", "type": "number", "required": False},
                {"name": "active", "type": "boolean", "required": False},
                {"name": "joined_date", "type": "date", "required": False},
                {"name": "status", "type": "select", "required": True, "options": ["active", "inactive", "pending"]}
            ]
        }
    }
    response = requests.post(f"{BASE_URL}/api/databases", json=database_data, headers=headers)
    print_response(response, "✅ Database Created" if response.status_code == 200 else "❌ Failed")

    if response.status_code != 200:
        return

    database_id = response.json()['id']
    print(f"\n✅ Database ID: {database_id}")

    # Step 4: List Databases
    print(f"\n📋 Step 4: List Databases for Project {project_id}")
    response = requests.get(f"{BASE_URL}/api/databases?project_id={project_id}", headers=headers)
    print_response(response, "✅ Databases List")

    # Step 5: Create Record
    print(f"\n➕ Step 5: Create Record in Database {database_id}")
    record_data = {
        "data": {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "active": True,
            "joined_date": "2025-01-15",
            "status": "active"
        }
    }
    response = requests.post(f"{BASE_URL}/api/databases/{database_id}/records", json=record_data, headers=headers)
    print_response(response, "✅ Record Created" if response.status_code == 200 else "❌ Failed")

    if response.status_code != 200:
        return

    record_id = response.json()['id']
    print(f"\n✅ Record ID: {record_id}")

    # Step 6: Create Another Record
    print(f"\n➕ Step 6: Create Another Record")
    record_data2 = {
        "data": {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "status": "pending"
        }
    }
    response = requests.post(f"{BASE_URL}/api/databases/{database_id}/records", json=record_data2, headers=headers)
    print_response(response, "✅ Record Created" if response.status_code == 200 else "❌ Failed")

    record_id2 = response.json()['id'] if response.status_code == 200 else None

    # Step 7: List Records
    print(f"\n📋 Step 7: List All Records")
    response = requests.get(f"{BASE_URL}/api/databases/{database_id}/records", headers=headers)
    print_response(response, "✅ Records List")

    # Step 8: Get Specific Record
    print(f"\n🔍 Step 8: Get Record {record_id}")
    response = requests.get(f"{BASE_URL}/api/databases/{database_id}/records/{record_id}", headers=headers)
    print_response(response, "✅ Record Details")

    # Step 9: Update Record
    print(f"\n✏️  Step 9: Update Record {record_id}")
    update_data = {
        "data": {
            "name": "John Updated",
            "email": "john.updated@example.com",
            "age": 31,
            "active": False,
            "joined_date": "2025-01-15",
            "status": "inactive"
        }
    }
    response = requests.put(f"{BASE_URL}/api/databases/{database_id}/records/{record_id}", json=update_data, headers=headers)
    print_response(response, "✅ Record Updated" if response.status_code == 200 else "❌ Failed")

    # Step 10: Test Validation - Invalid Type
    print(f"\n❌ Step 10: Test Validation (Invalid Type)")
    invalid_data = {
        "data": {
            "name": "Test",
            "email": "test@example.com",
            "age": "not a number",  # Should fail
            "status": "active"
        }
    }
    response = requests.post(f"{BASE_URL}/api/databases/{database_id}/records", json=invalid_data, headers=headers)
    print_response(response, "✅ Validation Caught" if response.status_code == 400 else "⚠️ Unexpected")

    # Step 11: Test Validation - Missing Required Field
    print(f"\n❌ Step 11: Test Validation (Missing Required)")
    invalid_data2 = {
        "data": {
            "name": "Test"
            # Missing required 'email' and 'status'
        }
    }
    response = requests.post(f"{BASE_URL}/api/databases/{database_id}/records", json=invalid_data2, headers=headers)
    print_response(response, "✅ Validation Caught" if response.status_code == 400 else "⚠️ Unexpected")

    # Step 12: Test Validation - Invalid Select Option
    print(f"\n❌ Step 12: Test Validation (Invalid Select)")
    invalid_data3 = {
        "data": {
            "name": "Test",
            "email": "test@example.com",
            "status": "invalid_status"  # Not in options
        }
    }
    response = requests.post(f"{BASE_URL}/api/databases/{database_id}/records", json=invalid_data3, headers=headers)
    print_response(response, "✅ Validation Caught" if response.status_code == 400 else "⚠️ Unexpected")

    # Step 13: Delete Record
    print(f"\n🗑️  Step 13: Delete Record {record_id}")
    response = requests.delete(f"{BASE_URL}/api/databases/{database_id}/records/{record_id}", headers=headers)
    print_response(response, "✅ Record Deleted" if response.status_code == 200 else "❌ Failed")

    # Step 14: Delete Database
    print(f"\n🗑️  Step 14: Delete Database {database_id}")
    response = requests.delete(f"{BASE_URL}/api/databases/{database_id}", headers=headers)
    print_response(response, "✅ Database Deleted" if response.status_code == 200 else "❌ Failed")

    # Step 15: Delete Project
    print(f"\n🗑️  Step 15: Delete Project {project_id}")
    response = requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=headers)
    print_response(response, "✅ Project Deleted" if response.status_code == 200 else "❌ Failed")

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
