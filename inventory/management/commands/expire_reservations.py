"""
Management command: expire_reservations
Run periodically to release expired stock reservations.

Usage:
  python manage.py expire_reservations

In production, schedule this to run every minute using cron:
  * * * * * cd /path/to/project && python manage.py expire_reservations >> /var/log/freshbasket_cron.log 2>&1
"""
from django.core.management.base import BaseCommand
from inventory.services import expire_reservations


class Command(BaseCommand):
    help = 'Expire stock reservations that have passed their expiry time and release stock back to available pool.'

    def handle(self, *args, **options):
        count = expire_reservations()
        if count:
            self.stdout.write(self.style.SUCCESS(f'Successfully expired {count} reservation(s).'))
        else:
            self.stdout.write('No expired reservations found.')

