import uuid

from django.core import mail
from django.test import SimpleTestCase, override_settings
import responses

from mtp_common.notify import NotifyClient, TemplateError
from mtp_common.test_utils import silence_logger

GOVUK_NOTIFY_TEST_API_KEY = 'test-11111111-1111-1111-1111-111111111111-22222222-2222-2222-2222-222222222222'
GOVUK_NOTIFY_API_BASE_URL = 'https://api.notifications.service.gov.uk'
GOVUK_NOTIFY_TEST_REPLY_TO_STAFF = '1234'
GOVUK_NOTIFY_TEST_REPLY_TO_PUBLIC = '3123'


def fake_template(template_id, template_name, required_personalisations=()):
    return {
        'type': 'email', 'postage': None, 'letter_contact_block': None,
        'created_at': '2021-08-11T11:00:00Z', 'updated_at': '2021-08-11T11:00:00Z', 'created_by': 'mtp@localhost',
        'version': 1,
        'id': template_id,
        'name': template_name,
        'subject': 'Subject',
        'body': 'Email ' + '\n'.join(
            f'(({field}))'
            for field in required_personalisations
        ),
        'personalisation': {
            field: {'required': True}
            for field in required_personalisations
        },
    }


def mock_all_templates_response(rsps, templates=()):
    rsps.add(
        responses.GET,
        f'{GOVUK_NOTIFY_API_BASE_URL}/v2/templates?type=email',
        match_querystring=True,
        json={'templates': templates or [
            fake_template('0000', 'generic', required_personalisations=['message']),
            fake_template('11', 'test-template'),
            fake_template('12', 'test-template2'),
        ]},
    )


def mock_send_email_response(rsps, template_id, to, personalisation=None, reference=None, staff_email=None):
    json_sent = {
        'template_id': template_id,
        'email_address': to,
    }
    if personalisation:
        json_sent['personalisation'] = personalisation
    if reference:
        json_sent['reference'] = reference
    if staff_email is True:
        json_sent['email_reply_to_id'] = GOVUK_NOTIFY_TEST_REPLY_TO_STAFF
    if staff_email is False:
        json_sent['email_reply_to_id'] = GOVUK_NOTIFY_TEST_REPLY_TO_PUBLIC

    message_id = str(uuid.uuid4())
    json_received = {
        'id': message_id, 'reference': reference,
        'uri': f'https://api.notifications.service.gov.uk/v2/notifications/{message_id}',
        'template': {
            'id': template_id,
            'uri': f'https://api.notifications.service.gov.uk/services/11111111-1111-1111-1111-111111111111'
                   f'/templates/{template_id}',
            'version': 1
        },
        'content': {
            'from_email': 'prisoner.money@localhost',
            'subject': '?????????',
            'body': '?????????',
        },
        'scheduled_for': None,
    }

    rsps.add(
        responses.POST,
        f'{GOVUK_NOTIFY_API_BASE_URL}/v2/notifications/email',
        match_querystring=True,
        json=json_received,
        match=[responses.json_params_matcher(json_sent)],
    )


class NotifyBaseTestCase(SimpleTestCase):
    def setUp(self):
        # ensure client is not reused
        NotifyClient.shared_client.cache_clear()


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
