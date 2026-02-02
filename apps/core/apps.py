from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self):
        # Otomatik ROLE gruplarını oluştur (ADMIN / USTA).
        # Kullanıcı yönetimi ekranında grup listesi boş kalmasın ve rol kontrolü çalışsın.
        from django.conf import settings
        from django.db.models.signals import post_migrate

        def ensure_role_groups(sender, **kwargs):
            try:
                from django.contrib.auth.models import Group
            except Exception:
                return

            admin_group = getattr(settings, "ROLE_ADMIN_GROUP", "ADMIN")
            worker_group = getattr(settings, "ROLE_WORKER_GROUP", "USTA")

            Group.objects.get_or_create(name=admin_group)
            Group.objects.get_or_create(name=worker_group)

        post_migrate.connect(ensure_role_groups, sender=self)
