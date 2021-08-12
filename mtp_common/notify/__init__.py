"""
This module is a convenience wrapper for `notifications-python-client` which is the official
GOV.UK Notify client made by GDS.

Because email templates can ONLY be created/edited via the GOV.UK Notify control panel,
MTP apps must be able to find and refer to templates by ID. This module intends to make it easier to:
• use the appropriate testing or live GOV.UK Notify account based on Django settings
• ensure that templates exist and have expected content
• refer to templates by name in code (rather than hard-coded IDs)

NB: Only emails are handled currently

TODO:
 - testing utils to make mocking easier
 - delivery callbacks
 - collect email addresses that permanently fail?
"""
from mtp_common.notify.client import NotifyClient, TemplateError  # noqa: F401
