import json
import uuid

from django.test import SimpleTestCase
import responses

from mtp_common.notify import NotifyClient
from mtp_common.notify.templates import NotifyTemplateRegistry

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


class NotifyMock(responses.RequestsMock):
    """
    Used for testing sending of emails from MTP apps.
    Intercepts all calls to send emails to templates registered with NotifyTemplateRegistry.
    Assertions can be made on `send_email_calls` before the context manager exits.
    """

    def __enter__(self):
        # ensure client is not reused
        NotifyClient.shared_client.cache_clear()

        super().__enter__()

        # return all registered templates
        mock_all_templates_response(self, templates=[
            dict(
                _base_email_template_response,
                id=str(uuid.uuid4()),
                name=template_name,
                subject=template_details['subject'],
                body=template_details['body'],
                personalisation={
                    field: {'required': True}
                    for field in template_details['personalisation']
                },
            )
            for template_name, template_details in NotifyTemplateRegistry.get_all_templates().items()
        ])

        def send_email_callback(request):
            request_data = json.loads(request.body)
            template_id = request_data['template_id']
            reference = request_data.get('reference')
            response_data = fake_email_response(template_id, reference=reference)
            return 200, {}, json.dumps(response_data)

        # allow sending emails without requiring specific params so assertions can be made by specific tests
        self.add_callback(
            responses.POST,
            f'{GOVUK_NOTIFY_API_BASE_URL}/v2/notifications/email',
            callback=send_email_callback,
            content_type='application/json',
        )

        return self

    @property
    def send_email_calls(self):
        """
        Filter out requests calls only to send emails
        """

        def send_email_filter(call):
            return call.request.url == f'{GOVUK_NOTIFY_API_BASE_URL}/v2/notifications/email' \
                   and call.request.method == responses.POST

        return list(filter(send_email_filter, self.calls))

    @property
    def send_email_request_data(self):
        """
        Returns only the request data posted whilst sending emails
        """
        return [
            json.loads(call.request.body)
            for call in self.send_email_calls
        ]


_base_email_template_response = {
    'type': 'email', 'postage': None, 'letter_contact_block': None,
    'created_at': '2021-08-11T11:00:00Z', 'updated_at': '2021-08-11T11:00:00Z', 'created_by': 'mtp@localhost',
    'version': 1,
}


def fake_template(template_id, template_name, required_personalisations=()):
    # fakes a template details response from GOV.UK Notify
    if template_name == 'generic':
        # the template called "generic" is special and is always expected to exist
        # it's a fallback used to be able to send a message with any subject and body
        subject = '((subject))'
        body = '((message))'
    else:
        subject = 'Email subject'
        body = 'Email body' if not required_personalisations else '\n'.join(
            f'(({field}))'
            for field in required_personalisations
        )
    return dict(
        _base_email_template_response,
        id=template_id,
        name=template_name,
        subject=subject,
        body=body,
        personalisation={
            field: {'required': True}
            for field in required_personalisations
        },
    )


def mock_all_templates_response(rsps, templates=()):
    rsps.add(
        responses.GET,
        f'{GOVUK_NOTIFY_API_BASE_URL}/v2/templates?type=email',
        match_querystring=True,
        json={'templates': templates or [
            fake_template('0000', 'generic', required_personalisations=['subject', 'message']),
            fake_template('11', 'test-template'),
            fake_template('12', 'test-template2'),
        ]},
    )


def fake_email_response(template_id, reference=None):
    message_id = str(uuid.uuid4())
    return {
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

    rsps.add(
        responses.POST,
        f'{GOVUK_NOTIFY_API_BASE_URL}/v2/notifications/email',
        match_querystring=True,
        json=fake_email_response(template_id, reference=reference),
        match=[responses.json_params_matcher(json_sent)],
    )
