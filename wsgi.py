import sys
import os

# Add the project directory to sys.path so PythonAnywhere can resolve imports
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from a2wsgi import ASGIMiddleware
from main import app

# Expose WSGI application callable for PythonAnywhere web server
application = ASGIMiddleware(app)
