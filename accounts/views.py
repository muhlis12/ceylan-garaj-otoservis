from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from django.contrib.auth.views import LoginView
from django.urls import reverse

from apps.core.roles import is_admin, is_worker


class RoleBasedLoginView(LoginView):
    """Giriş sonrası rol bazlı yönlendirme.

    - USTA -> /workorders/my/
    - ADMIN -> /
    """

    def get_success_url(self):
        # next parametresi varsa önce onu dene
        next_url = self.get_redirect_url()
        if next_url:
            return next_url

        user = self.request.user
        if is_worker(user) and not is_admin(user):
            return "/workorders/my/"
        return "/"

@require_GET
def logout_get(request):
    logout(request)
    return redirect("/accounts/login/")
