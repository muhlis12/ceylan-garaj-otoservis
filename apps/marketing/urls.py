from django.urls import path
from . import views

urlpatterns = [
    path("wa/open/", views.wa_open, name="wa_open"),
    path("wa/report/", views.wa_report, name="wa_report"),
    path("wa/campaign/", views.wa_campaign, name="wa_campaign"),
]
