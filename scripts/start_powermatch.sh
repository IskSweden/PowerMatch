#!/bin/bash

openchrome() {

  # Define the URL to open in kiosk mode
  URL="http://localhost:8000"

  # Launch Chromium in kiosk mode in the background
  # The ' & ' at the end runs the command asynchronously
  chromium-browser --kiosk --incognito --no-first-run --disable-infobars "$URL" &

  # Store the Process ID (PID) of the last background command
  CHROMIUM_PID=$!

  echo "Chromium launched with PID: $CHROMIUM_PID. Press Ctrl+P to close."

  # Wait for Ctrl+P key press
  xdotool search --onlyvisible --class chromium windowfocus key --clearmodifiers --window %1 Ctrl+p

  # Kill the Chromium process when Ctrl+P is detected
  kill $CHROMIUM_PID

  echo "Chromium closed."

}

cd ~/Documents/PowerMatch
source powermatch-venv/bin/activate

powermatch &
openchrome
