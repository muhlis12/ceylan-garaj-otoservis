from django.urls import path
from . import views

urlpatterns = [
    path("", views.workorders_list, name="workorders_list"),
    path("new/", views.workorders_new, name="workorders_new"),
    path("create/", views.workorder_create, name="workorder_create"),

    # işlemler
    path("<int:pk>/done/", views.workorder_done, name="workorder_done"),
    path("<int:pk>/edit/", views.workorder_edit, name="workorder_edit"),

    # print
    path("<int:pk>/print/", views.workorder_print, name="workorder_print"),
    path("<int:pk>/invoice.pdf", views.workorder_invoice_pdf, name="workorder_invoice_pdf"),
    path("<int:pk>/accept/print/", views.workorder_accept_print, name="workorder_accept_print"),
    path("<int:pk>/final/print/", views.workorder_final_print, name="workorder_final_print"),

    # ✅ usta ekranı
    path("my/", views.my_workorders, name="my_workorders"),
    path("my/<int:pk>/", views.worker_workorder_detail, name="worker_detail"),
]
