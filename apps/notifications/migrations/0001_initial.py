from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("channel", models.CharField(choices=[("SMS", "SMS"), ("WHATSAPP", "WhatsApp")], max_length=20)),
                ("to", models.CharField(max_length=80)),
                ("message", models.TextField()),
                ("status", models.CharField(choices=[("PENDING", "Beklemede"), ("SENT", "Gonderildi"), ("FAILED", "Basarisiz")], default="PENDING", max_length=20)),
                ("provider", models.CharField(blank=True, max_length=40)),
                ("provider_message_id", models.CharField(blank=True, max_length=120)),
                ("error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.branch")),
            ],
        ),
    ]
