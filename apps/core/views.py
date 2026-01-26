from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.http import JsonResponse

from .models import Branch, BranchMembership
from apps.workorders.models import WorkOrder
from apps.tirehotel.models import TireHotelEntry
from apps.customers.models import Vehicle


@login_required
def dashboard(request):
    """Gelen siraya gore 'Acik' isleri gosterir."""
    memberships = BranchMembership.objects.filter(user=request.user, is_active=True, branch__is_active=True)
    branches = [m.branch for m in memberships]

    # Ilk kez giriyorsa aktif subeyi atayalim
    if request.session.get("active_branch_id") is None and branches:
        request.session["active_branch_id"] = branches[0].id

    active_branch_id = request.session.get("active_branch_id")
    active_branch = None
    if active_branch_id:
        try:
            active_branch = Branch.objects.get(id=active_branch_id)
        except Branch.DoesNotExist:
            active_branch = None

    qs_work = WorkOrder.objects.all().order_by("status", "created_at")
    qs_tire = TireHotelEntry.objects.all().order_by("-created_at")

    if active_branch:
        qs_work = qs_work.filter(branch=active_branch)
        qs_tire = qs_tire.filter(branch=active_branch)

    today = timezone.localdate()
    work_today = qs_work.filter(created_at__date=today).count()
    open_work = qs_work.exclude(status=WorkOrder.STATUS_DONE).count()
    tire_active = qs_tire.filter(is_active=True).count()

    ctx = {
        "branches": branches,
        "active_branch": active_branch,
        "work_today": work_today,
        "open_work": open_work,
        "tire_active": tire_active,
    }
    return render(request, "base/dashboard.html", ctx)


@login_required
def switch_branch(request, branch_id: int):
    """Aktif subeyi degistirir.

    Navbar dropdown'dan cagirilir. Kullanici o subeye uye ise session'a yazar.
    """
    has_access = BranchMembership.objects.filter(user=request.user, branch_id=branch_id, is_active=True).exists()
    if has_access:
        request.session["active_branch_id"] = int(branch_id)
    return redirect(request.META.get("HTTP_REFERER", "/"))


def pwa_manifest(request):
    # Basit manifest; renkleri istersen siyah-kirmizi-beyaz uyarladik.
    from django.http import JsonResponse

    data = {
        "name": "OtoServis Pro",
        "short_name": "OtoServis",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#000000",
        "theme_color": "#b00020",
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    return JsonResponse(data)


def pwa_service_worker(request):
    from django.http import HttpResponse

    js = """
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  // Network-first basit strateji
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
"""
    return HttpResponse(js, content_type="application/javascript")


@login_required
def api_plate_search(request):
    """Plaka hizli arama.

    Web UI icin basit autocomplete endpointi.
    GET /api/plates/search/?q=06ABC123
    """

    branch_id = request.session.get("active_branch_id")
    q = (request.GET.get("q") or "").strip().upper()
    if not branch_id or len(q) < 2:
        return JsonResponse({"items": []})

    qs = Vehicle.objects.filter(branch_id=branch_id, plate__icontains=q).select_related("customer")
    items = []
    for v in qs.order_by("plate")[:10]:
        items.append(
            {
                "id": v.id,
                "plate": v.plate,
                "customer_name": v.customer.full_name if v.customer else "",
                "customer_phone": v.customer.phone if v.customer else "",
            }
        )
    return JsonResponse({"items": items})

