from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone

from apps.customers.models import Customer
from apps.core.models import Branch
from .models import WhatsAppClickLog

def _wa_phone(raw: str) -> str:
    if not raw:
        return ""
    p = raw.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
    if p.startswith("0"):
        p = "9" + p
    if p.startswith("5"):
        p = "90" + p
    return p

@login_required
def wa_open(request):
    branch_id = request.session.get("active_branch_id")
    if not branch_id:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/")

    phone = _wa_phone(request.GET.get("phone", ""))
    text = request.GET.get("text", "")
    mtype = request.GET.get("type", "manual")
    customer_id = request.GET.get("customer_id")
    workorder_id = request.GET.get("workorder_id")

    cust = Customer.objects.filter(id=customer_id).first() if customer_id else None

    # log
    WhatsAppClickLog.objects.create(
        branch_id=branch_id,
        customer=cust,
        phone=phone,
        message_type=mtype,
        workorder_id=int(workorder_id) if workorder_id else None,
        created_by=request.user,
    )

    if not phone:
        return redirect("/workorders/")

    return redirect(f"https://wa.me/{phone}?text={text}")

@login_required
def wa_report(request):
    branch_id = request.session.get("active_branch_id")
    if not branch_id:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/")

    logs = WhatsAppClickLog.objects.filter(branch_id=branch_id).order_by("-created_at")[:500]
    return render(request, "marketing/wa_report.html", {"logs": logs})

@login_required
def wa_campaign(request):
    branch_id = request.session.get("active_branch_id")
    if not branch_id:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/")

    if request.method == "POST":
        phone = _wa_phone(request.POST.get("phone", ""))
        text = (request.POST.get("text", "") or "").strip()
        if not phone or not text:
            messages.error(request, "Telefon ve mesaj zorunlu.")
            return redirect("/marketing/wa/campaign/")

        # log
        WhatsAppClickLog.objects.create(
            branch_id=branch_id,
            phone=phone,
            message_type="campaign",
            created_by=request.user,
        )
        return redirect(f"https://wa.me/{phone}?text={text}")

    return render(request, "marketing/wa_campaign.html")
