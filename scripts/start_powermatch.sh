#!/bin/bash
cd ~/Documents/PowerMatch
source powermatch-venv/bin/activate

./powermatch

sleep 10
chromium-browser --kiosk localhost:8000
