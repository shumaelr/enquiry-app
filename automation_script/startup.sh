#!/bin/bash
# Azure App Service startup script

# Create data directory for uploads
mkdir -p /home/data/BOQ /home/data/Sizing /home/data/SLD

# Set environment variable for watch directory
export WATCH_DIRECTORY=/home/data

# Start the web server
python web_viewer.py
