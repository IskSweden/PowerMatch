#!/bin/bash

cd ~/Documents/PowerMatch
source powermatch-venv/bin/activate
powermatch &
POWERMATCH_PID=$!

sleep 10

URL="localhost:8000"

DISPLAY=:0 chromium-browser --kiosk --incognito --no-first-run --disable-infobars "$URL" &
CHROMIUM_PID=$!

echo "Chromium launched with PID: $CHROMIUM_PID. Press Ctrl+P to close."

while kill -0 $CHROMIUM_PID >/dev/null 2>&1; do
  # Check if Ctrl+P is pressed using xdotool
  if xdotool search --onlyvisible --class chromium key --clearmodifiers --window %1 Ctrl+p; then
    break
  fi
  sleep 1
done

echo "Closing Chromium (PID: $CHROMIUM_PID) and powermatch (PID: $POWERMATCH_PID)..."
kill $CHROMIUM_PID
kill $POWERMATCH_PID

echo "All processes closed."
