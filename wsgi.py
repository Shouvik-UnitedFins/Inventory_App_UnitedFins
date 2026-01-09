import os
import sys
from pathlib import Path

# Add the project directory to the sys.path
path = Path(__file__).resolve().parent
sys.path.append(str(path))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'python_server.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application

# Get the WSGI application
application = get_wsgi_application()