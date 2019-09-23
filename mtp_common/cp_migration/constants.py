import enum


class CloudPlatformMigrationMode(enum.Enum):
    """
    Enum for the different modes in the Cloud Platform migration.
    """
    maintenance = 'Maintenance'
    moved = 'We have moved'
