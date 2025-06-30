#!/usr/bin/env python3
"""
Simple test script to verify Swayami API setup
Run this after starting the server with: python main.py
"""

import requests
import json
import base64

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_auth():
    """Test authentication"""
    print("🔐 Testing authentication...")
    
    # Test auth info
    response = requests.get(f"{API_BASE}/api/auth/test")
    print(f"Auth Test: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # Test login
    login_data = {
        "email": "contact.pavansb@gmail.com",
        "password": "test123"
    }
    response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
    print(f"Login: {response.status_code}")
    if response.status_code == 200:
        auth_response = response.json()
        print(f"Login successful! Token: {auth_response['access_token'][:20]}...")
        return auth_response['access_token']
    else:
        print(f"Login failed: {response.text}")
        return None

def test_goals_with_auth(token):
    """Test goals endpoint with authentication"""
    print("🎯 Testing goals with authentication...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a goal
    goal_data = {
        "title": "Learn FastAPI",
        "description": "Master FastAPI for backend development",
        "category": "programming",
        "priority": "high"
    }
    
    response = requests.post(f"{API_BASE}/api/goals", json=goal_data, headers=headers)
    print(f"Create Goal: {response.status_code}")
    if response.status_code == 200:
        goal = response.json()
        print(f"Goal created: {goal['title']}")
        
        # Get goals
        response = requests.get(f"{API_BASE}/api/goals", headers=headers)
        print(f"Get Goals: {response.status_code}")
        goals = response.json()
        print(f"Total goals: {len(goals)}")
        
        return goal['id'] if goals else None
    else:
        print(f"Create goal failed: {response.text}")
        return None

def test_basic_auth():
    """Test basic authentication"""
    print("🔑 Testing basic authentication...")
    
    # Create basic auth header
    credentials = "contact.pavansb@gmail.com:test123"
    b64_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {b64_credentials}"}
    
    response = requests.get(f"{API_BASE}/api/auth/status", headers=headers)
    print(f"Basic Auth Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Basic auth failed: {response.text}")

def main():
    print("🚀 Starting Swayami API Tests\n")
    
    try:
        # Test health
        test_health()
        
        # Test authentication
        token = test_auth()
        
        if token:
            # Test goals with Bearer token
            goal_id = test_goals_with_auth(token)
            
        # Test basic auth
        test_basic_auth()
        
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   cd backend && python main.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main() 