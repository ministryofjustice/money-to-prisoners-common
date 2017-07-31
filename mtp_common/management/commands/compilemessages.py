from django.core.management.commands.compilemessages import Command as CompileMessagesCommand


class Command(CompileMessagesCommand):
    program_options = [option for option in CompileMessagesCommand.program_options if option != '--check-format']

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--check-format', action='store_true', help='Enable message format checking',
        )

    def handle(self, **options):
        if options['check_format']:
            self.program_options = self.program_options + ['--check-format']
        return super().handle(**options)
