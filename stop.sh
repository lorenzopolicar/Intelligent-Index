#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Check if app.pid exists
if [[ ! -f app.pid ]]; then
    echo "No PID file found. Is the app running?"
    exit 1
fi

# Kill the process
PID=$(cat app.pid)
if kill -9 "$PID" 2>/dev/null; then
    echo "App stopped (PID: $PID)"
    rm -f app.pid  # Remove the PID file
else
    echo "Failed to stop the app (Process may not exist)."
fi
