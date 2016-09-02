#!/bin/bash

echo "aws_purge_snapshots.py"
python3 aws_purge_snapshots.py \
    --snapshots snapshots.json \
    --days 3 \
    --out purge.sh \

echo "purge.sh"
chmod +x purge.sh
./purge.sh
