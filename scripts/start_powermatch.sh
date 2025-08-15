#!/bin/bash

openchrome() {
  xset s noblank
  xset s off

  xscreensaver &

  unclutter -idle 1 -root &

  # Let Chromium think it always exited cleanly.
  sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' '~/.config/chromium/Default/Preferences'
  sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' '~/.config/chromium/Default/Preferences'

  # Start Chromium.
  chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:8000
}

cd ~/Documents/PowerMatch
source powermatch-venv/bin/activate

powermatch &
openchrome
