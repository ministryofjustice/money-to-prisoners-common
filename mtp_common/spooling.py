import inspect
import logging
import pickle
import time

logger = logging.getLogger('mtp')

try:
    import uwsgi
    import uwsgidecorators

    if uwsgi.masterpid() == 0 or 'spooler' not in uwsgi.opt:
        logger.warning('uWSGI master and spooler need to be enabled to use spooling')
        raise ImportError
except ImportError:
    uwsgi = None
    uwsgidecorators = None


class Context:
    __slots__ = ('async', 'retries')

    def __init__(self, async, retries=None):
        """
        Defines the context in which a spoolable task is running
        :param async: whether it is running in the spooler asynchronously
        :param retries: number of times the task will be rescheduled if it fails, 0 means this is the last try;
            None implies that retrying was not enabled
        """
        self.async = async
        self.retries = retries


class Spooler:
    identifier = b'_mtp'
    spooler_period = 30

    def __init__(self):
        self.registry = {}
        self.installed = False
        self.fallback = None

    def __call__(self, env):
        if self.identifier not in env:
            # fallback for compatibility with uwsgidecorators.spool
            if self.fallback:
                return self.fallback(env)
            logger.error('Unknown spooler task, no fallback method')
            return uwsgi.SPOOL_IGNORE

        task_name = env[self.identifier]
        if task_name not in self.registry:
            logger.error('Spooler task `%s` not registered' % task_name)
            return uwsgi.SPOOL_IGNORE

        task = self.registry[task_name]
        retries = env.get(b'retries')

        args, kwargs = (), {}
        try:
            if b'args' in env:
                args = pickle.loads(env[b'args'])
            if b'kwargs' in env:
                kwargs = pickle.loads(env[b'kwargs'])
            body = env.get('body') or env.get(b'body')
            if body:
                body = pickle.loads(body)
                kwargs.update(body)
        except (EOFError, pickle.UnpicklingError):
            logger.exception('Spooler task %s failed to load arguments; '
                             'large parameters should be added to body_params' % task.name)
            return uwsgi.SPOOL_OK

        try:
            self.run(task, args, kwargs, retries)
        except:
            logger.exception('Spooler task %s failed with uncaught exception' % task.name)

        return uwsgi.SPOOL_OK

    def install(self):
        if uwsgi:
            if 'spooler-frequency' in uwsgi.opt:
                self.spooler_period = int(uwsgi.opt['spooler-frequency'])
            self.fallback = uwsgidecorators.manage_spool_request
            uwsgi.spooler = self
            logger.info('MTP spooler installed')
            self.installed = True

    def register(self, task):
        if task.name in self.registry:
            logger.warning('%s is already registered as a spooler task' % task.name)
        self.registry[task.name] = task

    def schedule(self, task, args, kwargs, retries=None, **spool_kwargs):
        body = {}
        for body_param in task.body_params:
            if body_param not in kwargs:
                continue
            body[body_param] = kwargs.pop(body_param)
        job = {self.identifier: task.name}
        if retries is not None:
            job[b'retries'] = str(retries).encode('utf8')
        if args:
            job[b'args'] = pickle.dumps(args)
        if kwargs:
            job[b'kwargs'] = pickle.dumps(kwargs)
        if body:
            job[b'body'] = pickle.dumps(body)
        for key, value in spool_kwargs.items():
            job[key.encode('utf8')] = str(value).encode('utf8')
        uwsgi.spool(job)

    def run(self, task, args, kwargs, retries):
        if retries is not None:
            retries = int(retries)
            if task.context_name:
                kwargs[task.context_name] = Context(async=True, retries=retries)
            try:
                task.func(*args, **kwargs)
            except task.retry_on_errors:
                retries -= 1
                if retries < 0:
                    logger.exception('Spooler task %s failed after %d tries' % (task.name, task.retries + 1))
                else:
                    logger.warning('Spooler task %s failed, rescheduling' % task.name)

                    delay = (task.retries - retries + 1) * self.spooler_period + 2
                    self.schedule(task, args, kwargs, retries=retries, at=int(time.time()) + delay)
        else:
            if task.context_name:
                kwargs[task.context_name] = Context(async=True)
            task.func(*args, **kwargs)


spooler = Spooler()
spooler.install()


class Task:
    def __init__(self, func, context_name=None, pre_condition=True, retries=None, retry_on_errors=(), body_params=()):
        self.func = func
        self.name = func.__name__.encode('utf8')
        self.context_name = context_name
        self.pre_condition = pre_condition
        self.retries = retries
        self.retry_on_errors = retry_on_errors
        self.body_params = set(body_params)

        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __call__(self, *args, **kwargs):
        if self.pre_condition and spooler.installed:
            # schedule asynchronously
            spooler.schedule(self, args, kwargs, retries=self.retries)
            return

        # call synchronously
        try:
            self.run(args, kwargs)
        except:
            logger.exception('Spooler task %s failed with uncaught exception' % self.name)
            raise

    def run(self, args, kwargs):
        if self.retries:
            for retries_left in range(self.retries, -1, -1):
                try:
                    if self.context_name:
                        kwargs[self.context_name] = Context(async=False, retries=retries_left)
                    self.func(*args, **kwargs)
                    return
                except self.retry_on_errors:
                    time.sleep(0.001)
            logger.exception('Spooler task %s failed after %d tries' % (self.name, self.retries + 1))
        else:
            if self.context_name:
                kwargs[self.context_name] = Context(async=False)
            self.func(*args, **kwargs)


def spoolable(*, pre_condition=True, retries=None, retry_on_errors=(), body_params=()):
    """
    Decorates a function to make it spoolable using uWSGI, but if no spooling mechanism is available,
    the function is called synchronously. All decorated function arguments must be picklable and
    the first annotated with `Context` will receive an object that defines the current execution state.
    Return values are always ignored.
    :param pre_condition: additional condition needed to use spooler
    :param retries: number of times to retry if `retry_on_errors` trapped
    :param retry_on_errors: errors to trap and retry
    :param body_params: parameter names that can have large values and should use spooler body

    NB: client apps should import `from mtp_common.spoolable_tasks import spoolable` to also register mtp-common tasks
    """

    def decorator(func):
        context_name = None
        keyword_kinds = {inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY}
        invalid_body_params = set(body_params)
        for name, parameter in inspect.signature(func).parameters.items():
            if parameter.kind not in keyword_kinds:
                continue
            if not context_name and parameter.annotation is Context:
                context_name = name
            elif name in invalid_body_params:
                invalid_body_params.remove(name)
        if invalid_body_params:
            raise TypeError('Spoolable task body_params must be keyword arguments')

        task = Task(func, context_name=context_name, pre_condition=pre_condition,
                    retries=retries, retry_on_errors=retry_on_errors,
                    body_params=body_params)
        spooler.register(task)
        return task

    return decorator
