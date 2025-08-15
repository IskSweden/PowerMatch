#!/bin/bash

echo "Removing old instance"
cd ~/Documents
rm -rf Powermatch/

echo "Pulling newest target_new branch from github"
cd ~/Documents
git clone -b target_new --single-branch https://github.com/IskSweden/PowerMatch.git
echo "cloned target_new branch"

cd ~/Documents/PowerMatch
python3 -m venv powermatch-venv
sleep 5
source powermatch-venv/bin/activate
sleep 5

pip install --upgrade pip
pip install .
