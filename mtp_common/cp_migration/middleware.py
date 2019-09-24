from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

from mtp_common.auth.models import MojAnonymousUser

from mtp_common.cp_migration.views import get_maintenance_response, get_we_have_moved_response
from mtp_common.cp_migration.constants import CloudPlatformMigrationMode


def _get_migration_mode():
    try:
        return CloudPlatformMigrationMode[settings.CLOUD_PLATFORM_MIGRATION_MODE]
    except (AttributeError, KeyError):
        pass

    return None


class CloudPlatformMigrationMiddleware(MiddlewareMixin):
    """
    When migrating to Cloud Platform, this middleware overrides the default behaviour
    and returns either a:
    - maintenance page saying that the site offline whilst we update it
    - a page saying that we have moved to a new url.
    """
    def __init__(self, *args, **kwargs):
        """
        Cache the migration mode so that we don't have to calculate it all the time.
        """
        self.migration_mode = _get_migration_mode()
        super().__init__(*args, **kwargs)

    def process_request(self, request):
        """
        Returns an ad-hoc response if in maintenance or 'we have moved' mode;
        otherwise, continue as usual.

        It fails silently if no mode is specified or the actual value is not
        one recognised by the system.
        """
        if not self.migration_mode:
            return None

        if self.migration_mode == CloudPlatformMigrationMode.maintenance:
            request.user = MojAnonymousUser()
            return get_maintenance_response(request)

        if self.migration_mode == CloudPlatformMigrationMode.moved:
            request.user = MojAnonymousUser()
            return get_we_have_moved_response(request)

        return None
