import unittest
from unittest import mock

from django.core import mail
from django.test import SimpleTestCase
from django.test.utils import override_settings

from mtp_common.tasks import send_email
from mtp_common.spooling import spooler


@unittest.skipIf(spooler.installed, 'Cannot test emails under uWSGI')
@override_settings(APP='common', ENVIRONMENT='local')
class EmailTestCase(SimpleTestCase):
    @mock.patch('mtp_common.tasks.ConsoleEmailBackend')
    def test_send_plain_email(self, backend):
        send_email('test1@example.com', 'dummy-email.txt', 'email subject 1')
        self.assertFalse(backend().write_message.called)
        send_email('test2@example.com', 'dummy-email.txt', 'email subject 2')
        self.assertFalse(backend().write_message.called)

        self.assertEqual(len(mail.outbox), 2)
        for index, email in enumerate(mail.outbox):
            self.assertEqual(email.body.strip(), 'EMAIL-')
            self.assertEqual(email.subject, 'email subject %d' % (index + 1))
            self.assertSequenceEqual(email.recipients(), ['test%d@example.com' % (index + 1)])

    @mock.patch('mtp_common.tasks.ConsoleEmailBackend')
    def test_special_addresses_ignored(self, backend):
        for address in ('admin@mtp.local', 'test-prison-1@mtp.local', 'disallowed@outside.local'):
            send_email(address, 'dummy-email.txt', 'email subject')
            self.assertTrue(backend().write_message.called)

    @override_settings(ENVIRONMENT='prod')
    @mock.patch('mtp_common.tasks.ConsoleEmailBackend')
    def test_special_addresses_ignored_on_production(self, backend):
        for address in ('admin@mtp.local', 'test-prison-1@mtp.local', 'disallowed@outside.local'):
            send_email(address, 'dummy-email.txt', 'email subject')
            self.assertFalse(backend().write_message.called)
