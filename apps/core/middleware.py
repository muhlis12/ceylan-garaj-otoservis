from django.shortcuts import redirect
from django.urls import reverse

EXEMPT_PREFIXES = (
    "/accounts/login/",
    "/accounts/logout/",
    "/accounts/logout-get/",
    "/admin/login/",
    "/static/",
    "/media/",
)

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={path}")

        return self.get_response(request)
