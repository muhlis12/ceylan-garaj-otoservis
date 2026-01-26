from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("switch-branch/<int:branch_id>/", views.switch_branch, name="switch_branch"),
    # Basit API endpointleri
    path("api/plates/search/", views.api_plate_search, name="api_plate_search"),
    path("pwa/manifest.json", views.pwa_manifest, name="pwa_manifest"),
    path("pwa/sw.js", views.pwa_service_worker, name="pwa_sw"),
]
