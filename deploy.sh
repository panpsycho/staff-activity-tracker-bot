#!/bin/bash 
icd /home/opc/staff-activity-tracker-bot 
git pull 
source .venv/bin/activate 
pip install -r requirements.txt 
sudo systemctl restart discordbot 
echo "Deployed and restarted."
