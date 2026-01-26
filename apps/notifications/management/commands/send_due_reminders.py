from django.core.management.base import BaseCommand

from apps.notifications.triggers import due_tirehotel_reminders


class Command(BaseCommand):
    help = "Lastik otel due_at yaklasan kayitlar icin WhatsApp hatirlatma gonderir"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7, help="Kac gun icine yaklasanlari gondersin")

    def handle(self, *args, **options):
        days = options.get("days") or 7
        due_tirehotel_reminders(days_ahead=days)
        self.stdout.write(self.style.SUCCESS(f"OK: due reminders checked (days={days})"))
