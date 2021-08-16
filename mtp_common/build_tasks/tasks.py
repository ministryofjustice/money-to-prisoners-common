import functools
import os
import sys
import threading

import pkg_resources

from .executor import Context, Tasks, TaskError
from .paths import in_dir, paths_for_shell

tasks = Tasks()


@tasks.register('dependencies', 'additional_assets', 'bundles', 'collect_static_files',
                'take_screenshots', 'compile_messages', 'precompile_python_code', default=True)
def build(_: Context):
    """
    Builds all necessary assets
    """


@tasks.register('build')
def start(context: Context, port=8000):
    """
    Starts a development server
    """
    # NB: if called in the same interpreter, cannot use auto-reloading else all tasks re-run
    # context.management_command('runserver', addrport=f'0:{port}', use_reloader=False)
    return context.shell(sys.executable, 'manage.py', 'runserver', f'0:{port}')


@tasks.register('build')
def serve(context: Context, port=8000, browsersync_port=3000, browsersync_ui_port=3030):
    """
    Starts a development server with auto-building and live-reload
    """
    from watchdog.events import PatternMatchingEventHandler
    from watchdog.observers import Observer

    class RebuildHandler(PatternMatchingEventHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._patterns = ['*.js', '*.scss', '*.html']
            self._ignore_directories = True
            self.builder = None
            self.rebuild_javascript = threading.Event()
            self.rebuild_stylesheets = threading.Event()

        def on_any_event(self, event):
            if self.builder:
                self.builder.cancel()
            extension = event.src_path.rsplit('.', 1)[-1].lower()
            if extension == 'js':
                self.rebuild_javascript.set()
            elif extension == 'scss':
                self.rebuild_stylesheets.set()
            self.builder = threading.Timer(3, self.rebuild)
            self.builder.start()

        def rebuild(self):
            if self.rebuild_javascript.is_set():
                self.rebuild_javascript.clear()
                context.debug('Triggering javascript build')
                bundle_javascript(context)
            if self.rebuild_stylesheets.is_set():
                self.rebuild_stylesheets.clear()
                context.debug('Triggering stylesheet build')
                bundle_stylesheets(context)
            context.debug('Reloading browsers')
            context.node_tool('browser-sync', 'reload', f'--port={browsersync_port}')

    context.info('Watching sources')
    observer = Observer()
    paths = [
        context.app.common_asset_source_path,
        context.app.asset_source_path,
        context.app.common_templates_path,
        context.app.templates_path,
    ]
    handler = RebuildHandler()
    for path in paths:
        observer.schedule(handler, path, recursive=True)
    observer.setDaemon(True)
    observer.start()

    context.info('Starting browser sync')
    browsersync_args = ['start', '--host=localhost', '--no-open',
                        '--logLevel', {0: 'silent', 1: 'info', 2: 'debug'}[context.verbosity],
                        f'--port={browsersync_port}', f'--proxy=localhost:{port}',
                        f'--ui-port={browsersync_ui_port}']
    browsersync = functools.partial(context.node_tool, 'browser-sync', *browsersync_args)
    threading.Thread(target=browsersync, daemon=True).start()

    context.info('Starting web server')
    return start(context, port=port)


@tasks.register('build', 'lint')
def test(context: Context, test_labels=None, functional_tests=False, accessibility_tests=False, webdriver=None):
    """
    Tests the app
    """
    if accessibility_tests:
        functional_tests = True
        os.environ['RUN_ACCESSIBILITY_TESTS'] = '1'
    if functional_tests:
        os.environ['RUN_FUNCTIONAL_TESTS'] = '1'
    if webdriver:
        os.environ['WEBDRIVER'] = webdriver
    test_labels = (test_labels or '').split()
    return context.management_command('test', *test_labels, interactive=False)


@tasks.register(hidden=True)
def create_build_paths(context: Context):
    """
    Creates directories needed for build outputs
    """
    paths = [
        context.app.asset_build_path,
        context.app.scss_build_path,
        context.app.screenshots_build_path,
        context.app.collected_assets_path,
    ]
    for path in filter(None, paths):
        os.makedirs(path, exist_ok=True)


@tasks.register(hidden=True)
def python_dependencies(context: Context, common_path=None):
    """
    Updates python dependencies
    """
    context.pip_command('install', '-r', context.requirements_file)
    if common_path:
        context.pip_command('uninstall', '--yes', 'money-to-prisoners-common')
        context.pip_command('install', '--force-reinstall', '-e', common_path)
        context.shell('rm', '-rf', 'webpack.config.js')  # because it refers to path to common


@tasks.register(hidden=True)
def package_json(context: Context):
    """
    Generates a package.json file
    """
    context.write_template('package.json')


@tasks.register('package_json', hidden=True)
def node_dependencies(context: Context):
    """
    Updates node.js dependencies
    """
    args = ['--loglevel', {0: 'silent', 1: 'warn', 2: 'info'}[context.verbosity]]
    if not context.use_colour:
        args.append('--color false')
    args.append('install')
    return context.shell('npm', *args)


@tasks.register('python_dependencies', 'node_dependencies', hidden=True)
def dependencies(_: Context):
    """
    Updates all dependencies
    """


@tasks.register(hidden=True)
def docker_compose_config(context: Context, port=8000):
    """
    Generates a docker-compose.yml file
    """
    context.write_template('docker-compose.yml', context={
        'port': port,
    })


@tasks.register('docker_compose_config', hidden=True)
def local_docker(context: Context):
    """
    Runs the app in a docker container; for local development only!
    Once performed, `docker-compose up` can be used directly
    """
    args = ()
    if context.verbosity > 1:
        args += ('--verbose',)
    args += ('up', '--build', '--remove-orphans')
    if not context.use_colour:
        args += ('--no-color',)
    context.shell('docker-compose', *args)


@tasks.register(hidden=True)
def webpack_config(context: Context):
    """
    Generates a webpack.config.js file
    """
    context.write_template('webpack.config.js')


@tasks.register('create_build_paths', 'node_dependencies', 'webpack_config', hidden=True)
def bundle_javascript(context: Context, production_bundle=False):
    """
    Compiles javascript
    """
    args = ['--bail']
    if not context.use_colour:
        args.append('--no-color')
    if production_bundle:
        args.append('--mode=production')
    return context.node_tool('webpack', *args)


@tasks.register('create_build_paths', 'node_dependencies', hidden=True)
def bundle_stylesheets(context: Context, production_bundle=False):
    """
    Compiles stylesheets
    """
    def make_output_file(css_path):
        css_name = os.path.basename(css_path)
        base_name = os.path.splitext(css_name)[0]
        return os.path.join(context.app.scss_build_path, f'{base_name}.css')

    style = 'compressed' if production_bundle else 'nested'
    args = [
        'pysassc',  # pysassc entrypoint always removes the first item
        f'--output-style={style}',
    ]
    for path in context.app.scss_include_paths:
        args.append(f'--include-path={path}')

    return_code = 0
    pysassc = pkg_resources.load_entry_point('libsass', 'console_scripts', 'pysassc')
    for source_file in context.app.scss_source_file_set.paths_for_shell(separator=None):
        context.info(f'Building {source_file}')
        pysassc_args = [*args + [source_file, make_output_file(source_file)]]
        return_code = pysassc(pysassc_args) or return_code

    return return_code


@tasks.register('bundle_javascript', 'bundle_stylesheets', hidden=True)
def bundles(_: Context):
    """
    Compiles assets
    """


@tasks.register(hidden=True)
def lint_config(context: Context):
    """
    Generates javasript and stylesheet linting configuration files
    """
    context.write_template('eslintrc.json', path='.eslintrc.json')
    context.write_template('sass-lint.yml', path='.sass-lint.yml')


@tasks.register('node_dependencies', 'lint_config', hidden=True)
def lint_javascript(context: Context):
    """
    Tests javascript for code and style errors
    """
    args = ['--format', 'stylish']
    if context.verbosity == 0:
        args.append('--quiet')
    if not context.use_colour:
        args.append('--no-color')
    args.append(context.app.javascript_source_path)
    return context.node_tool('eslint', *args)


@tasks.register('node_dependencies', 'lint_config', hidden=True)
def lint_stylesheets(context: Context):
    """
    Tests stylesheets for code and style errors
    """
    args = ['--format', 'stylish', '--syntax', 'scss']
    if context.verbosity > 1:
        args.append('--verbose')
    args.append(os.path.join(context.app.scss_source_path, '**', '*.scss'))
    return context.node_tool('sass-lint', *args)


@tasks.register('lint_javascript', 'lint_stylesheets', hidden=True)
def lint(_: Context):
    """
    Tests javascript and stylesheets for code and style errors
    """


@tasks.register('create_build_paths', hidden=True)
def additional_assets(context: Context):
    """
    Collects assets from GOV.UK frontend toolkit
    """
    rsync_flags = '-avz' if context.verbosity == 2 else '-az'
    for path in context.app.additional_asset_paths:
        context.shell(f'rsync {rsync_flags} {path}/ {context.app.asset_build_path}/')


@tasks.register('create_build_paths', hidden=True)
def take_screenshots(context: Context):
    """
    Takes screenshots if special test cases are defined
    """
    context.management_command('takescreenshots', interactive=False)
    collect_static_files(context)


@tasks.register('create_build_paths', hidden=True)
def collect_static_files(context: Context):
    """
    Collects assets for serving from single root
    """
    context.management_command('collectstatic', interactive=False)


@tasks.register(hidden=True)
def precompile_python_code(context: Context):
    """
    Pre-compiles python modules
    """
    from compileall import compile_dir

    kwargs = {}
    if context.verbosity < 2:
        kwargs['quiet'] = True
    compile_dir(context.app.django_app_name, **kwargs)


@tasks.register('python_dependencies')
def make_messages(context: Context, javascript=False, fuzzy=False):
    """
    Collects text into translation source files
    """
    kwargs = {
        'all': True,
        'keep_pot': True,
        'no_wrap': True,
    }
    if fuzzy:
        kwargs['allow_fuzzy'] = True
    if javascript:
        kwargs.update(domain='djangojs', ignore_patterns=['app.js'])
    with in_dir(context.app.django_app_name):
        return context.management_command('makemessages', **kwargs)


@tasks.register('python_dependencies', hidden=True)
def compile_messages(context: Context):
    """
    Compiles translation messages
    """
    with in_dir(context.app.django_app_name):
        return context.management_command('compilemessages')


@tasks.register('python_dependencies')
def translations(context: Context, pull=False, push=False):
    """
    Synchronises translations with transifex.com
    """
    if not (pull or push):
        raise TaskError('Specify whether to push or pull translations')
    if pull:
        context.shell('tx', 'pull')
        make_messages(context, javascript=False)
        make_messages(context, javascript=True)
    if push:
        context.shell('tx', 'push', '--source', '--no-interactive')


@tasks.register()
def clean(context: Context, delete_dependencies: bool = False):
    """
    Deletes build outputs
    """
    paths = [
        context.app.asset_build_path, context.app.collected_assets_path,
        'docker-compose.yml', 'package.json', 'package-lock.json', 'webpack.config.js',
    ]
    context.shell(f'rm -rf {paths_for_shell(paths)}')
    context.shell(f'find {context.app.django_app_name} -name "*.pyc" -or -name __pycache__ -delete')

    if delete_dependencies:
        context.info(f'Cleaning app {context.app.name} dependencies')
        paths = ['node_modules', 'venv']
        context.shell(f'rm -rf {paths_for_shell(paths)}')
