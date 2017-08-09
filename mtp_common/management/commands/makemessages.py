from django.core.management.commands.makemessages import Command as MakeMessagesCommand


class Command(MakeMessagesCommand):
    msgmerge_options = MakeMessagesCommand.msgmerge_options + ['--no-fuzzy-matching']

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--allow-fuzzy', action='store_true', help='Enable fuzzy matching for new entries',
        )

    def handle(self, **options):
        if options['allow_fuzzy']:
            self.msgmerge_options = [option for option in self.msgmerge_options if option != '--no-fuzzy-matching']
        return super().handle(**options)
