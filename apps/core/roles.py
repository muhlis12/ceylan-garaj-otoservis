from django.conf import settings

def is_admin(user) -> bool:
    if not user.is_authenticated:
        return False
    admin_group = getattr(settings, "ROLE_ADMIN_GROUP", "ADMIN")
    # Grup adları bazen farklı büyük/küçük harflerle oluşturulabiliyor (ADMIN/Admin/admin).
    return user.is_superuser or user.groups.filter(name__iexact=admin_group).exists()

def is_worker(user) -> bool:
    if not user.is_authenticated:
        return False
    worker_group = getattr(settings, "ROLE_WORKER_GROUP", "USTA")
    return user.groups.filter(name__iexact=worker_group).exists()
