from django.core.management import call_command
from django.contrib.auth.models import User

def init_demo_data():
    # Create demo user if it doesn't exist
    if not User.objects.filter(username='demo').exists():
        User.objects.create_user('demo', password='demo123')
    
    # Load the fixture data
    call_command('loaddata', 'demo_data.json')
