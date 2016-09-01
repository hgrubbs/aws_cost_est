#!/bin/bash

echo "aws_snapshot_instance_volumes.py"
python3 aws_snapshot_instance_volumes.py \
    --instances instances.json \
    --volumes volumes.json \
    --out backup.sh \
    --fast

echo "backup.sh"
chmod +x backup.sh
./backup.sh
