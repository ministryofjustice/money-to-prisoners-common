import uuid

from django.test import SimpleTestCase, override_settings
import responses

from mtp_common.notify import NotifyClient, TemplateError

GOVUK_NOTIFY_TEST_API_KEY = 'test-11111111-1111-1111-1111-111111111111-22222222-2222-2222-2222-222222222222'
GOVUK_NOTIFY_API_BASE_URL = 'https://api.notifications.service.gov.uk'


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
            fake_template('11', 'test-template'),
            fake_template('12', 'test-template2'),
        ]},
    )


def mock_send_email_response(rsps, template_id, to, personalisation=None, reference=None):
    json_sent = {
        'template_id': template_id,
        'email_address': to,
    }
    if personalisation:
        json_sent['personalisation'] = personalisation
    if reference:
        json_sent['reference'] = reference

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


class NotifyTestCase(SimpleTestCase):
    def setUp(self):
        # ensure client is not reused
        NotifyClient.shared_client.cache_clear()

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
