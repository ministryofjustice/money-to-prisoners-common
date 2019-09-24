from django.test import SimpleTestCase
from django.test.utils import modify_settings, override_settings
from django.urls import reverse

from mtp_common.cp_migration.constants import CloudPlatformMigrationMode


@modify_settings(
    MIDDLEWARE={
        'append': 'mtp_common.cp_migration.middleware.CloudPlatformMigrationMiddleware',
    },
)
class CloudPlatformMigrationMiddlewareTestCase(SimpleTestCase):
    """
    Test cases for CloudPlatformMigrationMiddleware.
    """

    def test_absent_mode_gets_ignored(self):
        """
        Test that if settings doesn't define any `CLOUD_PLATFORM_MIGRATION_MODE`, the system
        doesn't do anything.
        """
        response = self.client.get(reverse('dummy'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'DUMMY')

    def test_invalid_mode_gets_ignored(self):
        """
        Test that if settings.CLOUD_PLATFORM_MIGRATION_MODE is not a recognised mode, the system
        doesn't do anything.
        """
        scenarios = [
            'invalid',
            '',
            None,
        ]
        for scenario in scenarios:
            with override_settings(CLOUD_PLATFORM_MIGRATION_MODE=scenario):
                response = self.client.get(reverse('dummy'))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b'DUMMY')

    @override_settings(CLOUD_PLATFORM_MIGRATION_MODE=CloudPlatformMigrationMode.maintenance.name)
    def test_maintenance_mode(self):
        """
        Test that if settings.CLOUD_PLATFORM_MIGRATION_MODE == maintenance, a 503 response is returned.
        """
        response = self.client.get(reverse('dummy'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response['cache-control'],
            'max-age=0, no-cache, no-store, must-revalidate',
        )
        self.assertEqual(
            response['retry-after'],
            '18000',
        )

    @override_settings(
        CLOUD_PLATFORM_MIGRATION_MODE=CloudPlatformMigrationMode.moved.name,
        CLOUD_PLATFORM_MIGRATION_URL='https://new-dummy',
    )
    def test_we_have_moved_mode(self):
        """
        Test that if settings.CLOUD_PLATFORM_MIGRATION_MODE == moved, a 200 response is returned
        with details of the new url.
        """
        full_path = f"{reverse('dummy')}?param=value"
        response = self.client.get(full_path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'https://new-dummy{full_path}')
