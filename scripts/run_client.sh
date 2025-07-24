#!/bin/bash

# Sync system clock
sudo chronyc -a burst 4/4
sudo chronyc -a makestep

# Run the Python client with config.ini
python3 client.py --config config.ini

# Create time_logs directory if it doesn't exist
mkdir -p time_logs

# Log chronyc 
chronyc tracking > time_logs/chronyc_tracking_$(date +%Y%m%d_%H%M%S).log