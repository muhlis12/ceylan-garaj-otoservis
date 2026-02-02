from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.http import HttpResponse

from apps.core.models import Branch
from apps.customers.models import Customer, Vehicle
from .models import TireHotelEntry
from .forms import TireHotelCreateForm
from apps.notifications.triggers import on_tirehotel_created, on_tirehotel_delivered


@login_required
def tire_list(request):
    branch_id = request.session.get("active_branch_id")
    qs = TireHotelEntry.objects.all().order_by("-created_at")
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    return render(request, "tirehotel/tire_list.html", {"items": qs})


@login_required
def tire_create(request):
    """Yeni lastik otel kaydi.

    - /tirehotel/new/ : sayfa
    - /tirehotel/create/ : modal alias

    Plaka uzerinden arac/musteri eslestirir; yoksa yeni musteri+arac olusturur.
    """
    branch_id = request.session.get("active_branch_id")
    if not branch_id:
        messages.error(request, "Once aktif sube secmelisin.")
        return redirect("dashboard")

    branch = Branch.objects.get(id=branch_id)

    if request.method == "POST":
        # Modal formdan gelebilecek alternatif isimleri normalize et
        post = request.POST.copy()
        # plate_text
        if not post.get("plate_text") and post.get("plate"):
            post["plate_text"] = post.get("plate")
        # price
        if not post.get("price") and post.get("fee"):
            post["price"] = post.get("fee")
        # rack/slot
        if not post.get("rack_code") and post.get("rack"):
            post["rack_code"] = f"R{post.get('rack')}" if post.get("rack") and not str(post.get('rack')).startswith("R") else post.get("rack")
        if not post.get("slot_code") and post.get("slot"):
            post["slot_code"] = f"G{post.get('slot')}" if post.get("slot") and not str(post.get('slot')).startswith("G") else post.get("slot")

        # ✅ Zorunlu alanlar gelmiyorsa default ver (hızlı kayıt için)
        if not post.get("rack_code"):
            post["rack_code"] = "R1"
        if not post.get("slot_code"):
            post["slot_code"] = "G1"
        if not post.get("price"):
            post["price"] = "0"
        # brand/size from tire_text (best-effort)
        if not post.get("brand") and post.get("tire_text"):
            post["brand"] = post.get("tire_text")

        form = TireHotelCreateForm(post, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.branch = branch

            plate = (obj.plate_text or "").strip().upper()
            obj.plate_text = plate

            # musteri/arac eslestirme
            if plate:
                v = Vehicle.objects.select_related("customer").filter(branch=branch, plate=plate).first()
                if v:
                    obj.vehicle = v
                    obj.customer = v.customer
                else:
                    full_name = (post.get("full_name") or "").strip()
                    phone = (post.get("phone") or "").strip()
                    email = (post.get("email") or "").strip()
                    if full_name:
                        c = Customer.objects.create(branch=branch, full_name=full_name, phone=phone, email=email)
                        v = Vehicle.objects.create(branch=branch, customer=c, plate=plate)
                        obj.customer = c
                        obj.vehicle = v

            if not obj.received_at:
                obj.received_at = timezone.localdate()
            obj.is_active = True
            obj.save()
            messages.success(request, "Lastik otel kaydi olusturuldu.")
            on_tirehotel_created(obj)
            return redirect("tire_list")
        else:
            messages.error(request, "Form hatasi: " + str(form.errors))
            return redirect("tire_list")

    # GET: sayfa formu
    form = TireHotelCreateForm()
    return render(request, "tirehotel/tire_create.html", {"form": form})


@login_required
def tire_checkout(request, pk: int):
    obj = get_object_or_404(TireHotelEntry, pk=pk)
    obj.is_active = False
    obj.released_at = timezone.localdate()
    obj.save(update_fields=["is_active", "released_at"])
    messages.success(request, "Cikis yapildi.")
    on_tirehotel_delivered(obj)
    return redirect("tire_list")


@login_required
def tire_deliver(request, pk: int):
    """Panelden teslim."""
    if request.method == "POST":
        return tire_checkout(request, pk)
    return redirect("tire_list")


@login_required
def tire_edit(request, pk: int):
    """Panelden duzenle (modal)."""
    obj = get_object_or_404(TireHotelEntry, pk=pk)
    if request.method == "POST":
        post = request.POST
        obj.plate_text = (post.get("plate_text") or post.get("plate") or obj.plate_text).strip().upper()
        obj.season = post.get("season", obj.season)
        obj.brand = post.get("brand", obj.brand)
        obj.size = post.get("size", obj.size)
        qty_raw = (post.get("qty") or "").strip()
        if qty_raw.isdigit():
            obj.qty = int(qty_raw)
        rack = post.get("rack_code") or post.get("rack")
        slot = post.get("slot_code") or post.get("slot")
        if rack:
            obj.rack_code = rack
        if slot:
            obj.slot_code = slot
        price_raw = (post.get("price") or post.get("fee") or "").replace(",", ".").strip()
        try:
            if price_raw:
                obj.price = float(price_raw)
        except Exception:
            pass
        obj.notes = post.get("notes", post.get("note", obj.notes))
        # due_at
        if post.get("due_at"):
            try:
                obj.due_at = datetime.fromisoformat(post.get("due_at")).date()
            except Exception:
                pass
        obj.save()
        messages.success(request, "Lastik kaydi guncellendi ✅")
    return redirect("tire_list")


@login_required
def tire_print_label(request, pk: int):
    """Yazici icin etiket / print sayfasi."""
    obj = get_object_or_404(TireHotelEntry, pk=pk)
    return render(request, "tirehotel/print_label.html", {"t": obj})
