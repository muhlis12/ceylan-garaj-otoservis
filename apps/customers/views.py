from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_GET

from decimal import Decimal

from apps.core.models import Branch, BranchMembership
from .models import Customer, Vehicle


def _can_manage(request, branch_id: int) -> bool:
    role = BranchMembership.objects.filter(user=request.user, branch_id=branch_id, is_active=True).values_list("role", flat=True).first()
    return role in (BranchMembership.ROLE_ADMIN, BranchMembership.ROLE_MANAGER)


def _get_branch_id(request):
    bid = request.session.get("active_branch_id")
    return int(bid) if bid else None



@login_required
def customer_detail(request, pk: int):
    """Müşteri detay: araçlar + iş emirleri + kullanılan parçalar + lastik otel kayıtları"""
    branch_id = _get_branch_id(request)
    customer = get_object_or_404(Customer, pk=pk)

    if branch_id and customer.branch_id != branch_id:
        messages.error(request, "Bu şubede yetkin yok.")
        return redirect("/customers/")

    vehicles = Vehicle.objects.filter(customer=customer).order_by("-created_at")

    # İş emirleri (parçalarla)
    try:
        from apps.workorders.models import WorkOrder
        orders = (
            WorkOrder.objects
            .select_related("vehicle")
            .prefetch_related("parts__part")   # inventory.WorkOrderPart related_name="parts"
            .filter(customer=customer)
            .order_by("-created_at")
        )
    except Exception:
        orders = []

    # Lastik otel kayıtları
    try:
        from apps.tirehotel.models import TireHotelEntry
        tire_entries = TireHotelEntry.objects.filter(customer=customer).order_by("-created_at")
    except Exception:
        tire_entries = []

    # Parça geçmişi (özet)
    parts_summary = []
    try:
        # inventory app varsa
        from apps.inventory.models import WorkOrderPart
        qs_parts = (
            WorkOrderPart.objects
            .select_related("part", "order")
            .filter(order__customer=customer)
            .order_by("-created_at")
        )

        agg = {}
        for p in qs_parts:
            key = f"{p.part.name}"
            if key not in agg:
                agg[key] = {"name": p.part.name, "qty": Decimal("0.00"), "total": Decimal("0.00")}
            agg[key]["qty"] += (p.qty or Decimal("0.00"))
            agg[key]["total"] += (p.line_total or Decimal("0.00"))

        parts_summary = sorted(agg.values(), key=lambda x: (-x["total"], x["name"]))
    except Exception:
        parts_summary = []

    return render(
        request,
        "customers/customer_detail.html",
        {
            "customer": customer,
            "vehicles": vehicles,
            "orders": orders,
            "tire_entries": tire_entries,
            "parts_summary": parts_summary,
        },
    )



@login_required
def customers_list(request):
    branch_id = _get_branch_id(request)
    qs = Customer.objects.all().order_by("-created_at")
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    return render(request, "customers/customers_list.html", {"items": qs})


@login_required
def vehicles_list(request):
    branch_id = _get_branch_id(request)
    qs = Vehicle.objects.select_related("customer").all().order_by("-created_at")
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    return render(request, "customers/vehicles_list.html", {"items": qs})


@require_GET
@login_required
def plate_lookup(request):
    branch_id = _get_branch_id(request)
    q = (request.GET.get("q") or "").strip().upper()

    if not q:
        return JsonResponse({"found": False})

    qs = Vehicle.objects.select_related("customer")
    if branch_id:
        qs = qs.filter(branch_id=branch_id)

    v = qs.filter(plate=q).first()
    if not v:
        return JsonResponse({"found": False})

    return JsonResponse({
        "found": True,
        "vehicle": {"id": v.id, "plate": v.plate, "brand": v.brand, "model": v.model, "year": v.year},
        "customer": {"id": v.customer.id, "full_name": v.customer.full_name, "phone": v.customer.phone, "email": v.customer.email},
    })


@login_required
def customer_create(request):
    branch_id = _get_branch_id(request)
    if not branch_id:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/customers/")

    if not _can_manage(request, branch_id):
        messages.error(request, "Müşteri eklemek için yetkin yok.")
        return redirect("/customers/")

    branch = Branch.objects.get(id=branch_id)

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip()
        plate = (request.POST.get("plate") or "").strip().upper()

        if not full_name:
            messages.error(request, "Ad Soyad zorunlu.")
            return redirect("/customers/")

        c = Customer.objects.create(branch=branch, full_name=full_name, phone=phone, email=email)
        if plate:
            Vehicle.objects.create(branch=branch, customer=c, plate=plate)

        messages.success(request, "Müşteri kaydedildi ✅")
        return redirect("/customers/")

    return redirect("/customers/")


@login_required
def customer_edit(request, pk: int):
    branch_id = _get_branch_id(request)
    c = get_object_or_404(Customer, pk=pk)

    if branch_id and c.branch_id != branch_id:
        messages.error(request, "Bu şubede yetkin yok.")
        return redirect("/customers/")

    if branch_id and not _can_manage(request, branch_id):
        messages.error(request, "Müşteri düzenlemek için yetkin yok.")
        return redirect("/customers/")

    if request.method == "POST":
        c.full_name = request.POST.get("full_name", c.full_name)
        c.phone = request.POST.get("phone", c.phone)
        c.email = request.POST.get("email", c.email)
        c.notes = request.POST.get("notes", c.notes)
        c.save()
        messages.success(request, "Müşteri güncellendi ✅")

    return redirect("/customers/")


@login_required
def customer_delete(request, pk: int):
    branch_id = _get_branch_id(request)
    c = get_object_or_404(Customer, pk=pk)

    if branch_id and c.branch_id != branch_id:
        messages.error(request, "Bu şubede yetkin yok.")
        return redirect("/customers/")

    if branch_id and not _can_manage(request, branch_id):
        messages.error(request, "Müşteri silmek için yetkin yok.")
        return redirect("/customers/")

    if request.method == "POST":
        c.delete()
        messages.success(request, "Müşteri silindi ✅")

    return redirect("/customers/")
