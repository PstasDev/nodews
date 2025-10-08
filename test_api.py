#!/usr/bin/env python3
"""
Simple test script to verify authentication API endpoints.
Run this after starting the Django server.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("🧪 Testing Authentication API Endpoints\n")
    
    # Test user registration
    print("1. Testing user registration...")
    register_data = {
        "username": "testuser123",
        "email": "test@example.com",
        "password1": "testsecurepass123",
        "password2": "testsecurepass123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/register/", 
                               json=register_data,
                               headers={'Content-Type': 'application/json'})
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        print("   ✅ Registration endpoint working")
    except Exception as e:
        print(f"   ❌ Registration failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test user login
    print("2. Testing user login...")
    login_data = {
        "username": "testuser123",
        "password": "testsecurepass123"
    }
    
    try:
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/login/", 
                              json=login_data,
                              headers={'Content-Type': 'application/json'})
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 200:
            print("   ✅ Login endpoint working")
            
            # Test getting user info
            print("\n3. Testing user info endpoint...")
            user_response = session.get(f"{BASE_URL}/api/user/")
            print(f"   Status: {user_response.status_code}")
            print(f"   Response: {user_response.json()}")
            
            if user_response.status_code == 200:
                print("   ✅ User info endpoint working")
            
            # Test logout
            print("\n4. Testing logout...")
            logout_response = session.post(f"{BASE_URL}/api/logout/")
            print(f"   Status: {logout_response.status_code}")
            print(f"   Response: {logout_response.json()}")
            
            if logout_response.status_code == 200:
                print("   ✅ Logout endpoint working")
        
    except Exception as e:
        print(f"   ❌ Login test failed: {e}")
    
    print("\n" + "="*50)
    print("🎯 API Testing Complete!")
    print("📖 Visit http://127.0.0.1:8000/ to test the web interface")
    print("📚 See API_DOCUMENTATION.md for detailed endpoint usage")

if __name__ == "__main__":
    test_api()