from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
import datetime

# ---- Sabit servis şablonları (Usta ekranı) ----
SERVICES_CATALOG = [
    "İç-Dış Yıkama",
    "İç Yıkama",
    "Dış Yıkama",
    "Motor Yıkama",
    "Alt Yıkama",
    "Cilalı Yıkama",
    "Yağ Bakımı",
    "Balata Değişimi",
    "Lastik Tamiri",
    "Lastik Balansı",
]

from apps.core.roles import is_admin, is_worker
from apps.customers.models import Customer, Vehicle
from apps.core.models import Branch
from apps.notifications.triggers import on_workorder_done, on_workorder_created
from .models import WorkOrder
from apps.core.permissions import admin_required, worker_required


def get_default_worker():
    """USTA grubundan ilk aktif kullanıcı."""
    try:
        g = Group.objects.get(name=getattr(settings, "ROLE_WORKER_GROUP", "USTA"))
        return g.user_set.filter(is_active=True).order_by("id").first()
    except Group.DoesNotExist:
        return None


def _plate_of(o: WorkOrder) -> str:
    plate = (getattr(o, "plate_text", "") or "").strip()
    if not plate and getattr(o, "vehicle_id", None) and o.vehicle:
        plate = (o.vehicle.plate or "").strip()
    return (plate or "").upper()


def repeat_visit_info(order: WorkOrder, days: int = 30):
    """Return dict about last DONE workorder for same plate within `days` (excluding itself)."""
    plate = _plate_of(order)
    if not plate:
        return None
    since = timezone.now() - datetime.timedelta(days=days)
    qs = WorkOrder.objects.filter(created_at__gte=since).exclude(pk=order.pk)
    # same branch scope to avoid noise
    if getattr(order, "branch_id", None):
        qs = qs.filter(branch_id=order.branch_id)
    qs = qs.filter(status=WorkOrder.STATUS_DONE).select_related("vehicle").order_by("-created_at")
    # match by plate_text or vehicle plate
    hit = None
    for cand in qs[:50]:
        if _plate_of(cand) == plate:
            hit = cand
            break
    if not hit:
        return None
    delta_days = (timezone.now().date() - hit.created_at.date()).days
    return {"last_id": hit.id, "last_date": hit.created_at, "delta_days": delta_days}





# -------------------------
# ADMIN: Liste
# -------------------------
@login_required
def workorders_new(request):
    branch_id = request.session.get("active_branch_id")
    qs = WorkOrder.objects.select_related("customer", "vehicle").order_by("-created_at")

    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    # --- tekrar geliş uyarısı (son 30 gün içinde DONE varsa) ---
    plates = []
    for it in qs.select_related("vehicle")[:200]:
        p = _plate_of(it)
        if p:
            plates.append(p)
    plates = list(dict.fromkeys(plates))
    since = timezone.now() - datetime.timedelta(days=30)
    recent_done = WorkOrder.objects.filter(status=WorkOrder.STATUS_DONE, created_at__gte=since).select_related("vehicle")
    if branch_id:
        recent_done = recent_done.filter(branch_id=branch_id)
    done_plates = set(_plate_of(x) for x in recent_done[:2000])
    repeat_map = {p: (p in done_plates) for p in plates}

    # Django template icinde dict.get(plate|upper) gibi ifadeler parse edilemiyor.
    # Bu yuzden tekrar-ziyaret bilgisini view tarafinda her kayda isliyoruz.
    items = list(qs)
    for o in items:
        o.is_repeat = bool(repeat_map.get(_plate_of(o)))

    return render(request, "workorders/workorders_list.html", {"items": items})


@login_required
@admin_required
def workorders_list(request):
    # Usta ise kendi ekranına yönlendir
    if is_worker(request.user) and not is_admin(request.user):
        return redirect(getattr(settings, "WORKER_HOME_URL", "/workorders/my/"))

    branch_id = request.session.get("active_branch_id")
    qs = WorkOrder.objects.select_related("customer", "vehicle").order_by("-created_at")

    if branch_id:
        qs = qs.filter(branch_id=branch_id)

    # --- tekrar geliş uyarısı (son 30 gün içinde DONE varsa) ---
    plates = []
    for it in qs.select_related("vehicle")[:200]:
        p = _plate_of(it)
        if p:
            plates.append(p)
    plates = list(dict.fromkeys(plates))

    since = timezone.now() - datetime.timedelta(days=30)
    recent_done = WorkOrder.objects.filter(
        status=WorkOrder.STATUS_DONE,
        created_at__gte=since
    ).select_related("vehicle")

    if branch_id:
        recent_done = recent_done.filter(branch_id=branch_id)

    done_plates = set(_plate_of(x) for x in recent_done[:2000])
    repeat_map = {p: (p in done_plates) for p in plates}

    items = list(qs)

    # ✅ 1) repeat flag
    for o in items:
        o.is_repeat = bool(repeat_map.get(_plate_of(o)))

    # ✅ 2) güvenli plaka display (vehicle None olsa da patlamaz)
    for o in items:
        plate = ""
        try:
            if getattr(o, "vehicle", None) and getattr(o.vehicle, "plate_text", None):
                plate = (o.vehicle.plate_text or "").strip()
            elif getattr(o, "plate_text", None):
                plate = (o.plate_text or "").strip()
            elif getattr(o, "vehicle", None) and getattr(o.vehicle, "plate", None):
                plate = (o.vehicle.plate or "").strip()
        except Exception:
            plate = ""
        o.plate_display = plate

    return render(request, "workorders/workorders_list.html", {"items": items})


# -------------------------
# ADMIN: İş Emri Oluştur
# -------------------------
@login_required
@admin_required
def workorder_create(request):
    if is_worker(request.user) and not is_admin(request.user):
        messages.error(request, "Usta iş emri oluşturamaz.")
        return redirect(getattr(settings, "WORKER_HOME_URL", "/workorders/my/"))

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

        customer = Customer.objects.create(branch=branch, full_name=full_name, phone=phone, email=email)
        vehicle = Vehicle.objects.create(branch=branch, customer=customer, plate=plate, brand=v_brand, model=v_model)
    else:
        updated = False
        if v_brand and not vehicle.brand:
            vehicle.brand = v_brand
            updated = True
        if v_model and not vehicle.model:
            vehicle.model = v_model
            updated = True
        if updated:
            vehicle.save()

    worker = get_default_worker()

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
        assigned_to=worker,
    )

    try:
        on_workorder_created(wo)
    except Exception as e:
        print("WhatsApp trigger failed (created):", e)

    messages.success(request, f"İş emri kaydedildi ✅ #{wo.id}")
    return redirect("/workorders/")


# -------------------------
# ADMIN: Edit / Done
# -------------------------
@login_required
@admin_required
def workorder_edit(request, pk: int):
    if is_worker(request.user) and not is_admin(request.user):
        messages.error(request, "Usta fiyat/güncelleme yapamaz.")
        return redirect(getattr(settings, "WORKER_HOME_URL", "/workorders/my/"))

    o = get_object_or_404(WorkOrder, pk=pk)

    if request.method == "POST":
        o.status = request.POST.get("status", o.status)

        km_raw = (request.POST.get("km") or "").strip()
        o.km = int(km_raw) if km_raw.isdigit() else None

        o.payment_method = (request.POST.get("payment_method") or "").strip().upper()
        o.complaint = (request.POST.get("complaint") or "").strip()
        o.worker_note = (request.POST.get('worker_note') or '').strip()
        o.staff_note = (request.POST.get('staff_note') or '').strip()
        o.subject = (request.POST.get("subject") or o.subject).strip()

        labor_raw = (request.POST.get("labor_total") or "").replace(",", ".").strip()
        parts_raw = (request.POST.get("parts_total") or "").replace(",", ".").strip()

        if labor_raw != "":
            try:
                o.labor_total = Decimal(labor_raw)
            except Exception:
                pass

        if parts_raw != "":
            try:
                o.parts_total = Decimal(parts_raw)
            except Exception:
                pass

        o.grand_total = (o.labor_total or Decimal("0.00")) + (o.parts_total or Decimal("0.00"))

        if "is_paid" in request.POST:
            o.is_paid = (request.POST.get("is_paid") == "1")

        if o.status == WorkOrder.STATUS_DONE and not o.finished_at:
            o.finished_at = timezone.now()

        o.save()
        messages.success(request, "İş emri güncellendi ✅")

    return redirect("/workorders/")


@login_required
@admin_required
def workorder_done(request, pk: int):
    if is_worker(request.user) and not is_admin(request.user):
        messages.error(request, "Usta işi teslim edemez. Admin teslim eder.")
        return redirect(getattr(settings, "WORKER_HOME_URL", "/workorders/my/"))

    o = get_object_or_404(WorkOrder, pk=pk)

    if request.method == "POST":
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


# -------------------------
# PRINT / PDF
# -------------------------
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


# -------------------------
# USTA: Liste + Detay
# -------------------------
@login_required
@worker_required
def my_workorders(request):
    # worker_required zaten kontrol ediyor

    branch_id = request.session.get("active_branch_id")
    qs = WorkOrder.objects.select_related("customer","vehicle").order_by("-created_at")

    if branch_id:
        qs = qs.filter(branch_id=branch_id)

    # ✅ Usta sadece DONE olmayanları görsün (veya sadece assigned)
    qs = qs.exclude(status=WorkOrder.STATUS_DONE)

    # Eğer "tek usta her işi görsün" istiyorsan böyle kalsın.
    # Eğer "sadece assigned_to kendisi" istiyorsan:
    # qs = qs.filter(assigned_to=request.user)
    # --- tekrar geliş uyarısı (son 30 gün içinde DONE varsa) ---
    plates = []
    for it in qs.select_related("vehicle")[:200]:
        p = _plate_of(it)
        if p:
            plates.append(p)
    plates = list(dict.fromkeys(plates))
    since = timezone.now() - datetime.timedelta(days=30)
    recent_done = WorkOrder.objects.filter(status=WorkOrder.STATUS_DONE, created_at__gte=since).select_related("vehicle")
    if branch_id:
        recent_done = recent_done.filter(branch_id=branch_id)
    done_plates = set(_plate_of(x) for x in recent_done[:2000])
    repeat_map = {p: (p in done_plates) for p in plates}

    items = list(qs)
    for o in items:
        o.is_repeat = bool(repeat_map.get(_plate_of(o)))

    # güvenli plaka gösterimi
    for o in items:
        o.plate_display = (o.plate_text or "").strip() or (o.vehicle.plate if getattr(o, "vehicle", None) else "") or "-"

    return render(request, "workorders/my_workorders.html", {"items": items})


@login_required
@worker_required
def worker_workorder_detail(request, pk: int):
    # worker_required zaten kontrol ediyor

    o = get_object_or_404(WorkOrder, pk=pk)
         # ✅ güvenli plaka gösterimi
    plate = ""
    try:
        if getattr(o, "vehicle", None) and getattr(o.vehicle, "plate_text", None):
           plate = (o.vehicle.plate_text or "").strip()
        elif getattr(o, "plate_text", None):
           plate = (o.plate_text or "").strip()
        elif getattr(o, "vehicle", None) and getattr(o.vehicle, "plate", None):
            plate = (o.vehicle.plate or "").strip()
    except Exception:
        plate = ""
    o.plate_display = plate


    repeat_info = repeat_visit_info(o, days=30)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "start":
            o.status = WorkOrder.STATUS_IN_PROGRESS
            if not o.started_at:
                o.started_at = timezone.now()
            o.save()
            messages.success(request, "İşlem başlatıldı ✅")
            return redirect(f"/workorders/my/{o.id}/")

        if action == "save_note":
            services = request.POST.getlist("services")
            if services:
                o.worker_services = "|".join([s.strip() for s in services if s.strip()])
            else:
                o.worker_services = (request.POST.get("worker_services") or "").strip()
            o.worker_note = (request.POST.get("worker_note") or "").strip()
            o.save()
            messages.success(request, "Kaydedildi ✅")
            return redirect(f"/workorders/my/{o.id}/")
        if action == "finish":
            finisher = (request.POST.get("finisher_name") or "").strip()
            if not finisher:
                messages.error(request, "Kalfa adı zorunlu.")
                return redirect(f"/workorders/my/{o.id}/")

            o.worker_finished_by_name = finisher
            o.worker_finished_at = timezone.now()

            # ✅ Usta bitirince DONE yapmayalım. Admin fiyatlandırıp teslim edecek.
            o.status = WorkOrder.STATUS_WAITING_ADMIN
            o.save()

            messages.success(request, "Usta tamamladı ✅ (Admin fiyatlandırıp teslim edecek)")
            return redirect("/workorders/my/")

    return render(request, "workorders/worker_detail.html", {"o": o, "repeat_info": repeat_info, "services_catalog": SERVICES_CATALOG})