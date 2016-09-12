#!/bin/env python3
import argparse
import json
import sys
import datetime


def load_jsons(args):
    """Open volumes/instances json files, then parse them and return both."""
    try:
        f = open(args.volumes, 'r')
        volumes_json = json.load(f)
        f.close()
    except Exception as e:
        print("Could not load/parse volumes JSON: %s" % e)
        sys.exit(1)
    try:
        f = open(args.instances, 'r')
        instances_json = json.load(f)
        f.close()
    except Exception as e:
        print("Could not load/parse instances JSON: %s" % e)
        sys.exit(1)
    return (volumes_json, instances_json)


def collect_instances(instances):
    """Return stripped down and slightly modified dictionary of instances."""
    parsed_instances = list()
    instances = [r['Instances'][0] for r in instances['Reservations']]
    for i in instances:
        this_instance = {}
        this_instance['InstanceId'] = i['InstanceId']
        this_instance['InstanceType'] = i['InstanceType']
        this_instance['Platform'] = i.get('Platform', 'non-windows')
        this_instance['AMI'] = i['ImageId']
        this_instance['Volumes'] = list()
        for t in i['Tags']:
            if t['Key'] != 'Name':
                continue
            else:
                this_instance['Name'] = t['Value']
                break
        parsed_instances.append(this_instance)
    return parsed_instances


def collect_volumes(volumes):
    """Return stripped down and slightly modified dictionary of volumes."""
    parsed_volumes = list()
    volumes = volumes['Volumes']
    for v in volumes:
        if (v['State'] != 'in-use') or (len(v['Attachments']) < 1):
            print("Skipping non in-use volume: %s" % v['VolumeId'])
            continue
        this_volume = {}
        this_volume['InstanceId'] = v['Attachments'][0]['InstanceId']
        this_volume['Device'] = v['Attachments'][0]['Device']
        this_volume['VolumeId'] = v.get('VolumeId')
        this_volume['VolumeType'] = v.get('VolumeType')
        this_volume['Iops'] = v.get('Iops')
        this_volume['Size'] = v.get('Size')
        for tags in v.get('Tags', []):
            if tags['Key'] == 'Name':
                this_volume['Name'] = tags['Value']
                break
        parsed_volumes.append(this_volume)
    return parsed_volumes


def associate_volumes_instances(volumes, instances):
    """Return a dict of instances and their associated volumes."""
    for i in instances:
        for v in volumes:
            if v['InstanceId'] == i['InstanceId']:
                v['IsBackup'] = True
                i['Volumes'].append(v)
    return instances


def gen_aws_cli_shellcode(instances, args):
    """Write shellcode to generate volume snapshots with usable descriptions."""
    now = str(datetime.datetime.now())
    if args.fast is False:
        background = ''
    elif args.fast is True:
        background = '&'

    shellcode = "#!/bin/sh\n"
    for i in instances:
        shellcode += "# instance: %s\n" % i['InstanceId']
        for v in i['Volumes']:
            v['timestamp'] = now
            shellcode += "echo 'instance: %s' - 'volume %s'\n" % (i['InstanceId'], v['VolumeId'])
            shellcode += "aws ec2 create-snapshot --volume-id=%s --description='%s' --output=json %s\n\n" % (v['VolumeId'], json.dumps(v), background)
    try:
        f = open(args.out, 'w')
        f.write(shellcode)
        f.close()
    except Exception as e:
        print("Error writing output file: %s" % e)
        sys.exit(1)


def main(args):
    (vol_json, inst_json) = load_jsons(args)
    instances = collect_instances(inst_json)
    volumes = collect_volumes(vol_json)
    instances = associate_volumes_instances(volumes, instances)
    gen_aws_cli_shellcode(instances, args)
    return True


if __name__ == '__main__':
    description = "This program snapshots attached volumes."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--instances', type=str, help='instances json', required=True)
    parser.add_argument('--volumes', type=str, help='volumes json', required=True)
    parser.add_argument('--fast', action="store_const", const=True, default=False, help='shellcode will spawn backups in background', required=False)
    parser.add_argument('--out', type=str, help='aws cli shellcode file', required=True)
    args = parser.parse_args()
    main(args)
