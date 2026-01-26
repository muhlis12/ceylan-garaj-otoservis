from django.urls import path
from . import views

urlpatterns = [
    path("revenue/", views.revenue_report, name="revenue_report"),
    path("profit/", views.profit_report, name="profit_report"),
]
