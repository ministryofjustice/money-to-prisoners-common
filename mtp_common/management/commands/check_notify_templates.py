import textwrap

from django.core.management import BaseCommand, CommandError

from mtp_common.notify.templates import NotifyTemplateRegistry


class Command(BaseCommand):
    """
    Checks whether all expected templates exist in GOV.UK Notify
    """
    help = textwrap.dedent(__doc__).strip()

    def handle(self, *args, **options):
        verbosity = options['verbosity']
        error, messages = NotifyTemplateRegistry.check_notify_templates()
        if verbosity and messages:
            messages = '\n'.join(messages)
            style = self.style.ERROR if error else self.style.WARNING
            self.stderr.write(style(messages))
        if error:
            raise CommandError('Required GOV.UK Notify templates are missing or have insufficient personalisation')
        elif not messages and verbosity:
            self.stderr.write(self.style.SUCCESS('GOV.UK Notify templates are all exactly as expected'))
