from django.shortcuts import redirect
from django.conf import settings

from apps.core.permissions import is_worker_request, is_admin_request


class WorkerLockdownMiddleware:
    """
    Usta kullanıcıyı sadece /workorders/my/ alanında tutar.
    Admin ise serbesttir.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or "/"

        # ✅ slash'lı ve slash'sız login/logout URL'leri muaf olmalı
        exempt_prefixes = (
            "/accounts/login",      "/accounts/login/",
            "/accounts/logout",     "/accounts/logout/",
            "/accounts/logout-get", "/accounts/logout-get/",
            "/admin/", "/static/", "/media/",
        )
        if path.startswith(exempt_prefixes):
            return self.get_response(request)

        # ✅ Usta ise (admin değilse) sadece /workorders/my/ alanında tut
        if request.user.is_authenticated and is_worker_request(request) and not is_admin_request(request):
            worker_home = getattr(settings, "WORKER_HOME_URL", "/workorders/my/")

            # worker_home normalize
            if not worker_home.endswith("/"):
                worker_home += "/"

            # /workorders/my (slash yoksa) -> /workorders/my/
            if path == worker_home[:-1]:
                return redirect(worker_home)

            # worker_home dışına çıkarsa geri gönder
            if not path.startswith(worker_home):
                return redirect(worker_home)

        return self.get_response(request)
