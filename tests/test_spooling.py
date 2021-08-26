import importlib
import pickle
import unittest
from unittest import mock

from django.core import mail
from django.test.utils import override_settings
from notifications_python_client.errors import APIError, HTTPError, InvalidResponse
from requests import RequestException

from mtp_common.spooling import Context, Task, spoolable, spooler
from mtp_common.test_utils.notify import NotifyMock, GOVUK_NOTIFY_TEST_API_KEY, GOVUK_NOTIFY_TEST_REPLY_TO_STAFF
from tests.utils import SimpleTestCase


@unittest.skipIf(spooler.installed, 'Cannot test spoolable tasks under uWSGI')
class SpoolableTestCase(unittest.TestCase):
    def setUp(self):
        spooler._registry = {}

    def test_context_argument(self):
        @spoolable()
        def passes():
            pass

        self.assertIsInstance(passes, Task)
        self.assertIsNone(passes.context_name)

        state = {'runs': 0}

        @spoolable()
        def passes1(ctx: Context):
            self.assertIsInstance(ctx, Context)
            state['runs'] += 1

        @spoolable()  # noqa
        def passes2(a, b, context: Context = None):
            self.assertIsInstance(context, Context)
            state['runs'] += 1

        @spoolable()  # noqa
        def passes3(*, context: Context, **kwargs):
            self.assertIsInstance(context, Context)
            state['runs'] += 1

        @spoolable()  # noqa
        def passes4(*args, context: Context, **kwargs):
            self.assertIsInstance(context, Context)
            state['runs'] += 1

        @spoolable()  # noqa
        def passes5(*args, context: Context = None, **kwargs):
            self.assertIsInstance(context, Context)
            state['runs'] += 1

        passes1()
        passes2(1, b=2)
        passes3()
        passes4()
        passes5()
        self.assertEqual(state['runs'], 5)

    def test_must_accept_body_params_as_keyword_arguments(self):
        with self.assertRaises(TypeError):
            @spoolable(body_params=('a',))
            def fails_1():
                pass

        with self.assertRaises(TypeError):
            @spoolable(body_params=('a',))  # noqa
            def fails_2(*a):
                pass

        with self.assertRaises(TypeError):
            @spoolable(body_params=('a',))  # noqa
            def fails_3(*args, **kwargs):
                pass

        @spoolable(body_params=('a',))  # noqa
        def passes4(a):
            pass

        @spoolable(body_params=('a', 'b'))  # noqa
        def passes5(a, b, **kwargs):
            pass

        @spoolable(body_params=('a', 'b'))  # noqa
        def passes6(a, b, *args, **kwargs):
            pass

    @mock.patch('mtp_common.spooling.logger')
    def test_warning_if_task_name_reused(self, logger):
        @spoolable()
        def func():
            pass

        @spoolable()  # noqa
        def func():  # noqa: F811
            pass

        self.assertTrue(logger.warning.called)

    def test_task_register(self):
        @spoolable()
        def func():
            pass

        @spoolable()
        def func2():
            pass

        self.assertIn(b'func', spooler._registry)
        self.assertIn(b'func2', spooler._registry)

    def test_synchronous_run(self):
        state = {'run': False}

        @spoolable()
        def func(a, b, context: Context):
            self.assertEqual(a, 1)
            self.assertEqual(b, 2)
            self.assertFalse(context.spooled)
            state['run'] = True
            return 321

        self.assertIsNone(func(1, b=2), 'spooler tasks cannot return values')
        self.assertTrue(state['run'], 'spooler task did not run')

    @mock.patch('mtp_common.spooling.logger')
    def test_synchronous_raising_unknown_error(self, logger):
        state = {'runs': 0}

        @spoolable()
        def func():
            state['runs'] += 1
            raise ValueError()

        with self.assertRaises(ValueError):
            func()
        self.assertTrue(logger.exception.called)
        self.assertEqual(state['runs'], 1)

    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_run(self, uwsgi):
        state = {'run': False}

        @spoolable()
        def func(a, b, context: Context):
            self.assertEqual(a, 1)
            self.assertEqual(b, 2)
            self.assertTrue(context.spooled)
            state['run'] = True
            return 321

        self.assertIsNone(func(1, 2), 'spooler tasks cannot return values')
        self.assertFalse(state['run'], 'spooler task ran synchronously')
        self.assertTrue(uwsgi.spool.called)
        # simulate spooler:
        self.assertEqual(spooler({
            spooler.identifier: b'func',
            b'args': pickle.dumps((1,)),
            b'kwargs': pickle.dumps({'b': 2}),
        }), uwsgi.SPOOL_OK)
        self.assertTrue(state['run'], 'spooler task did not run')

    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_precondition(self, uwsgi):
        state = {'runs': 0}

        @spoolable(pre_condition=True)
        def async_task(context: Context):
            self.assertTrue(context.spooled)
            state['runs'] += 1

        @spoolable(pre_condition=False)
        def sync_task(context: Context):
            self.assertFalse(context.spooled)
            state['runs'] += 1

        async_task()
        sync_task()
        self.assertEqual(len(uwsgi.spool.call_args_list), 1)
        spooler({spooler.identifier: b'async_task'})
        self.assertEqual(state['runs'], 2)

    @mock.patch.object(spooler, 'installed', True)
    @mock.patch.object(spooler, 'fallback')
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_fallback(self, uwsgi, fallback):
        fallback.return_value = uwsgi.SPOOL_OK
        self.assertEqual(spooler({
            b'ud_spool_func': b'func',
        }), uwsgi.SPOOL_OK)
        self.assertTrue(fallback.called)

    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.logger')
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_missing(self, uwsgi, logger):
        self.assertEqual(spooler({
            spooler.identifier: b'func',
        }), uwsgi.SPOOL_IGNORE)
        self.assertTrue(logger.error.called, True)


@override_settings(GOVUK_NOTIFY_API_KEY=GOVUK_NOTIFY_TEST_API_KEY,
                   GOVUK_NOTIFY_REPLY_TO_STAFF=GOVUK_NOTIFY_TEST_REPLY_TO_STAFF)
@unittest.skipIf(spooler.installed, 'Cannot test spoolable tasks under uWSGI')
class SendEmailTestCase(SimpleTestCase):
    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_send_email_task(self, uwsgi):
        # send_email task should call out to GOV.UK Notify when spooler call is simulated
        import mtp_common.tasks

        if b'send_email' not in spooler._registry:
            # other tests had already loaded the module and then cleared the registry
            importlib.reload(mtp_common.tasks)

        self.assertIn(b'send_email', spooler._registry)

        job = {
            spooler.identifier: b'send_email',
            b'args': pickle.dumps(('generic', 'test1@example.com')),
            b'kwargs': pickle.dumps(dict(staff_email=True)),
            b'body': pickle.dumps(dict(personalisation={'abc': '321'})),
        }

        # schedule call
        self.assertIsNone(mtp_common.tasks.send_email(
            'generic', 'test1@example.com', personalisation={'abc': '321'}, staff_email=True)
        )
        self.assertEqual(len(mail.outbox), 0)
        call_args, _ = uwsgi.spool.call_args
        self.assertDictEqual(call_args[0], job)

        # simulate call
        with NotifyMock() as mock_notify:
            self.assertEqual(spooler(job), uwsgi.SPOOL_OK)
            send_email_request_data = mock_notify.send_email_request_data
        self.assertEqual(len(send_email_request_data), 1)
        send_email_request_data = send_email_request_data[0]
        send_email_request_data.pop('template_id')  # because template_id is random
        self.assertDictEqual(send_email_request_data, {
            'email_address': 'test1@example.com',
            'personalisation': {'abc': '321'},
            'email_reply_to_id': GOVUK_NOTIFY_TEST_REPLY_TO_STAFF,
        })

        self.assertEqual(len(mail.outbox), 0)

    @mock.patch('mtp_common.spooling.logger')
    @mock.patch('mtp_common.notify.client.NotifyClient.send_email')
    def test_synchronous_send_email_does_not_retry(self, mocked_send_email, logger):
        from mtp_common.tasks import send_email

        state = {'calls': 0}

        def count_calls_and_raise_error(*args, **kwargs):
            state['calls'] += 1
            raise APIError

        mocked_send_email.side_effect = count_calls_and_raise_error
        with self.assertRaises(APIError), NotifyMock(assert_all_requests_are_fired=False):
            send_email('generic', 'admin@mtp.local', retry_attempts=10)
        self.assertEqual(state['calls'], 1)
        self.assertTrue(logger.exception.called, True)

    def assertAsynchronousSendEmailRetries(self, uwsgi, mocked_send_email, logger, error_to_raise):  # noqa: N802
        from mtp_common.tasks import send_email

        state = {'calls': 0}

        def count_calls_and_raise_error(*args, **kwargs):
            state['calls'] += 1
            raise error_to_raise

        mocked_send_email.side_effect = count_calls_and_raise_error
        uwsgi.spool = spooler.__call__
        with NotifyMock(assert_all_requests_are_fired=False):
            send_email('generic', 'admin@mtp.local', retry_attempts=3)
        self.assertEqual(state['calls'], 4, msg='send_email should have retried 3 times and failed after')
        self.assertTrue(logger.exception.called, True)

    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.logger')
    @mock.patch('mtp_common.notify.client.NotifyClient.send_email')
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_send_email_retries_on_503_service_unavailable(self, uwsgi, mocked_send_email, logger):
        self.assertAsynchronousSendEmailRetries(
            uwsgi, mocked_send_email, logger,
            APIError
        )

    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.logger')
    @mock.patch('mtp_common.notify.client.NotifyClient.send_email')
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_send_email_retries_on_500_internal_error(self, uwsgi, mocked_send_email, logger):
        self.assertAsynchronousSendEmailRetries(
            uwsgi, mocked_send_email, logger,
            HTTPError.create(RequestException(response=mock.MagicMock(status_code=500)))
        )

    def assertAsynchronousSendEmailDoesNotRetry(self, uwsgi, mocked_send_email, logger, error_to_raise):  # noqa: N802
        from mtp_common.tasks import send_email

        state = {'calls': 0}

        def count_calls_and_raise_error(*args, **kwargs):
            state['calls'] += 1
            raise error_to_raise

        mocked_send_email.side_effect = count_calls_and_raise_error
        uwsgi.spool = spooler.__call__
        with NotifyMock(assert_all_requests_are_fired=False):
            send_email('generic', 'admin@mtp.local', retry_attempts=10)
        self.assertEqual(state['calls'], 1, msg='send_email should not have retried')
        self.assertTrue(logger.exception.called, True)

    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.logger')
    @mock.patch('mtp_common.notify.client.NotifyClient.send_email')
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_send_email_does_not_retry_on_invalid_json_response(self, uwsgi, mocked_send_email, logger):
        self.assertAsynchronousSendEmailDoesNotRetry(
            uwsgi, mocked_send_email, logger,
            InvalidResponse
        )

    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.logger')
    @mock.patch('mtp_common.notify.client.NotifyClient.send_email')
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_send_email_does_not_retry_on_400(self, uwsgi, mocked_send_email, logger):
        self.assertAsynchronousSendEmailDoesNotRetry(
            uwsgi, mocked_send_email, logger,
            HTTPError.create(RequestException(response=mock.MagicMock(status_code=400)))
        )

    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.logger')
    @mock.patch('mtp_common.notify.client.NotifyClient.send_email')
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_send_email_does_not_retry_on_403(self, uwsgi, mocked_send_email, logger):
        self.assertAsynchronousSendEmailDoesNotRetry(
            uwsgi, mocked_send_email, logger,
            HTTPError.create(RequestException(response=mock.MagicMock(status_code=403)))
        )
