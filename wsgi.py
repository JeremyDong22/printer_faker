#!/usr/bin/env python3
"""
WSGI entry point for Printer API Service v2
This file is used by gunicorn to start the application
"""

from printer_api_service_v2 import app

# Export the Flask app for gunicorn
# Services (TCP server, etc.) are started via gunicorn's when_ready hook
application = app