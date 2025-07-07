#!/bin/bash

# Number of repetitions
REPEAT=48

# After experiment is run, sleep for 60 minutes
SLEEP_FOR_MINUTES=60

for ((i=1; i<=REPEAT; i++))
do
    echo "Run $i of $REPEAT at $(date)"
    ./run_client.sh
    if [ $i -lt $REPEAT ]; then
        sleep SLEEP_FOR_MINUTES * 60 
    fi
done