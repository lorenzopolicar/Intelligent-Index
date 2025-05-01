source .venv/bin/activate || { echo "Failed to activate venv"; exit 1; }

nohup python src/app.py > app.log 2>&1 &

# Get the process ID and save it to a file
echo $! > app.pid

echo "App started in the background with PID: $(cat app.pid)"
echo "Logs: tail -f app.log"

