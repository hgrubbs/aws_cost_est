#!/bin/env python3
import argparse
import json
import sys

# Dictionary to associate cost-per-gb with volume types
volume_costs = {
    'io1': 0.00,
    'gp2': 0.10,
    'standard': 0.05,
}

# Dictionary to associate hourly cost with each instance type
instance_costs = {
}


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
        this_volume['VolumeId'] = v.get('VolumeId')
        this_volume['VolumeType'] = v.get('VolumeType')
        this_volume['Iops'] = v.get('Iops')
        this_volume['Size'] = v.get('Size')
        parsed_volumes.append(this_volume)
    return parsed_volumes


def associate_volumes_instances(volumes, instances):
    """Return a dict of instances and their associated volumes."""
    for i in instances:
        for v in volumes:
            if v['InstanceId'] == i['InstanceId']:
                i['Volumes'].append(v)
    return instances


def sum_volume_usage(instances):
    """Sum volume's Size within the instance dict, grouped by VolumeType. Returns dictionary of instances."""
    for i in instances:
        i['VolumeUsage'] = {'gp2': 0, 'standard': 0, 'io1': 0}
        for v in i['Volumes']:
            i['VolumeUsage'][v['VolumeType']] += v['Size']
    return instances


def write_csv(instances, filename):
    """Writes a CSV containing instance/volume data, with associated costs."""
    try:
        f = open(filename, 'w')
        line = 'Platform,AMI,InstanceId,Name,Type,standard-GB,standard-cost,ssd-GB,ssd-cost,piops-GB,piops-cost,\n'
        f.write(line)
        for i in instances:
            standard_cost = int(i['VolumeUsage']['standard'] * volume_costs['standard'])
            ssd_cost = int(i['VolumeUsage']['gp2'] * volume_costs['gp2'])
            piops_cost = int(i['VolumeUsage']['io1'] * volume_costs['io1'])
            line = "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\n" % (
                i['Platform'],
                i['AMI'],
                i['InstanceId'],
                i['Name'],
                i['InstanceType'],
                i['VolumeUsage']['standard'],
                standard_cost,
                i['VolumeUsage']['gp2'],
                ssd_cost,
                i['VolumeUsage']['io1'],
                piops_cost,
            )
            f.write(line)
        f.close()
    except Exception as e:
        print("Failed to write output file: %s" % e)
        sys.exit(1)


def main(args):
    (vol_json, inst_json) = load_jsons(args)
    instances = collect_instances(inst_json)
    volumes = collect_volumes(vol_json)
    instances = associate_volumes_instances(volumes, instances)
    instances = sum_volume_usage(instances)
    write_csv(instances, args.out)
    print("Wrote %s" % args.out)
    return True


if __name__ == '__main__':
    description = "This program associates AWSCLI output for volumes attached to instances."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--instances', type=str, help='instances json', required=True)
    parser.add_argument('--volumes', type=str, help='volumes json', required=True)
    parser.add_argument('--out', type=str, help='filename to write CSV', required=True)
    args = parser.parse_args()
    main(args)
