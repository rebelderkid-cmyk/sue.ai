#!/bin/bash

LOG_FILE="/home/rinne/night_shift.log"

echo "🌙 Night Shift Started at $(date)" > $LOG_FILE

# 1. Wait for Easy Indexer to finish
echo "⏳ Waiting for Easy Indexer to finish..." >> $LOG_FILE
while pgrep -f "easy_indexer.py" > /dev/null; do
    echo "   Indexer still running... sleeping 60s" >> $LOG_FILE
    sleep 60
done
echo "✅ Indexer Finished!" >> $LOG_FILE

# 2. Install Typhoon Dependencies
echo "🛠️ Installing Typhoon Dependencies..." >> $LOG_FILE
pip install torch transformers pillow accelerate sentencepiece protobuf >> $LOG_FILE 2>&1

# 3. Download & Run Typhoon
echo "🌪️ Starting Typhoon OCR Engine..." >> $LOG_FILE
# Note: This might likely crash on CPU if RAM < 32GB for 7B model. 
# We assume the machine has enough RAM.
python3 /home/rinne/run_typhoon.py >> /home/rinne/typhoon_runner.log 2>&1

echo "☀️ Night Shift Complete at $(date)" >> $LOG_FILE
