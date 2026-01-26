from django.urls import path
from . import views

urlpatterns = [
    path("", views.customers_list, name="customers_list"),
    path("vehicles/", views.vehicles_list, name="vehicles_list"),

    # ✅ API
    path("api/plate-lookup/", views.plate_lookup, name="plate_lookup"),
     # ✅ PANELDEN YÖNETİM
    path("create/", views.customer_create, name="customer_create"),
    path("<int:pk>/", views.customer_detail, name="customer_detail"),
    path("<int:pk>/edit/", views.customer_edit, name="customer_edit"),
    path("<int:pk>/delete/", views.customer_delete, name="customer_delete"),
]
