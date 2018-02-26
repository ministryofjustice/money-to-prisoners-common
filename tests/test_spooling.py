import importlib
import pickle
import unittest
from unittest import mock

from django.core import mail
from django.test.utils import override_settings

from mtp_common.spooling import Context, Task, spoolable, spooler
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
            def fails():
                pass

        with self.assertRaises(TypeError):
            @spoolable(body_params=('a',))  # noqa
            def fails(*a):
                pass

        with self.assertRaises(TypeError):
            @spoolable(body_params=('a',))  # noqa
            def fails(*args, **kwargs):
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
        def func():
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
        def async(context: Context):
            self.assertTrue(context.spooled)
            state['runs'] += 1

        @spoolable(pre_condition=False)
        def sync(context: Context):
            self.assertFalse(context.spooled)
            state['runs'] += 1

        async()
        sync()
        self.assertEqual(len(uwsgi.spool.call_args_list), 1)
        spooler({spooler.identifier: b'async'})
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


@override_settings(APP='common', ENVIRONMENT='local')
@unittest.skipIf(spooler.installed, 'Cannot test spoolable tasks under uWSGI')
class SendEmailTestCase(SimpleTestCase):
    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_send_email_task(self, uwsgi):
        import mtp_common.tasks

        if b'send_email' not in spooler._registry:
            # other tests had already loaded the module and then cleared the registry
            importlib.reload(mtp_common.tasks)

        self.assertIn(b'send_email', spooler._registry)

        email_args = ('test1@example.com', 'dummy-email.txt', '890')
        email_kwargs = dict(context={'abc': '321'}, html_template='dummy-email.html')
        job = {
            spooler.identifier: b'send_email',
            b'args': pickle.dumps(email_args),
            b'kwargs': pickle.dumps(email_kwargs),
        }

        # schedule call
        self.assertIsNone(mtp_common.tasks.send_email(*email_args, **email_kwargs))
        self.assertEqual(len(mail.outbox), 0)
        uwsgi.spool.assert_called_with(job)

        # simulate call
        self.assertEqual(spooler(job), uwsgi.SPOOL_OK)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, '890')
        self.assertEqual(email.body, 'EMAIL-321')
        self.assertSequenceEqual(email.recipients(), ['test1@example.com'])

    @override_settings(ENVIRONMENT='prod')
    @mock.patch('mtp_common.spooling.logger')
    @mock.patch('mtp_common.tasks.EmailMultiAlternatives')
    def test_synchronous_send_email_does_not_retry(self, mocked_email, logger):
        from mtp_common.tasks import mail_errors, send_email

        mail_error = mail_errors[0]
        state = {'calls': 0}

        def mock_send_email():
            state['calls'] += 1
            raise mail_error

        mocked_email().send = mock_send_email
        with self.assertRaises(mail_error):
            send_email('admin@mtp.local', 'dummy-email.txt', 'email subject', retry_attempts=10)
        self.assertEqual(state['calls'], 1)
        self.assertTrue(logger.exception.called, True)

    @override_settings(ENVIRONMENT='prod')
    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.logger')
    @mock.patch('mtp_common.tasks.EmailMultiAlternatives')
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_send_email_retries(self, uwsgi, mocked_email, logger):
        from mtp_common.tasks import mail_errors, send_email

        mail_error = mail_errors[0]
        state = {'calls': 0}

        def mock_send_email():
            state['calls'] += 1
            raise mail_error

        mocked_email().send = mock_send_email
        uwsgi.spool = spooler.__call__
        send_email('admin@mtp.local', 'dummy-email.txt', 'email subject', retry_attempts=3)
        self.assertEqual(state['calls'], 4)
        self.assertTrue(logger.exception.called, True)
