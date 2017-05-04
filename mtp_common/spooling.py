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


class Spooler:
    identifier = b'_mtp'
    task_arguments = ('spoolable_async', 'spoolable_retries')
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
            for arg in self.task_arguments:
                kwargs.pop(arg, None)
            job[b'kwargs'] = pickle.dumps(kwargs)
        if body:
            job[b'body'] = pickle.dumps(body)
        for key, value in spool_kwargs.items():
            job[key.encode('utf8')] = str(value).encode('utf8')
        uwsgi.spool(job)

    def run(self, task, args, kwargs, retries):
        kwargs['spoolable_async'] = True
        if retries is not None:
            retries = int(retries)
            kwargs['spoolable_retries'] = retries
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
            task.func(*args, **kwargs)


spooler = Spooler()
spooler.install()


class Task:
    def __init__(self, func, pre_condition=True, retries=None, retry_on_errors=(), body_params=()):
        self.func = func
        self.name = func.__name__.encode('utf8')
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
        kwargs['spoolable_async'] = False
        if self.retries:
            for retries_left in range(self.retries, -1, -1):
                try:
                    kwargs['spoolable_retries'] = retries_left
                    self.func(*args, **kwargs)
                    return
                except self.retry_on_errors:
                    time.sleep(0.001)
            logger.exception('Spooler task %s failed after %d tries' % (self.name, self.retries + 1))
        else:
            self.func(*args, **kwargs)


def spoolable(*, pre_condition=True, retries=None, retry_on_errors=(), body_params=()):
    """
    Decorates a function to make it spoolable if possible and registers it with the spooler.
    All decorated function parameters must be picklable and the function must accept the arguments 
    that define the context in which it is being run, which can be done with a **kwargs catch-all argument:
    - spoolable_async: whether the task is being run asynchronously
    - spoolable_retries: number of retries left before giving up, if any
    :param pre_condition: additional condition needed to use spooler
    :param retries: number of times to retry if `retry_on_errors` trapped
    :param retry_on_errors: errors to trap and retry
    :param body_params: parameter names that can have large values and should use spooler body

    NB: client apps should import `from mtp_common.spoolable_tasks import spoolable` to also register mtp-common tasks
    """

    def decorator(func):
        keyword_kinds = {inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY}
        var_keyword_found = False
        task_arguments_missing = set(Spooler.task_arguments)
        invalid_body_params = set(body_params)
        for name, parameter in inspect.signature(func).parameters.items():
            if parameter.kind == inspect.Parameter.VAR_KEYWORD:
                var_keyword_found = True
            elif name in task_arguments_missing:
                if parameter.kind not in keyword_kinds:
                    raise TypeError('Spoolable task function must accept %s as a keyword argument' % name)
                task_arguments_missing.remove(name)
            elif name in invalid_body_params and parameter.kind in keyword_kinds:
                invalid_body_params.remove(name)
        if task_arguments_missing and not var_keyword_found:
            raise TypeError('Spoolable task function accepts all spooler task arguments')
        if invalid_body_params:
            raise TypeError('Spoolable task body_params must be keyword arguments')

        task = Task(func, pre_condition=pre_condition, retries=retries, retry_on_errors=retry_on_errors,
                    body_params=body_params)
        spooler.register(task)
        return task

    return decorator
