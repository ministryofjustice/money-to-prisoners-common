import os

import pkg_resources

from .paths import FileSet


class App:
    """
    Describes an MTP app and returns derrived information and paths
    """
    collected_assets_path = 'static'
    node_modules_path = 'node_modules'

    def __init__(self, app, root_path):
        self.name = app
        self.root_path = root_path

    def __repr__(self):
        return f'<App: {self.name}>'

    @property
    def django_app_name(self):
        return f'mtp_{self.name}'

    @property
    def hyphenated_name(self):
        return self.name.replace('_', '-')

    @property
    def complete_hyphenated_name(self):
        return f'money-to-prisoners-{self.hyphenated_name}'

    @property
    def title(self):
        return self.name.replace('_', ' ').title()

    @property
    def common_version(self):
        from mtp_common import __version__

        return __version__

    @property
    def asset_source_path(self):
        return os.path.join(self.django_app_name, 'assets-src')

    @property
    def javascript_source_path(self):
        return self.asset_source_path

    @property
    def scss_source_path(self):
        return self.asset_source_path

    @property
    def scss_source_file_set(self):
        if self.name == 'api':
            return FileSet('*.scss', root=self.scss_source_path)
        return FileSet('app.scss', root=self.scss_source_path)

    @property
    def asset_build_path(self):
        return os.path.join(self.django_app_name, 'assets')

    @property
    def images_build_path(self):
        return os.path.join(self.asset_build_path, 'images')

    @property
    def screenshots_build_path(self):
        return os.path.join(self.images_build_path, 'screenshots')

    @property
    def javascript_build_path(self):
        return self.asset_build_path

    @property
    def scss_build_path(self):
        return self.asset_build_path

    @property
    def templates_path(self):
        return os.path.join(self.django_app_name, 'templates')

    @property
    def common_path(self):
        try:
            path = pkg_resources.get_distribution('money-to-prisoners-common').location
        except (AttributeError, pkg_resources.DistributionNotFound):
            return None
        return os.path.relpath(os.path.join(path, 'mtp_common'), self.root_path)

    @property
    def common_asset_source_path(self):
        return os.path.join(self.common_path, 'assets-src')

    @property
    def common_javascript_source_path(self):
        return self.common_asset_source_path

    @property
    def common_scss_source_path(self):
        return self.common_asset_source_path

    @property
    def common_templates_path(self):
        return os.path.join(self.common_path, 'templates')

    @property
    def additional_asset_paths(self):
        yield os.path.join(self.node_modules_path, 'govuk-frontend/govuk/assets')

    @property
    def javascript_include_paths(self):
        yield self.common_javascript_source_path
        yield self.javascript_source_path

    @property
    def scss_include_paths(self):
        yield self.node_modules_path
        yield self.common_scss_source_path
        yield self.scss_source_path
