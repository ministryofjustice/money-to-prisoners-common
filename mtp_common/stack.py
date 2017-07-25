import boto.cloudformation
import boto.ec2
import boto.ec2.autoscale
from boto.utils import get_instance_identity


class StackInterrogationException(Exception):
    pass


class InstanceNotInAsgException(Exception):
    pass


def is_first_instance():
    '''
    Returns True if the current instance is the first instance in the ASG group,
    sorted by instance_id.
    '''
    try:
        instance_identity = get_instance_identity()
        instance_id = instance_identity['document']['instanceId']
        instance_region = instance_identity['document']['availabilityZone'].strip()[:-1]
        conn = boto.ec2.connect_to_region(instance_region)
        instance_data = conn.get_all_instances(
            instance_ids=[instance_id]
        )[0].instances[0]

        # my autoscaling group
        asg_group = instance_data.tags['aws:autoscaling:groupName']

        autoscale = boto.ec2.autoscale.connect_to_region(instance_region)
        group = autoscale.get_all_groups(names=[asg_group])[0]
        sorted_instance_ids = sorted(
            [instance.instance_id for instance in group.instances]
        )
    except boto.exception.AWSConnectionError as e:
        raise StackInterrogationException(e)

    if instance_id not in sorted_instance_ids:
        raise InstanceNotInAsgException()

    return sorted_instance_ids[0] == instance_id
