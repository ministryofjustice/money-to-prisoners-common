import importlib
import pickle
import unittest
from unittest import mock

from django.core import mail
from django.test.utils import override_settings

from mtp_common.spooling import spoolable, spooler
from tests.utils import SimpleTestCase


class CustomError(Exception):
    pass


@unittest.skipIf(spooler.installed, 'Cannot test spoolable tasks under uWSGI')
class SpoolableTestCase(unittest.TestCase):
    def setUp(self):
        spooler.registry = {}

    def test_must_accept_all_task_arguments(self):
        with self.assertRaises(TypeError):
            @spoolable()
            def fails():
                pass

        with self.assertRaises(TypeError):
            @spoolable()  # noqa
            def fails(a):
                pass

        with self.assertRaises(TypeError):
            @spoolable()  # noqa
            def fails(a, *b, c=None):
                pass

        with self.assertRaises(TypeError):
            @spoolable()  # noqa
            def fails(spoolable_async, *spoolable_retries, **kwargs):
                pass

        @spoolable()
        def passes1(**kwargs):
            pass

        @spoolable()  # noqa
        def passes2(spoolable_async=False, spoolable_retries=0):
            pass

        @spoolable()  # noqa
        def passes3(spoolable_async, spoolable_retries, *, a=None, **kwargs):
            pass

        spooler.registry = {}

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
        def passes4(a, **kwargs):
            pass

        @spoolable(body_params=('a', 'b'))  # noqa
        def passes5(a, b, **kwargs):
            pass

        @spoolable(body_params=('a', 'b'))  # noqa
        def passes6(a, b, *args, **kwargs):
            pass

    @mock.patch('mtp_common.spooling.logger')
    def test_warning_if_task_name_reused(self, logger):
        @spoolable()  # noqa
        def func(**kwargs):
            pass

        @spoolable()  # noqa
        def func(**kwargs):
            pass

        self.assertTrue(logger.warning.called)

    def test_task_register(self):
        @spoolable()
        def func(**kwargs):
            pass

        @spoolable()
        def func2(**kwargs):
            pass

        self.assertIn(b'func', spooler.registry)
        self.assertIn(b'func2', spooler.registry)

    def test_synchronous_run(self):
        state = {'run': False}

        @spoolable()
        def func(a, b, **kwargs):
            self.assertEqual(a, 1)
            self.assertEqual(b, 2)
            self.assertFalse(kwargs['spoolable_async'])
            state['run'] = True
            return 321

        self.assertIsNone(func(1, b=2), 'spooler tasks cannot return values')
        self.assertTrue(state['run'], 'spooler task did not run')

    @mock.patch('mtp_common.spooling.logger')
    def test_synchronous_retries(self, logger):
        state = {'runs': 0}

        @spoolable(retries=2, retry_on_errors=(CustomError,))  # noqa
        def func(**kwargs):
            state['runs'] += 1
            raise CustomError()

        func()
        self.assertTrue(logger.exception.called)
        self.assertEqual(state['runs'], 3)

    @mock.patch('mtp_common.spooling.logger')
    def test_synchronous_retries_retry_count(self, logger):
        state = {'runs': 0}

        @spoolable(retries=2, retry_on_errors=(CustomError,))
        def func(**kwargs):
            self.assertEqual(kwargs['spoolable_retries'], 2 - state['runs'])
            state['runs'] += 1
            raise CustomError()

        func()
        self.assertTrue(logger.exception.called)
        self.assertEqual(state['runs'], 3)

    @mock.patch('mtp_common.spooling.logger')
    def test_synchronous_retries_raising_unknown_error(self, logger):
        state = {'runs': 0}

        @spoolable(retries=10, retry_on_errors=(CustomError,))  # noqa
        def func(**kwargs):
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
        def func(a, b, **kwargs):
            self.assertEqual(a, 1)
            self.assertEqual(b, 2)
            self.assertTrue(kwargs['spoolable_async'])
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
        def async(**kwargs):
            self.assertTrue(kwargs['spoolable_async'])
            state['runs'] += 1

        @spoolable(pre_condition=False)
        def sync(**kwargs):
            self.assertFalse(kwargs['spoolable_async'])
            state['runs'] += 1

        async()
        sync()
        self.assertEqual(len(uwsgi.spool.call_args_list), 1)
        spooler({spooler.identifier: b'async'})
        self.assertEqual(state['runs'], 2)

    @mock.patch.object(spooler, 'installed', True)
    @mock.patch('mtp_common.spooling.logger')
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_retries(self, uwsgi, logger):
        state = {'runs': 0}

        @spoolable(retries=2, retry_on_errors=(CustomError,))
        def func(**kwargs):
            self.assertTrue(kwargs['spoolable_async'])
            self.assertEqual(kwargs['spoolable_retries'], 2 - state['runs'])
            state['runs'] += 1
            raise CustomError()

        self.assertIsNone(func(), 'spooler tasks cannot return values')
        self.assertEqual(state['runs'], 0)
        self.assertTrue(uwsgi.spool.called)
        # simulate spooler:
        self.assertEqual(spooler({
            spooler.identifier: b'func',
            b'retries': b'2',
        }), uwsgi.SPOOL_OK)
        self.assertEqual(spooler({
            spooler.identifier: b'func',
            b'retries': b'1',
        }), uwsgi.SPOOL_OK)
        self.assertEqual(spooler({
            spooler.identifier: b'func',
            b'retries': b'0',
        }), uwsgi.SPOOL_OK)
        self.assertEqual(state['runs'], 3)
        self.assertTrue(logger.exception.called)

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
    @mock.patch('tests.utils.get_template_source')
    @mock.patch('mtp_common.spooling.uwsgi')
    def test_asynchronous_send_email_task(self, uwsgi, get_template_source):
        import mtp_common.spoolable_tasks

        if b'send_email' not in spooler.registry:
            # other tests had already loaded the module and then cleared the registry
            importlib.reload(mtp_common.spoolable_tasks)

        self.assertIn(b'send_email', spooler.registry)

        # template setup
        email_body = 'abc-{{ abc }}'
        get_template_source.return_value = email_body

        email_args = ('test1@example.com', 'tpl.txt', '890')
        email_kwargs = dict(context={'abc': '321'}, html_template='tpl.html')
        job = {
            spooler.identifier: b'send_email',
            b'retries': b'3',
            b'args': pickle.dumps(email_args),
            b'kwargs': pickle.dumps(email_kwargs),
        }

        # schedule call
        self.assertIsNone(mtp_common.spoolable_tasks.send_email(*email_args, **email_kwargs))
        self.assertEqual(len(mail.outbox), 0)
        uwsgi.spool.assert_called_with(job)

        # simulate call
        self.assertEqual(spooler(job), uwsgi.SPOOL_OK)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, '890')
        self.assertEqual(email.body, 'abc-321')
        self.assertSequenceEqual(email.recipients(), ['test1@example.com'])
