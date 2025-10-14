"""
Quick setup script for Büfé Admin interface.
Run this after migrations to set up initial data.
"""

from django.contrib.auth.models import User
from bufe.models import Bufe, OpeningHours
from datetime import time

def setup_bufe_admin():
    """
    Setup the Büfé admin interface with initial data.
    """
    print("Setting up Büfé Admin interface...")
    
    # 1. Create or get Bufe instance
    bufe, created = Bufe.objects.get_or_create(
        id=1,
        defaults={'nev': 'Iskolai Büfé'}
    )
    
    if created:
        print("✓ Created Büfé instance")
        
        # Create default opening hours
        default_hours = [
            (0, time(7, 30), time(15, 30)),   # Hétfő
            (1, time(7, 30), time(15, 30)),   # Kedd
            (2, time(7, 30), time(15, 30)),   # Szerda
            (3, time(7, 30), time(15, 30)),   # Csütörtök
            (4, time(7, 30), time(14, 0)),    # Péntek
        ]
        
        for weekday, from_hour, to_hour in default_hours:
            OpeningHours.objects.create(
                bufe=bufe,
                weekday=weekday,
                from_hour=from_hour,
                to_hour=to_hour
            )
        
        print("✓ Created default opening hours (Mon-Fri)")
    else:
        print("✓ Büfé instance already exists")
    
    # 2. List current bufeadmin users
    current_admins = bufe.bufeadmin.all()
    if current_admins.exists():
        print(f"\nCurrent bufeadmin users ({current_admins.count()}):")
        for admin in current_admins:
            print(f"  - {admin.username} ({admin.email})")
    else:
        print("\n⚠ No bufeadmin users assigned yet!")
        print("\nTo add a bufeadmin user, run:")
        print("  python manage.py shell")
        print("  >>> from bufe.models import Bufe")
        print("  >>> from django.contrib.auth.models import User")
        print("  >>> bufe = Bufe.objects.first()")
        print("  >>> user = User.objects.get(username='YOUR_USERNAME')")
        print("  >>> bufe.bufeadmin.add(user)")
        print("  >>> bufe.save()")
        
    # 3. Show access URLs
    print("\n" + "="*60)
    print("Büfé Admin Interface URLs:")
    print("="*60)
    print("  Dashboard:      http://localhost:8000/bufe/admin/")
    print("  Menu:           http://localhost:8000/bufe/admin/menu/")
    print("  Opening Hours:  http://localhost:8000/bufe/admin/opening-hours/")
    print("  WebSocket:      ws://localhost:8000/ws/bufe/orders/")
    print("="*60)
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("  1. Add bufeadmin users (see instructions above)")
    print("  2. Start Redis: redis-server")
    print("  3. Run server: python manage.py runserver")
    print("  4. Visit: http://localhost:8000/bufe/admin/")
    

if __name__ == '__main__':
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nodews_project.settings')
    django.setup()
    
    setup_bufe_admin()
