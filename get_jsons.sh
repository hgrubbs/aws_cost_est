#!/bin/bash

echo "getting instances"
aws ec2 describe-instances --output json > instances.json

echo "getting volumes"
aws ec2 describe-volumes --output json > volumes.json

echo "getting snapshots"
aws ec2 describe-snapshots --filter Name="description",Values="*dc3-srv*" --output json > snapshots.json
