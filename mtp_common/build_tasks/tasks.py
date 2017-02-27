import contextlib
import functools
import io
import os
import socket
import sys
import threading

from .executor import Context, Tasks, TaskError
from .paths import FileSet, in_dir, paths_for_shell

tasks = Tasks()


@tasks.register('dependencies', 'govuk_template', 'additional_assets', 'bundles', 'collect_static_files',
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
    # context.management_command('runserver', addrport='0:%s' % port, use_reloader=False)
    return context.shell(sys.executable, 'manage.py', 'runserver', '0:%s' % port)


@tasks.register('build')
def serve(context: Context, port=8000, browsersync_port=3000, browsersync_ui_port=3030):
    """
    Starts a development server with auto-building and live-reload
    """
    try:
        from watchdog.observers import Observer
    except ImportError:
        context.pip_command('install', 'watchdog>0.8,<0.9')
        from watchdog.observers import Observer

    from watchdog.events import PatternMatchingEventHandler

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
            context.node_tool('browser-sync', 'reload', '--port=%s' % browsersync_port)

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
                        '--port=%s' % browsersync_port, '--proxy=localhost:%s' % port,
                        '--ui-port=%s' % browsersync_ui_port]
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
        selenium_drivers(context)
        os.environ['RUN_FUNCTIONAL_TESTS'] = '1'
    if webdriver:
        os.environ['WEBDRIVER'] = webdriver
    test_labels = (test_labels or '').split()
    return context.management_command('test', args=test_labels, interactive=False)


@tasks.register(hidden=True)
def create_build_paths(context: Context):
    """
    Creates directories needed for build outputs
    """
    paths = [context.app.asset_build_path, context.app.screenshots_build_path, context.app.collected_assets_path]
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


@tasks.register('node_dependencies', hidden=True)
def selenium_drivers(context: Context):
    """
    Installs selenium drivers
    """
    context.node_tool('selenium-standalone', 'install')


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
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        context.shell('docker-machine', 'ip', 'default')
    host_machine_ip = output.getvalue().strip() or socket.gethostbyname(socket.gethostname())
    args = ()
    if context.verbosity > 1:
        args += ('--verbose',)
    args += ('up', '--build', '--remove-orphans')
    if not context.use_colour:
        args += ('--no-color',)
    context.shell('docker-compose', *args, environment={'HOST_MACHINE_IP': host_machine_ip})


@tasks.register(hidden=True)
def webpack_config(context: Context):
    """
    Generates a webpack.config.js file
    """
    context.write_template('webpack.config.js')


@tasks.register('create_build_paths', 'node_dependencies', 'webpack_config', hidden=True)
def bundle_javascript(context: Context):
    """
    Compiles javascript
    """
    args = ['--bail']
    if context.verbosity > 0:
        args.append('--verbose')
    if not context.use_colour:
        args.append('--no-colors')
    return context.node_tool('webpack', *args)


@tasks.register('create_build_paths', 'node_dependencies', hidden=True)
def bundle_stylesheets(context: Context):
    """
    Compiles stylesheets
    """
    args = [
        '--output', context.app.scss_build_path,
        '--output-style', 'compressed',
    ]
    if context.verbosity == 0:
        args.append('--quiet')
    if not context.use_colour:
        args.append('--no-color')
    for path in context.app.scss_include_paths:
        args.append('--include-path')
        args.append(path)
    return_code = 0
    for source_file in context.app.scss_source_file_set.paths_for_shell(separator=None):
        return_code = context.node_tool('node-sass', *args + [source_file]) or return_code
    return return_code


@tasks.register('bundle_javascript', 'bundle_stylesheets', hidden=True)
def bundles(_: Context):
    """
    Compiles assets
    """


@tasks.register('node_dependencies', hidden=True)
def lint_javascript(context: Context):
    """
    Tests javascript for code and style errors
    """
    args = [
        '--config', os.path.join(context.app.common_templates_path, 'mtp_common', 'build_tasks', 'eslintrc.json'),
        '--format', 'stylish',
    ]
    if context.verbosity == 0:
        args.append('--quiet')
    if not context.use_colour:
        args.append('--no-color')
    args.append(context.app.javascript_source_path)
    return context.node_tool('eslint', *args)


@tasks.register('node_dependencies', hidden=True)
def lint_stylesheets(context: Context):
    """
    Tests stylesheets for code and style errors
    """
    args = [
        '--config', os.path.join(context.app.common_templates_path, 'mtp_common', 'build_tasks', 'sass-lint.yml'),
        '--format', 'stylish',
        '--syntax', 'scss',
    ]
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
def govuk_template(context: Context, version='0.19.2', replace_fonts=True):
    """
    Installs GOV.UK template
    """
    if FileSet(os.path.join(context.app.govuk_templates_path, 'base.html')):
        # NB: check is only on main template and not the assets included
        return
    url = 'https://github.com/alphagov/govuk_template/releases' \
          '/download/v{0}/django_govuk_template-{0}.tgz'.format(version)
    try:
        context.shell('curl --location %(silent)s --output govuk_template.tgz %(url)s' % {
            'silent': '--silent' if context.verbosity == 0 else '',
            'url': url,
        })
        context.shell('tar xzf govuk_template.tgz ./govuk_template')
        rsync_flags = '-avz' if context.verbosity == 2 else '-az'
        context.shell('rsync %s govuk_template/static/ %s/' % (rsync_flags, context.app.asset_build_path))
        context.shell('rsync %s govuk_template/templates/ %s/' % (rsync_flags, context.app.templates_path))
    finally:
        context.shell('rm -rf govuk_template.tgz ./govuk_template')
    if replace_fonts:
        # govuk_template includes .eot font files for IE, but they load relative to current URL not the stylesheet
        # this option removes these files so common's fonts-ie8.css override is used
        context.shell('rm -rf %s/stylesheets/fonts-ie8.css'
                      ' %s/stylesheets/fonts/' % (context.app.asset_build_path, context.app.asset_build_path))


@tasks.register('create_build_paths', hidden=True)
def additional_assets(context: Context):
    """
    Collects assets from GOV.UK frontend toolkit
    """
    rsync_flags = '-avz' if context.verbosity == 2 else '-az'
    for path in context.app.additional_asset_paths:
        context.shell('rsync %s %s %s/' % (rsync_flags, path, context.app.asset_build_path))


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
def make_messages(context: Context):
    """
    Collects text into translation source files
    """
    with in_dir(context.app.django_app_name):
        return context.management_command('makemessages', all=True, keep_pot=True, no_wrap=True)


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
    if push:
        context.shell('tx', 'push', '--source', '--no-interactive')


@tasks.register()
def clean(context: Context, delete_dependencies: bool = False):
    """
    Deletes build outputs
    """
    paths = [context.app.asset_build_path, context.app.collected_assets_path, context.app.govuk_templates_path,
             'docker-compose.yml', 'package.json', 'webpack.config.js']
    context.shell('rm -rf %s' % paths_for_shell(paths))
    context.shell('find %s -name "*.pyc" -or -name __pycache__ -delete' % context.app.django_app_name)

    if delete_dependencies:
        context.info('Cleaning app %s dependencies' % context.app.name)
        paths = ['node_modules', 'venv']
        context.shell('rm -rf %s' % paths_for_shell(paths))
