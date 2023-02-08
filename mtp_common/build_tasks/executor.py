import configparser
import collections.abc
import functools
import inspect
import os
import subprocess
import sys
import traceback

import django
from django.core.management import call_command
from django.core.management.color import supports_color
import pkg_resources

from .app import App
from .paths import FileSet


class ExecutorError(Exception):
    pass


class ParameterError(ExecutorError):
    pass


class TaskError(ExecutorError):
    pass


class Tasks(collections.abc.MutableMapping):
    """
    Defines a list of tasks
    """

    def __init__(self):
        self._tasks = collections.OrderedDict()
        self._overidden_tasks = collections.defaultdict(list)

    def __repr__(self):
        return f'<Tasks: {len(self)} registered>'

    def __getitem__(self, key):
        return self._tasks[key]

    def __setitem__(self, key, value):
        self._tasks[key] = value

    def __delitem__(self, key):
        del self._tasks[key]

    def __len__(self):
        return len(self._tasks)

    def __iter__(self):
        return iter(self._tasks)

    def register(self, *dependencies, default=False, hidden=False, ignore_return_code=False):
        """
        Decorates a callable to turn it into a task
        """

        def outer(func):
            task = Task(func, *dependencies, default=default, hidden=hidden, ignore_return_code=ignore_return_code)
            overidden_task = self._tasks.pop(task.name, None)
            if overidden_task:
                self._overidden_tasks[task.name].append(overidden_task)
            self[task.name] = task
            return task

        return outer

    def lookup_task(self, task):
        """
        Looks up a task by name or by callable
        """
        if isinstance(task, str):
            try:
                return self[task]
            except KeyError:
                pass
        raise TaskError(f'Unknown task {task}')

    def get_default_task(self):
        """
        Returns the default task if there is only one
        """
        default_tasks = list(filter(lambda task: task.default, self.values()))
        if len(default_tasks) == 1:
            return default_tasks[0]

    def get_overidden_tasks(self, name):
        return self._overidden_tasks[name]


class Task:
    """
    Defines a task and its parameters and dependencies
    """

    def __init__(self, func: callable, *dependencies, default=False, hidden=False, ignore_return_code=False):
        self.name = func.__name__
        self.func = func
        self.dependencies = dependencies
        self.default = default
        self.hidden = hidden
        self.ignore_return_code = ignore_return_code

        self.description = ((inspect.getdoc(func) or '').splitlines() or [''])[0]
        self.parameters = ParameterGroup.from_callable(func, ignored_parameters={'self', 'context'})

        functools.update_wrapper(self, func)

    def __repr__(self):
        parameters = ', '.join(map(repr, self.parameters.values()))
        return f'{self.name}({parameters})'

    def __call__(self, context, **kwargs):
        parameters = self.parameters.to_dict()
        parameters.update(kwargs)
        return_code = self.func(context, **parameters)
        if not (self.ignore_return_code or return_code in (0, None)):
            raise TaskError(f'{self.name} exited with an error')
        return return_code

    @property
    def title_name(self):
        """
        Returns the name of the task for printing
        """
        return self.name.replace('_', ' ')


class ParameterGroup(collections.abc.MutableMapping):
    """
    Defines a set of parameters accepted by a task
    """

    @classmethod
    def from_callable(cls, func, ignored_parameters=frozenset()):
        """
        Reads a function or method signature to produce a set of parameters
        """
        group = cls()
        signature = inspect.signature(func)
        for parameter in signature.parameters.values():
            if parameter.name.startswith('_') or parameter.name in ignored_parameters:
                continue
            parameter = Parameter.from_callable_parameter(parameter)
            group[parameter.name] = parameter
        return group

    @classmethod
    def from_mapping(cls, mapping):
        """
        Produces a set of parameters from a mapping
        """
        group = cls()
        for name, value in mapping.items():
            if name.startswith('_'):
                continue
            group[name] = Parameter(
                name=name,
                value=value,
                constraint=Parameter.constraint_from_type(value),
            )
        return group

    def __init__(self):
        self._parameters = collections.OrderedDict()

    def __repr__(self):
        if not self:
            return '<Parameters>'
        parameters = ', '.join(map(repr, self._parameters.values()))
        return f'<Parameters: {parameters}>'

    def __getitem__(self, key):
        return self._parameters[key]

    def __setitem__(self, key, value):
        self._parameters[key] = value

    def __delitem__(self, key):
        del self._parameters[key]

    def __len__(self):
        return len(self._parameters)

    def __iter__(self):
        return iter(self._parameters)

    def to_dict(self):
        """
        Converts the set of parameters into a dict
        """
        return dict((parameter.name, parameter.value) for parameter in self.values())

    def consume_arguments(self, argument_list):
        """
        Takes arguments from a list while there are parameters that can accept them
        """
        while True:
            argument_count = len(argument_list)
            for parameter in self.values():
                argument_list = parameter.consume_arguments(argument_list)
            if len(argument_list) == argument_count:
                return argument_list

    def update_from(self, mapping):
        """
        Updates the set of parameters from a mapping for keys that already exist
        """
        for key, value in mapping.items():
            if key in self:
                if isinstance(value, Parameter):
                    value = value.value
                self[key].value = value


class Parameter:
    """
    Defines a parameter accepted by a task
    """

    @classmethod
    def from_callable_parameter(cls, parameter):
        """
        Produces a parameter from a function or method
        """
        if parameter.kind == parameter.KEYWORD_ONLY or \
                parameter.kind == parameter.POSITIONAL_OR_KEYWORD and parameter.default is not parameter.empty:
            if parameter.annotation is not parameter.empty:
                constraint = parameter.annotation
            else:
                constraint = Parameter.constraint_from_type(parameter.default)
            return cls(
                name=parameter.name,
                value=parameter.default,
                constraint=constraint,
            )
        else:
            raise ParameterError('Only keyword parameters are supported')

    @classmethod
    def constraint_from_type(cls, value):
        """
        Returns the constraint callable given a value
        """
        if value is None:
            return None
        value_type = type(value)
        if value_type in (str, int, bool):
            return value_type
        raise ParameterError(f'Parameter type cannot be {value_type}')

    @classmethod
    def constraint_from_choices(cls, value_type: type, choices: collections.abc.Sequence):
        """
        Returns a constraint callable based on choices of a given type
        """
        choices_str = ', '.join(map(str, choices))

        def constraint(value):
            value = value_type(value)
            if value not in choices:
                raise ParameterError(f'Argument must be one of {choices_str}')
            return value

        constraint.__name__ = f'choices_{value_type.__name__}'
        constraint.__doc__ = f'choice of {choices_str}'
        return constraint

    def __init__(self, name, value, constraint):
        self._value = None
        self.name = name
        self.constraint = constraint
        self.value = value

    def __repr__(self):
        return f'{self.name}={self.value}'

    @property
    def arg_name(self):
        """
        Returns the name of the parameter as a command line flag
        """
        arg_name = self.name.replace('_', '-')
        if self.constraint is bool and self.value:
            return f'--no-{arg_name}'
        return f'--{arg_name}'

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self.constraint:
            try:
                self._value = self.constraint(value)
            except (ValueError, TypeError):
                raise ParameterError(
                    f'Argument {self.arg_name} needs a value of type {self.constraint.__name__}'
                )
        else:
            self._value = value

    @property
    def description(self):
        constraint = self.constraint
        if not constraint:
            return
        if constraint in (str, int, bool):
            return
        if hasattr(constraint, '__doc__'):
            return ((constraint.__doc__ or '').splitlines() or [''])[0]
        return

    def consume_arguments(self, argument_list):
        """
        Takes arguments from a list while this parameter can accept them
        """
        if len(argument_list) == 0:
            return []
        if argument_list[0] == self.arg_name:
            argument_list = argument_list[1:]
            if self.constraint is bool:
                self.value = not self.value
            else:
                try:
                    value = argument_list.pop(0)
                except IndexError:
                    raise ParameterError(f'Argument {self.arg_name} expects a value')
                self.value = value
        return argument_list


class Context:
    """
    Contains information for running tasks
    """

    def __init__(self, app: App,
                 print_task_names: bool = True,
                 print_task_paths: bool = True,
                 colour: bool = True,
                 django_settings: str = '',
                 requirements_file: str = 'requirements/dev.txt',
                 verbosity: Parameter.constraint_from_choices(int, (0, 1, 2)) = 2):
        self.app = app

        self.print_task_names = print_task_names
        self.print_task_paths = print_task_paths
        self.verbosity = verbosity
        self.use_colour = colour and supports_color()

        self.requirements_file = requirements_file
        self.django_settings = django_settings or f'{app.django_app_name}.settings'
        self._setup_django = False

        self.env = os.environ.copy()
        self.overidden_tasks = []

    def __repr__(self):
        return f'<Context for {self.app.name}>'

    def setup_django(self):
        if self._setup_django:
            return
        if 'DJANGO_SETTINGS_MODULE' not in os.environ:
            os.environ['DJANGO_SETTINGS_MODULE'] = self.django_settings
        django.setup()
        self._setup_django = True

    def red_style(self, text):
        if self.use_colour:
            return f'\x1b[31m{text}\x1b[0m'
        return text

    def green_style(self, text):
        if self.use_colour:
            return f'\x1b[32m{text}\x1b[0m'
        return text

    def yellow_style(self, text):
        if self.use_colour:
            return f'\x1b[33m{text}\x1b[0m'
        return text

    def blue_style(self, text):
        if self.use_colour:
            return f'\x1b[34m{text}\x1b[0m'
        return text

    def print(self, *msg, file=sys.stdout, verbosity=1):
        if self.verbosity >= verbosity:
            print(*msg, file=file)

    def debug(self, *msg, file=sys.stdout):
        self.print(*msg, file=file, verbosity=2)

    def info(self, *msg, file=sys.stdout):
        self.print(*msg, file=file, verbosity=1)

    def error(self, *msg, file=sys.stderr):
        self.print(*[self.red_style(m) for m in msg], file=file, verbosity=0)

    def write_template(self, template_name, context=None, path=None):
        from django.template.loader import get_template

        self.setup_django()
        template = get_template(f'mtp_common/build_tasks/{template_name}')
        template_path = os.path.relpath(template.origin.name, os.getcwd())
        path = path or template_name
        if not FileSet(template_path).modified_since(FileSet(path)):
            return

        self.info(f'Writing {template_name}')
        context = context or {}
        context['app'] = self.app
        content = template.render(context=context)
        with open(path, 'w+') as f:
            f.write(content)

    def pip_command(self, command, *args):
        """
        Runs a pip command
        """
        pip = pkg_resources.load_entry_point('pip', 'console_scripts', 'pip')
        args = [command] + list(args)
        if self.verbosity == 0:
            args.insert(0, '--quiet')
        elif self.verbosity == 2:
            args.insert(0, '--verbose')
        return pip(args)

    def shell(self, command, *args, environment=None, check=True):
        """
        Runs a shell command
        """
        command += ' ' + ' '.join(args)
        command = command.strip()
        self.debug(self.yellow_style(f'$ {command}'))
        env = self.env.copy()
        env.update(environment or {})
        return_code = subprocess.call(command, shell=True, env=env)
        if check and return_code:
            raise TaskError(f'Shell command `{command}` exited with error code: {return_code}')
        return return_code

    def node_tool(self, tool, *args):
        """
        Runs a node tool in a shell
        """
        return self.shell(f'npx {tool}', *args)

    def management_command(self, command, *args, **kwargs):
        """
        Runs a Django management command
        """
        self.setup_django()
        if 'verbosity' not in kwargs:
            kwargs['verbosity'] = self.verbosity
        if not self.use_colour:
            kwargs['no_color'] = False
        self.debug(self.yellow_style(f'$ manage.py {command}'))
        return call_command(command, *args, **kwargs)


class Executor:
    """
    Runs tasks

    Usage:
        exit(Executor(root_path=...).run())
    """
    name = 'MTP build tool'

    def __init__(self, root_path):
        self.root_path = root_path or '.'
        self.context_parameters = ParameterGroup.from_callable(Context.__init__, ignored_parameters={'self', 'app'})
        self.local_config = None
        self.available_tasks = None

    def __repr__(self):
        return f'<{self.name}>'

    def load_tasks(self):
        from .tasks import tasks

        self.available_tasks = tasks
        self.available_tasks['help'] = Task(self.help)

    def load_local_config(self):
        config_parser = configparser.ConfigParser()
        if not config_parser.read(os.path.join(self.root_path, 'setup.cfg')):
            raise ExecutorError('Cannot read configuration from setup.cfg')
        self.local_config = ParameterGroup.from_mapping(config_parser['mtp'])
        # update global parameters
        self.context_parameters.update_from(self.local_config)
        # update task parameter defaults
        for task in self.available_tasks.values():
            task.parameters.update_from(self.local_config)

    def parse_args(self):
        args = sys.argv[1:]
        args = self.context_parameters.consume_arguments(args)
        run_tasks = []
        while True:
            try:
                task_name = args.pop(0)
            except IndexError:
                break
            if task_name.startswith('-'):
                raise ParameterError(f'Unknown flag {task_name}')
            try:
                task = self.available_tasks[task_name]
                args = task.parameters.consume_arguments(args)
                run_tasks.append(task)
            except KeyError:
                raise TaskError(f'Unknown task {task_name}')
        return run_tasks

    def flatten_tasks(self, tasks):
        flattened = []
        for task in tasks:
            if not isinstance(task, Task):
                task = self.available_tasks.lookup_task(task)
            flattened.extend(self.flatten_tasks(task.dependencies))
            flattened.append(task)
        return flattened

    def help(self, context):
        """
        Prints this help (use --verbosity 2 for more details)
        """
        context.info(f'{self.name}\n{sys.argv[0]} [global options] [task] [task options]...\n')

        def print_parameter(prn, p):
            if p.description:
                suffix = f'    - {p.description}'
            else:
                suffix = ''
            if p.constraint is bool:
                prn(f'    {p.arg_name}' + suffix)
            else:
                prn(f'    {p.arg_name} [{p.value}]' + suffix)

        context.info('Global options:')
        for parameter in self.context_parameters.values():
            print_parameter(context.info, parameter)
        context.info()

        context.info('Commands:')
        name_template = '  {0.name:<%d}' % min(max(map(len, self.available_tasks)), 20)
        for task in self.available_tasks.values():
            printer = context.debug if task.hidden else context.info
            if task.description:
                printer((name_template + ' - {0.description}').format(task))
            else:
                printer(name_template.format(task))
            for parameter in task.parameters.values():
                print_parameter(printer, parameter)

    def run_task(self, context, task):
        if task.name != 'help':
            if context.print_task_names:
                context.info(context.blue_style(f'\n> Running {task.name} task...'))
            if context.print_task_paths:
                path = inspect.getfile(task.func)
                line = inspect.getsourcelines(task.func)[1]

                context.info(context.blue_style(f'File "{path}", line {line}'))

        os.chdir(self.root_path)
        context.overidden_tasks = self.available_tasks.get_overidden_tasks(task.name)
        return task(context)

    def run(self):
        cwd = os.getcwd()
        try:
            self.load_tasks()
            self.load_local_config()
            app = App(app=self.local_config['app'].value, root_path=self.root_path)
            tasks = self.parse_args() or [self.available_tasks.get_default_task() or self.available_tasks['help']]
            context = Context(app, **self.context_parameters.to_dict())
            tasks = self.flatten_tasks(tasks)
            run_tasks = set()
            for task in tasks:
                if task.name not in run_tasks:
                    run_tasks.add(task.name)
                    self.run_task(context, task)
            print('Done', file=sys.stderr)
            return 0
        except KeyboardInterrupt:
            print('Cancelled', file=sys.stderr)
            return 1
        except ParameterError as e:
            print(e, file=sys.stderr)
            return 12
        except TaskError as e:
            print(e, file=sys.stderr)
            return 11
        except ExecutorError as e:
            print(e, file=sys.stderr)
            return 10
        except Exception as e:
            print('Uncaught {}'.format(type(e)), file=sys.stderr)
            print(traceback.print_exc(), file=sys.stderr)
            print(e, file=sys.stderr)
            return 100
        finally:
            os.chdir(cwd)
