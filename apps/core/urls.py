from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("switch-branch/<int:branch_id>/", views.switch_branch, name="switch_branch"),
    # Basit API endpointleri
    path("api/plates/search/", views.api_plate_search, name="api_plate_search"),
    path("pwa/manifest.json", views.pwa_manifest, name="pwa_manifest"),
    path("pwa/sw.js", views.pwa_service_worker, name="pwa_sw"),

    # Kullanıcı Yönetimi (sadece ADMIN)
    path("users/", views.users_list, name="users_list"),
    path("users/new/", views.user_create, name="user_create"),
    path("users/<int:user_id>/edit/", views.user_edit, name="user_edit"),
]
