from django.urls import path
from django.contrib.auth import views as auth_views
from .views import logout_get

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),

    # POST logout (Django default)
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # ✅ GET logout (bizim yazdığımız kesin çözüm)
    path("logout-get/", logout_get, name="logout_get"),
]
