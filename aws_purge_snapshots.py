#!/bin/env python3
from dateutil import parser as date_parser
import datetime
import argparse
import json
import sys
import pdb


def load_jsons(args):
    """Open volumes/instances json files, then parse them and return both."""
    try:
        f = open(args.snapshots, 'r')
        snapshots_json = json.load(f)
        f.close()
    except Exception as e:
        print("Could not load/parse snapshots JSON: %s" % e)
        sys.exit(1)
    return snapshots_json


def gen_aws_cli_shellcode(snapshots, args):
    """Write shellcode to delete snapshots."""
    if args.fast is False:
        background = ''
    elif args.fast is True:
        background = '&'

    shellcode = "#!/bin/sh\n"
    for s in snapshots:
        shellcode += "echo 'deleting snapshot: %s'\n" % (s)
        shellcode += "aws ec2 delete-snapshot --snapshot-id=%s\n\n" % (s)
    try:
        f = open(args.out, 'w')
        f.write(shellcode)
        f.close()
    except Exception as e:
        print("Error writing output file: %s" % e)
        sys.exit(1)


def get_expired_snapshots(args, snapshots):
    """Returns list containing snapshot-id's that are expired."""
    day_s = 86400
    expired_snapshots = []
    now = datetime.datetime.now()
    for snapshot in snapshots['Snapshots']:
        desc = json.loads(snapshot['Description'])
        snapshot_date = date_parser.parse(desc['timestamp'])
        diff = now - snapshot_date
        if diff.total_seconds() > (args.days * day_s):
            expired_snapshots.append(snapshot['SnapshotId'])
    return expired_snapshots


def main(args):
    snapshots = load_jsons(args)
    expired_snapshots = get_expired_snapshots(args, snapshots)
    pdb.set_trace()
    gen_aws_cli_shellcode(expired_snapshots, args)
    return True


if __name__ == '__main__':
    description = "This program deletes old snapshot backups."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--snapshots', type=str, help='snapshots json', required=True)
    parser.add_argument('--days', type=int, help='retention in days', required=True)
    parser.add_argument('--fast', action="store_const", const=True, default=False, help='shellcode will spawn jobs in background', required=False)
    parser.add_argument('--out', type=str, help='aws cli shellcode file', required=True)
    args = parser.parse_args()
    main(args)
