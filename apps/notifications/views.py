from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import NotifyTestForm
from .service import send_sms, send_whatsapp


@login_required
def notify_test(request):
    branch_id = request.session.get("active_branch_id")
    if request.method == "POST":
        form = NotifyTestForm(request.POST)
        if form.is_valid():
            if not branch_id:
                messages.error(request, "Once aktif sube secmelisin.")
                return redirect("dashboard")
            channel = form.cleaned_data["channel"]
            to_e164 = form.cleaned_data["to_e164"]
            msg = form.cleaned_data["message"]
            if channel == "SMS":
                log = send_sms(branch_id, to_e164, msg)
            else:
                log = send_whatsapp(branch_id, to_e164, msg)
            if log.status == "SENT":
                messages.success(request, "Gonderildi")
            else:
                messages.error(request, f"Gonderim basarisiz: {log.error}")
            return redirect("notify_test")
    else:
        form = NotifyTestForm()

    return render(request, "notifications/notify_test.html", {"form": form})
