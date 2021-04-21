import inspect
import logging
import pickle

from django.utils.module_loading import autodiscover_modules

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
    __slots__ = ('spooled',)

    def __init__(self, spooled):
        """
        Defines the context in which a spoolable task is running
        :param spooled: whether it is running in the spooler asynchronously
        """
        self.spooled = spooled


class Spooler:
    identifier = b'_mtp'
    spooler_period = 30

    def __init__(self):
        self._registry = {}
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
        if task_name not in self._registry:
            logger.error('Spooler task `%s` not registered', task_name)
            return uwsgi.SPOOL_IGNORE

        task = self._registry[task_name]

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
            if task.context_name:
                kwargs[task.context_name] = Context(spooled=True)
            task.func(*args, **kwargs)
        except:  # noqa: E722,B001
            logger.exception('Spooler task %s failed with uncaught exception', task.name)

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
        if task.name in self._registry:
            logger.warning('%s is already registered as a spooler task', task.name)
        self._registry[task.name] = task

    def schedule(self, task, args, kwargs, **spool_kwargs):
        body = {}
        for body_param in task.body_params:
            if body_param not in kwargs:
                continue
            body[body_param] = kwargs.pop(body_param)
        job = {self.identifier: task.name}
        if args:
            job[b'args'] = pickle.dumps(args)
        if kwargs:
            job[b'kwargs'] = pickle.dumps(kwargs)
        if body:
            job[b'body'] = pickle.dumps(body)
        for key, value in spool_kwargs.items():
            job[key.encode('utf8')] = str(value).encode('utf8')
        uwsgi.spool(job)


spooler = Spooler()
spooler.install()


class Task:
    def __init__(self, func, context_name=None, pre_condition=True, body_params=()):
        self.func = func
        self.name = func.__name__.encode('utf8')
        self.context_name = context_name
        self.pre_condition = pre_condition
        self.body_params = set(body_params)

        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __call__(self, *args, **kwargs):
        if self.pre_condition and spooler.installed:
            # schedule asynchronously
            spooler.schedule(self, args, kwargs)
            return

        # call synchronously
        try:
            if self.context_name:
                kwargs[self.context_name] = Context(spooled=False)
            self.func(*args, **kwargs)
        except:  # noqa: E722,B001
            logger.exception('Spooler task %s failed with uncaught exception', self.name)
            raise


def spoolable(*, pre_condition=True, body_params=()):
    """
    Decorates a function to make it spoolable using uWSGI, but if no spooling mechanism is available,
    the function is called synchronously. All decorated function arguments must be picklable and
    the first annotated with `Context` will receive an object that defines the current execution state.
    Return values are always ignored and all exceptions are caught in spooled mode.
    :param pre_condition: additional condition needed to use spooler
    :param body_params: parameter names that can have large values and should use spooler body
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

        task = Task(func, context_name=context_name, pre_condition=pre_condition, body_params=body_params)
        spooler.register(task)
        return task

    return decorator


def autodiscover_tasks():
    """
    Call this from the file imported by the uWSGI spooler
    """
    autodiscover_modules('tasks', register_to=spooler)
