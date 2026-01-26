from django.urls import path
from . import views

urlpatterns = [
    path("test/", views.notify_test, name="notify_test"),
]
