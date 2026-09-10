#!/usr/bin/env python
"""
Flask app launcher that configures template_folder and static_folder
to serve from the repository root, then imports and runs the app.
"""
import os
import sys

# Set Flask template and static folders to the app's directory before importing app
os.environ['FLASK_TEMPLATE_FOLDER'] = os.path.dirname(os.path.abspath(__file__))
os.environ['FLASK_STATIC_FOLDER'] = os.path.dirname(os.path.abspath(__file__))

# Now import app
import app as app_module

# Configure Flask paths
app_module.app.template_folder = '.'
app_module.app.static_folder = '.'

# Initialize database
app_module.init_db()

# Get port from environment (Railway sets PORT)
port = int(os.environ.get('PORT', '5000'))

# Run the app
app_module.app.run(host='0.0.0.0', port=port, debug=False)
