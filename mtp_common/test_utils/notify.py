import uuid

from django.test import SimpleTestCase
import responses

from mtp_common.notify import NotifyClient

GOVUK_NOTIFY_API_BASE_URL = 'https://api.notifications.service.gov.uk'
GOVUK_NOTIFY_TEST_API_KEY = 'test-11111111-1111-1111-1111-111111111111-22222222-2222-2222-2222-222222222222'
GOVUK_NOTIFY_TEST_REPLY_TO_STAFF = '1234'
GOVUK_NOTIFY_TEST_REPLY_TO_PUBLIC = '3123'


class NotifyBaseTestCase(SimpleTestCase):
    """
    Used for testing GOV.UK Notify client itself,
    not for other tests whose side effect is email sending
    """

    def setUp(self):
        # ensure client is not reused
        NotifyClient.shared_client.cache_clear()


def fake_template(template_id, template_name, required_personalisations=()):
    # fakes a template details response from GOV.UK Notify
    # the template called "generic" is special and is always expected to exist
    subject = 'Prisoner money' if template_name == 'generic' else 'Email subject'
    body = 'Email body' if not required_personalisations else '\n'.join(
        f'(({field}))'
        for field in required_personalisations
    )
    return {
        'type': 'email', 'postage': None, 'letter_contact_block': None,
        'created_at': '2021-08-11T11:00:00Z', 'updated_at': '2021-08-11T11:00:00Z', 'created_by': 'mtp@localhost',
        'version': 1,
        'id': template_id,
        'name': template_name,
        'subject': subject,
        'body': body,
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
        'uri': f'{GOVUK_NOTIFY_API_BASE_URL}/v2/notifications/{message_id}',
        'template': {
            'id': template_id,
            'uri': f'{GOVUK_NOTIFY_API_BASE_URL}/services/11111111-1111-1111-1111-111111111111'
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
