from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # login/logout
    path("accounts/", include("accounts.urls")),

    # core (dashboard vs.)
    path("", include("apps.core.urls")),  # ✅ BURASI ÖNEMLİ

    # apps
    path("customers/", include("apps.customers.urls")),
    path("workorders/", include("apps.workorders.urls")),
    path("tirehotel/", include("apps.tirehotel.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("reports/", include("apps.reports.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("marketing/", include("apps.marketing.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
