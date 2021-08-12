from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.test import override_settings
import responses

from mtp_common.notify import NotifyClient, TemplateError
from mtp_common.notify.templates import NotifyTemplateRegistry
from mtp_common.test_utils import silence_logger
from mtp_common.test_utils.notify import (
    GOVUK_NOTIFY_TEST_API_KEY, GOVUK_NOTIFY_TEST_REPLY_TO_PUBLIC, GOVUK_NOTIFY_TEST_REPLY_TO_STAFF,
    fake_template,
    mock_all_templates_response, mock_send_email_response,
    NotifyBaseTestCase,
)


class NotifyTestCase(NotifyBaseTestCase):
    @override_settings(GOVUK_NOTIFY_API_KEY='')
    def test_missing_settings(self):
        # client cannot be created if api key is missing
        with responses.RequestsMock(), self.assertRaises(AssertionError):
            NotifyClient.shared_client()

    @override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY)
    def test_notify_client_duplicate_templates(self):
        # if multiple templates have the same name, the client cannot be created
        with responses.RequestsMock() as rsps, self.assertRaises(TemplateError):
            mock_all_templates_response(rsps, templates=[
                fake_template('0000', 'generic', required_personalisations=['message']),
                fake_template('11', 'test-template'),
                fake_template('12', 'test-template'),
            ])
            NotifyClient.shared_client()

    @override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY)
    def test_notify_client_loads_templates(self):
        # client is created and loads all template name-ids pairs
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps)
            client = NotifyClient.shared_client()
        self.assertEqual(client.get_template_id_for_name('test-template'), '11')
        self.assertEqual(client.get_template_id_for_name('test-template2'), '12')
        with self.assertRaises(TemplateError):
            client.get_template_id_for_name('test-template3')

    @override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY)
    def test_send_email_to_one_address(self):
        # can send a simple email by checking params posted to GOV.UK Notify
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps)
            client = NotifyClient.shared_client()
            mock_send_email_response(rsps, '11', 'sample@localhost')
            message_ids = client.send_email('test-template', 'sample@localhost')
        self.assertEqual(len(message_ids), 1)

    @override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY)
    def test_send_email_to_several_addresses(self):
        # can send simple emails by checking params posted to GOV.UK Notify
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps)
            client = NotifyClient.shared_client()
            mock_send_email_response(rsps, '12', 'sample@localhost')
            mock_send_email_response(rsps, '12', 'sample2@localhost')
            message_ids = client.send_email('test-template2', ['sample@localhost', 'sample2@localhost'])
        self.assertEqual(len(message_ids), 2)

    @override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY)
    def test_send_personalised_email(self):
        # can send a personalised email by checking params posted to GOV.UK Notify
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps, templates=[
                fake_template('0000', 'generic', required_personalisations=['message']),
                fake_template('11', 'test-template', required_personalisations=['first name']),
            ])
            client = NotifyClient.shared_client()
            personalisation = {
                'first name': 'Sample',
            }
            mock_send_email_response(rsps, '11', 'sample@localhost', personalisation=personalisation)
            client.send_email('test-template', 'sample@localhost', personalisation=personalisation)

    @override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY)
    def test_send_personalised_email_with_reference(self):
        # can send a personalised email with a reference by checking params posted to GOV.UK Notify
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps, templates=[
                fake_template('0000', 'generic', required_personalisations=['message']),
                fake_template('11', 'test-template', required_personalisations=['first name']),
            ])
            client = NotifyClient.shared_client()
            personalisation = {
                'first name': 'Sample',
                'last name': 'Name',
            }
            reference = 'registration-code-12345'
            mock_send_email_response(
                rsps, '11', 'sample@localhost', personalisation=personalisation, reference=reference,
            )
            client.send_email(
                'test-template', 'sample@localhost', personalisation=personalisation, reference=reference,
            )

    @override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY,
                       GOVUK_NOTIFY_REPLY_TO_STAFF=GOVUK_NOTIFY_TEST_REPLY_TO_STAFF,
                       GOVUK_NOTIFY_REPLY_TO_PUBLIC=GOVUK_NOTIFY_TEST_REPLY_TO_PUBLIC)
    def test_choose_public_reply_to_address_by_default(self):
        # public site should default to using public reply-to address, but allows overriding
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps)
            client = NotifyClient.shared_client()
            mock_send_email_response(rsps, '11', 'sample1@localhost', staff_email=False)
            client.send_email('test-template', 'sample1@localhost')
            mock_send_email_response(rsps, '11', 'sample1@localhost', staff_email=True)
            client.send_email('test-template', 'sample1@localhost', staff_email=True)

    @override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY,
                       GOVUK_NOTIFY_REPLY_TO_STAFF=GOVUK_NOTIFY_TEST_REPLY_TO_STAFF,
                       GOVUK_NOTIFY_REPLY_TO_PUBLIC=GOVUK_NOTIFY_TEST_REPLY_TO_PUBLIC,
                       MOJ_INTERNAL_SITE=True)
    def test_choose_staff_reply_to_address_if_internal_app(self):
        # internal sites should default to using staff reply-to address, but allow overriding
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps)
            client = NotifyClient.shared_client()
            mock_send_email_response(rsps, '11', 'sample1@localhost', staff_email=True)
            client.send_email('test-template', 'sample1@localhost')
            mock_send_email_response(rsps, '11', 'sample1@localhost', staff_email=False)
            client.send_email('test-template', 'sample1@localhost', staff_email=False)

    @override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY)
    def test_send_plain_text_email(self):
        # can send a plain text email by checking params posted to GOV.UK Notify
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps)
            client = NotifyClient.shared_client()
            message = 'Unformatted message\nwithout links'
            mock_send_email_response(rsps, '0000', 'sample@localhost', personalisation={'message': message})
            client.send_plain_text_email('sample@localhost', message)


@override_settings(EMAIL_BACKEND='mtp_common.notify.email_backend.NotifyEmailBackend',
                   GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY)
class NotifyEmailBackendTestCase(NotifyBaseTestCase):
    def test_email_is_sent_using_notify(self):
        # subject and body both appear in the plain text message body of the email
        with responses.RequestsMock() as rsps, silence_logger():
            mock_all_templates_response(rsps)
            mock_send_email_response(rsps, '0000', 'sample@localhost', personalisation={
                'message': 'Email subject\n-------------\nUnformatted message\nwithout links',
            })
            mail.EmailMessage(
                subject='Email subject', body='Unformatted message\nwithout links',
                to=['sample@localhost'],
            ).send()
        self.assertEqual(len(mail.outbox), 0)

    def test_email_is_sent_to_all_recipients(self):
        # CCed and BBCed addresses also get sent an individual email (GOV.UK Notify does not permit multiple recipients)
        with responses.RequestsMock() as rsps, silence_logger():
            mock_all_templates_response(rsps)
            mock_send_email_response(rsps, '0000', 'sample@localhost', personalisation={'message': '1\n-\n2'})
            mock_send_email_response(rsps, '0000', 'sample1@localhost', personalisation={'message': '1\n-\n2'})
            mock_send_email_response(rsps, '0000', 'sample2@localhost', personalisation={'message': '1\n-\n2'})
            mock_send_email_response(rsps, '0000', 'sample3@localhost', personalisation={'message': '1\n-\n2'})
            mail.EmailMessage(
                subject='1', body='2',
                to=['sample@localhost', 'sample1@localhost'], cc=['sample2@localhost'], bcc=['sample3@localhost'],
            ).send()
        self.assertEqual(len(mail.outbox), 0)


@override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY)
class NotifyTemplateRegistryTestCase(NotifyBaseTestCase):
    # used to pretend that only the generic template is registered
    # so that this test case does not need to be updated for each new template registered with mtp-common
    _pretend_registered_templates = {'generic': {
        'subject': 'Prisoner money',
        'body': '((message))',
        'personalisation': ['message'],
    }}

    @responses.activate
    def test_templates_are_registered(self):
        # this test actually runs autodiscovery to register templates, all others mock out autodiscovery
        NotifyTemplateRegistry.get_all_templates.cache_clear()
        templates = NotifyTemplateRegistry.get_all_templates()
        self.assertIn('generic', templates)
        for template_details in templates.values():
            self.assertSetEqual(set(template_details.keys()), {'subject', 'body', 'personalisation'})

    @mock.patch.object(NotifyTemplateRegistry, 'get_all_templates', return_value=_pretend_registered_templates)
    def test_successful_template_checking(self, _mock_get_all_templates):
        # pretend that only the generic template exists and check that matching api response produces no errors
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps)
            error, messages = NotifyTemplateRegistry.check_notify_templates()
            self.assertFalse(error)
            self.assertEqual(len(messages), 0)

    @mock.patch.object(NotifyTemplateRegistry, 'get_all_templates', return_value={'generic': {
        'subject': 'Just for testing',
        'body': '((message))\n-----\nPrisoner money team',
        'personalisation': ['message'],
    }})
    def test_template_checking_with_warnings(self, _mock_get_all_templates):
        # pretend that the expected subject and body for the generic email was different
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps)
            error, messages = NotifyTemplateRegistry.check_notify_templates()
            self.assertFalse(error)
            self.assertListEqual(
                messages,
                ['Email template ‘generic’ has different subject',
                 'Email template ‘generic’ has different body copy']
            )

    @mock.patch.object(NotifyTemplateRegistry, 'get_all_templates', return_value={'generic': {
        'subject': 'Prisoner money',
        'body': '((message))\n-----\n((footer))',
        'personalisation': ['message', 'footer'],
    }})
    def test_template_checking_with_errors(self, _mock_get_all_templates):
        # pretend that the generic email expected more personalisation
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps)
            error, messages = NotifyTemplateRegistry.check_notify_templates()
            self.assertTrue(error)
            self.assertListEqual(
                messages,
                ['Email template ‘generic’ has different body copy',
                 'Email template ‘generic’ is missing required personalisation: footer']
            )

    @mock.patch.object(NotifyTemplateRegistry, 'get_all_templates', return_value=_pretend_registered_templates)
    def test_management_command(self, _mock_get_all_templates):
        with responses.RequestsMock() as rsps:
            mock_all_templates_response(rsps)
            call_command('check_notify_templates', verbosity=0)
