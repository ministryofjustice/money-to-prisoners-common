import unittest
from unittest import mock

import responses

from mtp_common.stack import InstanceNotInAsgException, StackInterrogationException, is_first_instance


class StackTestCase(unittest.TestCase):
    def setup_responses(self, rsps, mock_boto3, instance_id, asg_name):
        rsps.add(rsps.GET, 'http://169.254.169.254/latest/dynamic/instance-identity/document',
                 json={'instanceId': instance_id, 'region': 'eu-west-1'})
        mock_autoscaling_client = mock_boto3.client()
        autoscaling_instances = []
        if asg_name:
            autoscaling_instances.append({'AutoScalingGroupName': asg_name})
        mock_autoscaling_client.describe_auto_scaling_instances.return_value = {
            'AutoScalingInstances': autoscaling_instances
        }
        mock_autoscaling_client.describe_auto_scaling_groups.return_value = {
            'AutoScalingGroups': [{'Instances': [
                {'InstanceId': 'i-91234567890123456', 'LifecycleState': 'InService'},  # not first
                {'InstanceId': 'i-01234567890123456', 'LifecycleState': 'InService'},  # first
                {'InstanceId': 'i-00234567890123456', 'LifecycleState': 'Terminating'},  # not counted
            ]}]
        }

    @mock.patch('mtp_common.stack.boto3')
    def test_first_in_asg(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            self.setup_responses(rsps, mock_boto3, 'i-01234567890123456', 'test-asg')
            self.assertTrue(is_first_instance())

    @mock.patch('mtp_common.stack.boto3')
    def test_not_first_in_asg(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            self.setup_responses(rsps, mock_boto3, 'i-91234567890123456', 'test-asg')
            self.assertFalse(is_first_instance())

    @mock.patch('mtp_common.stack.boto3')
    def test_not_first_in_asg_because_terminating(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            self.setup_responses(rsps, mock_boto3, 'i-00234567890123456', 'test-asg')
            self.assertFalse(is_first_instance())

    @mock.patch('mtp_common.stack.boto3')
    def test_not_in_asg(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            self.setup_responses(rsps, mock_boto3, 'i-00004567890123456', None)
            with self.assertRaises(InstanceNotInAsgException):
                is_first_instance()

    @mock.patch('mtp_common.stack.boto3')
    def test_not_in_aws(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, 'http://169.254.169.254/latest/dynamic/instance-identity/document',
                     status=404)
            mock_autoscaling_client = mock_boto3.client()
            with self.assertRaises(StackInterrogationException):
                is_first_instance()
        mock_autoscaling_client.assert_not_called()
