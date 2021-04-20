from unittest import mock

from django.test import SimpleTestCase

from mtp_common.security.checks import human_readable_check_rejection_reasons


class SecurityCheckRejectionReasonCategories(SimpleTestCase):
    def test_empty_rejection_reasons(self):
        self.assertListEqual(human_readable_check_rejection_reasons(None), [])
        self.assertListEqual(human_readable_check_rejection_reasons({}), [])

    def test_text_rejection_reason_category(self):
        self.assertListEqual(human_readable_check_rejection_reasons({
            'intelligence_report_id': 'ABC321',
        }), [
            'Associated intelligence report (IR): ABC321'
        ])

    def test_bool_rejection_reason_category(self):
        self.assertListEqual(human_readable_check_rejection_reasons({
            'payment_source_unidentified': True,
        }), [
            'Payment source is unidentified'
        ])

    @mock.patch('mtp_common.security.checks.logger')
    def test_malformed_bool_rejection_reason_category(self, mocked_logger):
        self.assertListEqual(human_readable_check_rejection_reasons({
            'payment_source_unidentified': 'False name used',
        }), [
            'Payment source is unidentified'
        ])
        mocked_logger.error.assert_called()

    @mock.patch('mtp_common.security.checks.logger')
    def test_malformed_rejection_reason_category(self, mocked_logger):
        self.assertListEqual(human_readable_check_rejection_reasons({
            'mercury_code': 'ABC321',
        }), [
            'mercury_code: ABC321'
        ])
        mocked_logger.error.assert_called()
