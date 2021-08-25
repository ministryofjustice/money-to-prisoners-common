"""
This module is a convenience wrapper for `notifications-python-client` which is the official
GOV.UK Notify client made by GDS.

Because email templates can ONLY be created/edited via the GOV.UK Notify control panel,
MTP apps must be able to find and refer to templates by ID. This module intends to make it easier to:
• use the appropriate testing or live GOV.UK Notify account based on Django settings
• ensure that templates exist and have expected content
• refer to templates by name in code (rather than hard-coded IDs)

Please note:
- Only emails are handled currently (no text messages or letters)
- Translation is not supported, because there is no method (yet?) to select templates based on language

TODO:
 - delivery callbacks for basic statistics (needs public api)
 - collect email addresses that permanently fail and keep a bounce list of addresses to ignore?
 - given that plain text emails can be sent, add a method to send rendered Django template (would support translations)?
"""
from mtp_common.notify.client import NotifyClient, TemplateError  # noqa: F401
from mtp_common.notify.templates import NotifyTemplateRegistry  # noqa: F401
