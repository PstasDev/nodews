from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    help = 'Clear all expired sessions and optionally all sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear all sessions, not just expired ones',
        )

    def handle(self, *args, **options):
        if options['all']:
            count = Session.objects.all().count()
            Session.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleared {count} sessions')
            )
        else:
            # Django automatically clears expired sessions
            from django.core.management import call_command
            call_command('clearsessions')
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared expired sessions')
            )