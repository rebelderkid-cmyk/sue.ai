#!/bin/bash
pkill -f kg_pipeline.py
rm -f kg_failed_log.txt
nohup python3 -u kg_pipeline.py > kg_pipeline.log 2>&1 &
echo "✅ Pipeline Started with PID $!"
