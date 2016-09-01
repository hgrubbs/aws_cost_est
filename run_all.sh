#!/bin/bash

echo "get_jsons.sh"
./get_jsons.sh

echo "aws_snapshot_instance_volumes.py"
python3 aws_snapshot_instance_volumes.py \
    --instances instances.json \
    --volumes volumes.json \
    --out backup.sh \
    --fast

echo "aws_purge_snapshots.py"
python3 aws_purge_snapshots.py \
    --snapshots snapshots.json \
    --days 3 \
    --out purge.sh \
    --fast

echo "backup.sh"
chmod +x backup.sh
./backup.sh

echo "purge.sh"
chmod +x purge.sh
./purge.sh
