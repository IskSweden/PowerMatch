#!/bin/bash

# Move to project root
cd "$HOME/Code/Python/PowerMatch" || exit

echo
echo "Starting FastAPI game server..."

# Activate the virtual environment and start the server
"$HOME/Code/Python/PowerMatch/venv/bin/python3" -m uvicorn powermatch.app:create_app --reload --factory

# Pause equivalent
read -rp "Press Enter to continue..."

