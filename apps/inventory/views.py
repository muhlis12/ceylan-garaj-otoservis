from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.db import models

from apps.core.models import Branch
from .models import Part, StockMove
from .services import get_stock
from apps.workorders.models import WorkOrder
from .models import Part, StockMove, WorkOrderPart





def _get_branch(request):
    branch_id = request.session.get("active_branch_id")
    if not branch_id:
        return None
    return Branch.objects.filter(id=branch_id).first()


@login_required
def parts_list(request):
    branch = _get_branch(request)
    if not branch:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/")

    parts = Part.objects.filter(branch=branch, is_active=True).order_by("name")
    rows = []
    for p in parts:
        rows.append({
            "obj": p,
            "stock": get_stock(branch.id, p.id),
        })

    return render(request, "inventory/parts_list.html", {
        "rows": rows,
        "branch": branch,
    })


@login_required
@transaction.atomic
def part_create(request):
    branch = _get_branch(request)
    if not branch:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/inventory/parts/")

    if request.method != "POST":
        return redirect("/inventory/parts/")

    name = (request.POST.get("name") or "").strip()
    sku = (request.POST.get("sku") or "").strip()
    barcode = (request.POST.get("barcode") or "").strip()
    brand = (request.POST.get("brand") or "").strip()
    unit = (request.POST.get("unit") or "adet").strip()

    sale_price_raw = (request.POST.get("sale_price") or "0").replace(",", ".")
    cost_price_raw = (request.POST.get("cost_price") or "0").replace(",", ".")

    try:
        sale_price = Decimal(sale_price_raw)
    except:
        sale_price = Decimal("0.00")
    try:
        cost_price = Decimal(cost_price_raw)
    except:
        cost_price = Decimal("0.00")

    min_stock_raw = (request.POST.get("min_stock") or "0").replace(",", ".")
    try:
        min_stock = Decimal(min_stock_raw)
    except:
        min_stock = Decimal("0.00")

    if not name:
        messages.error(request, "Parça adı zorunlu.")
        return redirect("/inventory/parts/")

    p = Part.objects.create(
        branch=branch,
        name=name,
        sku=sku,
        barcode=barcode,
        brand=brand,
        unit=unit,
        sale_price=sale_price,
        cost_price=cost_price,
        min_stock=min_stock,
    )
    # barcode otomatik üretim (modelde varsa)
    try:
        p.ensure_barcode()
    except Exception:
        pass

    messages.success(request, "Parça kaydedildi ✅")
    return redirect("/inventory/parts/")


@login_required
@transaction.atomic
def part_edit(request, pk:int):
    branch = _get_branch(request)
    if not branch:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/inventory/parts/")

    p = get_object_or_404(Part, pk=pk, branch=branch)

    if request.method != "POST":
        return redirect("/inventory/parts/")

    p.name = (request.POST.get("name") or p.name).strip()
    p.sku = (request.POST.get("sku") or p.sku).strip()
    p.barcode = (request.POST.get("barcode") or p.barcode).strip()
    p.brand = (request.POST.get("brand") or p.brand).strip()
    p.unit = (request.POST.get("unit") or p.unit).strip()

    sale_price_raw = (request.POST.get("sale_price") or str(p.sale_price)).replace(",", ".")
    cost_price_raw = (request.POST.get("cost_price") or str(p.cost_price)).replace(",", ".")

    try:
        p.sale_price = Decimal(sale_price_raw)
    except:
        pass
    try:
        p.cost_price = Decimal(cost_price_raw)
    except:
        pass

    min_stock_raw = (request.POST.get("min_stock") or str(p.min_stock)).replace(",", ".")
    try:
        p.min_stock = Decimal(min_stock_raw)
    except:
        pass

    p.save()
    messages.success(request, "Parça güncellendi ✅")
    return redirect("/inventory/parts/")


@login_required
@transaction.atomic
def part_stock_in(request, pk:int):
    branch = _get_branch(request)
    if not branch:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/inventory/parts/")

    p = get_object_or_404(Part, pk=pk, branch=branch)

    if request.method != "POST":
        return redirect("/inventory/parts/")

    qty_raw = (request.POST.get("qty") or "0").replace(",", ".")
    unit_cost_raw = (request.POST.get("unit_cost") or "0").replace(",", ".")
    note = (request.POST.get("note") or "").strip()

    try:
        qty = Decimal(qty_raw)
    except:
        qty = Decimal("0")
    try:
        unit_cost = Decimal(unit_cost_raw)
    except:
        unit_cost = Decimal("0")

    if qty <= 0:
        messages.error(request, "Stok girişi için adet > 0 olmalı.")
        return redirect("/inventory/parts/")

    StockMove.objects.create(
        branch=branch,
        part=p,
        move_type=StockMove.TYPE_IN,
        qty=qty,
        unit_cost=unit_cost,
        note=note or "Stok girişi",
    )

    messages.success(request, "Stok girişi yapıldı ✅")
    return redirect("/inventory/parts/")
    
@login_required
@transaction.atomic
def add_part_to_workorder(request, order_id: int):
    if request.method != "POST":
        return redirect("/workorders/")

    branch_id = request.session.get("active_branch_id")
    if not branch_id:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/workorders/")

    order = get_object_or_404(WorkOrder, id=order_id, branch_id=branch_id)

    part_id = int(request.POST.get("part_id"))
    qty_raw = (request.POST.get("qty") or "1").replace(",", ".").strip()
    unit_price_raw = (request.POST.get("unit_price") or "0").replace(",", ".").strip()

    try:
        qty = Decimal(qty_raw)
    except:
        qty = Decimal("1")

    try:
        unit_price = Decimal(unit_price_raw)
    except:
        unit_price = Decimal("0.00")

    part = get_object_or_404(Part, id=part_id, branch_id=branch_id, is_active=True)

    # ✅ stok kontrol
    stock = get_stock(branch_id, part.id)
    if stock < qty:
        messages.error(request, f"Stok yetersiz! Mevcut: {stock} / İstenen: {qty}")
        return redirect("/workorders/")

    # ✅ iş emri parça satırı oluştur
    wop = WorkOrderPart.objects.create(order=order, part=part, qty=qty, unit_price=unit_price, line_total=qty * unit_price)

    # ✅ stok düş (OUT)
    StockMove.objects.create(
        branch_id=branch_id,
        part=part,
        move_type=StockMove.TYPE_OUT,
        qty=qty,
        unit_cost=part.cost_price or Decimal("0.00"),
        note=f"WorkOrder #{order.id}",
        workorder=order,
    )

    # ✅ totals güncelle
    parts_total = sum((p.line_total for p in order.parts.all()), Decimal("0.00"))
    order.parts_total = parts_total
    order.grand_total = (order.labor_total or Decimal("0.00")) + parts_total
    order.save()

    messages.success(request, "Parça eklendi ✅ Stok düşüldü ✅")
    return redirect("/workorders/")
    
 
@require_GET
@login_required
def api_parts_search(request):
    """
    Select2: /inventory/api/parts/search/?q=filtre
    JSON: {results:[{id,text,barcode,price,stock},...]}
    """
    branch_id = request.session.get("active_branch_id")
    q = (request.GET.get("q") or "").strip()

    if not branch_id:
        return JsonResponse({"results": []})

    qs = Part.objects.filter(branch_id=branch_id, is_active=True)

    if q:
        qs = qs.filter(
            models.Q(name__icontains=q) |
            models.Q(barcode__icontains=q) |
            models.Q(sku__icontains=q)
        )

    qs = qs.order_by("name")[:30]

    results = []
    for p in qs:
        results.append({
            "id": p.id,
            "text": f"{p.name} ({p.brand})" if p.brand else p.name,
            "barcode": p.barcode,
            "price": str(p.sale_price),
            "stock": str(get_stock(branch_id, p.id)),
        })

    return JsonResponse({"results": results})


@require_GET
def api_part_detail(request, pk: int):
    """
    /inventory/api/parts/<id>/
    """
    branch_id = request.session.get("active_branch_id")
    if not branch_id:
        return JsonResponse({"ok": False}, status=400)

    p = Part.objects.filter(id=pk, branch_id=branch_id, is_active=True).first()
    if not p:
        return JsonResponse({"ok": False}, status=404)

    return JsonResponse({
        "ok": True,
        "id": p.id,
        "name": p.name,
        "barcode": p.barcode,
        "sale_price": str(p.sale_price),
        "stock": str(get_stock(branch_id, p.id)),
    })