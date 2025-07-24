#!/bin/bash

# Sync system clock
sudo chronyc -a burst 4/4
sudo chronyc -a makestep

# Run the Python client with config.ini
python3 server.py --config config.ini