import unittest

from django.core import mail
from django.test import SimpleTestCase
from django.test.utils import override_settings

from mtp_common.spooling import spooler
from mtp_common.tasks import send_email
from mtp_common.test_utils.notify import NotifyMock, GOVUK_NOTIFY_TEST_API_KEY


@unittest.skipIf(spooler.installed, 'Cannot test emails under uWSGI')
@override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY)
class EmailTestCase(SimpleTestCase):
    def test_send_email(self):
        # send_email task should call out to GOV.UK Notify
        with NotifyMock() as mock_notify:
            send_email('generic', 'test1@example.com')
            send_email('generic', 'test2@example.com')

            for index, send_email_data in enumerate(mock_notify.send_email_request_data):
                self.assertEqual(send_email_data['email_address'], f'test{index + 1}@example.com')
                self.assertIn('template_id', send_email_data)
        self.assertEqual(len(mail.outbox), 0)
