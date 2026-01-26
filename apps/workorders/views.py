from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from apps.customers.models import Customer, Vehicle
from apps.core.models import Branch
from apps.notifications.triggers import on_workorder_done, on_workorder_created
from .models import WorkOrder


@login_required
def workorders_new(request):
    branch_id = request.session.get("active_branch_id")
    qs = (WorkOrder.objects
          .select_related("customer", "vehicle")
          .prefetch_related("parts__part")
          .order_by("-created_at"))
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    return render(request, "workorders/workorders_list.html", {"items": qs, "auto_open_create": True})


@login_required
def workorders_list(request):
    branch_id = request.session.get("active_branch_id")
    qs = (WorkOrder.objects
          .select_related("customer", "vehicle")
          .prefetch_related("parts__part")
          .order_by("-created_at"))
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    return render(request, "workorders/workorders_list.html", {"items": qs})


@login_required
def workorder_create(request):
    branch_id = request.session.get("active_branch_id")
    if not branch_id:
        messages.error(request, "Aktif şube seçili değil. Önce şube seç.")
        return redirect("/workorders/")

    branch = Branch.objects.get(id=branch_id)
    if request.method != "POST":
        return redirect("/workorders/")

    plate = (request.POST.get("plate_text") or "").strip().upper()
    kind = request.POST.get("kind") or WorkOrder.KIND_CAR_WASH
    complaint = (request.POST.get("complaint") or "").strip()
    payment_method = (request.POST.get("payment_method") or "").strip().upper()

    km_raw = (request.POST.get("km") or "").strip()
    km = int(km_raw) if km_raw.isdigit() else None

    v_brand = (request.POST.get("vehicle_brand") or "").strip()
    v_model = (request.POST.get("vehicle_model") or "").strip()

    full_name = (request.POST.get("full_name") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    email = (request.POST.get("email") or "").strip()

    subject = (request.POST.get("subject") or "").strip()

    labor_raw = (request.POST.get("labor_total") or "0").replace(",", ".").strip()
    parts_raw = (request.POST.get("parts_total") or "0").replace(",", ".").strip()
    try:
        labor = Decimal(labor_raw)
    except Exception:
        labor = Decimal("0.00")
    try:
        parts = Decimal(parts_raw)
    except Exception:
        parts = Decimal("0.00")

    if not plate:
        messages.error(request, "Plaka zorunlu.")
        return redirect("/workorders/")

    vehicle = Vehicle.objects.select_related("customer").filter(branch=branch, plate=plate).first()
    customer = vehicle.customer if vehicle else None

    if not vehicle:
        if not full_name:
            messages.error(request, "Bu plaka sistemde yok. Müşteri adını girmen lazım.")
            return redirect("/workorders/")

        customer = Customer.objects.create(
            branch=branch,
            full_name=full_name,
            phone=phone,
            email=email,
        )
        vehicle = Vehicle.objects.create(
            branch=branch,
            customer=customer,
            plate=plate,
            brand=v_brand,
            model=v_model,
        )
    else:
        updated = False
        if v_brand and not vehicle.brand:
            vehicle.brand = v_brand; updated = True
        if v_model and not vehicle.model:
            vehicle.model = v_model; updated = True
        if updated:
            vehicle.save()

    wo = WorkOrder.objects.create(
        branch=branch,
        kind=kind,
        status=WorkOrder.STATUS_WAITING,
        customer=customer,
        vehicle=vehicle,
        plate_text=plate,
        complaint=complaint,
        km=km,
        payment_method=payment_method,
        subject=subject,
        labor_total=labor,
        parts_total=parts,
        grand_total=labor + parts,
    )

    # (Opsiyonel) eski trigger kalsın
    try:
        on_workorder_created(wo)
    except Exception as e:
        print("WhatsApp trigger failed (created):", e)

    messages.success(request, f"İş emri kaydedildi ✅ #{wo.id}")
    return redirect("/workorders/")


@login_required
def workorder_edit(request, pk: int):
    o = get_object_or_404(WorkOrder, pk=pk)
    if request.method == "POST":
        o.status = request.POST.get("status", o.status)

        km_raw = (request.POST.get("km") or "").strip()
        o.km = int(km_raw) if km_raw.isdigit() else None

        o.payment_method = (request.POST.get("payment_method") or "").strip().upper()
        o.complaint = (request.POST.get("complaint") or "").strip()
        o.subject = (request.POST.get("subject") or o.subject).strip()

        labor_raw = (request.POST.get("labor_total") or "").replace(",", ".").strip()
        parts_raw = (request.POST.get("parts_total") or "").replace(",", ".").strip()

        if labor_raw != "":
            try: o.labor_total = Decimal(labor_raw)
            except Exception: pass

        if parts_raw != "":
            try: o.parts_total = Decimal(parts_raw)
            except Exception: pass

        o.grand_total = (o.labor_total or Decimal("0.00")) + (o.parts_total or Decimal("0.00"))

        o.staff_note = (request.POST.get("staff_note") or "").strip()

        if "is_paid" in request.POST:
            o.is_paid = (request.POST.get("is_paid") == "1")

        if o.status == WorkOrder.STATUS_DONE and not o.finished_at:
            o.finished_at = timezone.now()

        o.save()
        messages.success(request, "İş emri güncellendi ✅")

    return redirect("/workorders/")


@login_required
def workorder_done(request, pk: int):
    o = get_object_or_404(WorkOrder, pk=pk)

    if request.method == "POST":
        labor_raw = (request.POST.get("labor_total") or "0").replace(",", ".").strip()
        parts_raw = (request.POST.get("parts_total") or "0").replace(",", ".").strip()

        try: labor = Decimal(labor_raw)
        except Exception: labor = Decimal("0.00")

        try: parts = Decimal(parts_raw)
        except Exception: parts = Decimal("0.00")

        o.labor_total = labor
        o.parts_total = parts
        o.grand_total = labor + parts

        o.status = WorkOrder.STATUS_DONE
        if not o.finished_at:
            o.finished_at = timezone.now()
        o.save()

        try:
            on_workorder_done(o)
        except Exception as e:
            print("WhatsApp trigger failed (done):", e)

        messages.success(request, f"İş emri bitirildi ✅ Toplam: {o.grand_total} ₺")

    return redirect("/workorders/")


@login_required
def workorder_print(request, pk: int):
    o = get_object_or_404(WorkOrder, pk=pk)
    return render(request, "workorders/print_receipt.html", {"o": o})


@login_required
def workorder_invoice_pdf(request, pk: int):
    o = get_object_or_404(WorkOrder, pk=pk)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        return HttpResponse("reportlab yüklü değil.", status=500)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_workorder_{o.id}.pdf"'
    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "CEYLAN GARAJ - İş Emri")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"İş Emri #: {o.id}"); y -= 18
    c.drawString(50, y, f"Plaka: {o.plate_text}"); y -= 18
    c.drawString(50, y, f"Konu: {o.subject or '-'}"); y -= 18
    c.drawString(50, y, f"Tarih: {o.created_at.strftime('%d.%m.%Y %H:%M')}"); y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Tutarlar"); y -= 18
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"İşçilik: {o.labor_total} ₺"); y -= 16
    c.drawString(50, y, f"Parça:   {o.parts_total} ₺"); y -= 16
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Toplam:  {o.grand_total} ₺"); y -= 25

    c.showPage()
    c.save()
    return response


@login_required
def workorder_accept_print(request, pk: int):
    o = get_object_or_404(WorkOrder, pk=pk)
    return render(request, "workorders/accept_receipt.html", {"o": o})


@login_required
def workorder_final_print(request, pk: int):
    o = get_object_or_404(WorkOrder, pk=pk)
    return render(request, "workorders/final_receipt.html", {"o": o})
