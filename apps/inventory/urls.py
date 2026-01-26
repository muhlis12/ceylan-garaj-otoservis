from django.urls import path
from . import views

urlpatterns = [
    path("parts/", views.parts_list, name="parts_list"),
    path("parts/create/", views.part_create, name="part_create"),
    path("parts/<int:pk>/edit/", views.part_edit, name="part_edit"),

    path("parts/<int:pk>/stock-in/", views.part_stock_in, name="part_stock_in"),
    path("workorders/<int:order_id>/add-part/", views.add_part_to_workorder, name="add_part_to_workorder"),
    path("api/parts/search/", views.api_parts_search, name="api_parts_search"),
    path("api/parts/<int:pk>/", views.api_part_detail, name="api_part_detail"),

]
