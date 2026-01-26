from django.urls import path
from . import views

urlpatterns = [
    path("", views.tire_list, name="tire_list"),
    # ✅ create (modal ve sayfa icin)
    path("new/", views.tire_create, name="tire_create"),
    path("create/", views.tire_create, name="tire_create_alias"),

    # ✅ edit/deliver
    path("<int:pk>/edit/", views.tire_edit, name="tire_edit"),
    path("<int:pk>/deliver/", views.tire_deliver, name="tire_deliver"),

    # checkout (hizli 'cikis' islemi)
    path("<int:pk>/checkout/", views.tire_checkout, name="tire_checkout"),

    # print label
    path("<int:pk>/print/", views.tire_print_label, name="tire_print"),
]
