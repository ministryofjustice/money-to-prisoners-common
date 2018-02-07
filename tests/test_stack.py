import unittest
from unittest import mock

import responses

from mtp_common.stack import InstanceNotInAsgException, StackInterrogationException, is_first_instance


class StackTestCase(unittest.TestCase):
    def setup_responses(self, rsps, mock_boto3, instance_id):
        rsps.add(rsps.GET, 'http://169.254.169.254/latest/dynamic/instance-identity/document',
                 json={'instanceId': instance_id, 'region': 'eu-west-1'})
        mock_autoscaling_client = mock_boto3.client()
        mock_autoscaling_client.describe_auto_scaling_instances.return_value = {
            'AutoScalingInstances': [{'AutoScalingGroupName': 'test-asg'}]
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
            self.setup_responses(rsps, mock_boto3, 'i-01234567890123456')
            self.assertTrue(is_first_instance())

    @mock.patch('mtp_common.stack.boto3')
    def test_not_first_in_asg(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            self.setup_responses(rsps, mock_boto3, 'i-91234567890123456')
            self.assertFalse(is_first_instance())

    @mock.patch('mtp_common.stack.boto3')
    def test_not_in_asg(self, mock_boto3):
        with responses.RequestsMock() as rsps:
            self.setup_responses(rsps, mock_boto3, 'i-00004567890123456')
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
