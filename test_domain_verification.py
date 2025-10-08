#!/usr/bin/env python
"""
Test script to demonstrate the Büfé domain verification functionality.
This script tests the domain access control with different email domains.
"""

import os
import sys
import django

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nodews_project.settings')
django.setup()

from django.contrib.auth.models import User
from bufe.utils import is_email_domain_allowed, check_domain_access, get_user_domain


def test_domain_verification():
    """Test the domain verification functionality"""
    print("🧪 Testing Büfé Domain Verification System")
    print("=" * 50)
    
    # Test cases
    test_emails = [
        ("test@szlgbp.hu", True, "Valid school domain"),
        ("developer@botond.eu", True, "Valid testing domain"),
        ("user@gmail.com", False, "Invalid external domain"),
        ("student@szlg.hu", False, "Similar but invalid domain"),
        ("", False, "Empty email"),
        ("invalid-email", False, "Invalid email format"),
        ("test@SZLGBP.HU", True, "Valid domain (case insensitive)"),
        ("admin@BOTOND.EU", True, "Valid testing domain (case insensitive)")
    ]
    
    print("\n📧 Email Domain Tests:")
    print("-" * 30)
    
    for email, expected, description in test_emails:
        result = is_email_domain_allowed(email)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | {email:<20} | {description}")
    
    # Test with actual user objects (if any exist)
    print("\n👤 User Access Tests:")
    print("-" * 30)
    
    # Check if there are any users in the database
    users = User.objects.all()[:5]  # Get first 5 users
    
    if users:
        for user in users:
            has_access, reason = check_domain_access(user)
            domain = get_user_domain(user)
            status = "✅ ALLOWED" if has_access else "❌ DENIED"
            print(f"{status} | {user.email:<25} | @{domain:<15} | {reason}")
    else:
        print("📝 No users found in database. Register some users to test!")
    
    print("\n🔧 Domain Configuration:")
    print("-" * 30)
    print("✅ Allowed domains:")
    print("   • @szlgbp.hu (Kőbányai Szent László Gimnázium)")
    print("   • @botond.eu (Testing domain)")
    
    print("\n📋 Access Requirements:")
    print("-" * 30)
    print("1. User must be authenticated")
    print("2. User must be active (email verified)")
    print("3. User's email domain must be in allowed list")
    
    print("\n🌐 Test URLs:")
    print("-" * 30)
    print("• Web interface: http://127.0.0.1:8000/bufe/")
    print("• API check: http://127.0.0.1:8000/bufe/api/check-access/")
    
    print("\n✨ Domain verification system is ready!")


if __name__ == "__main__":
    test_domain_verification()