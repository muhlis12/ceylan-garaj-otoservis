from datetime import timedelta
from django.utils import timezone

from apps.workorders.models import WorkOrder
from apps.tirehotel.models import TireHotelEntry

from .service import send_whatsapp
from .utils import to_e164_tr


def on_workorder_done(order: WorkOrder) -> None:
    """Is emri Teslim olunca otomatik WhatsApp bildirimi."""
    customer = order.customer
    if not customer or not customer.phone:
        return
    to = to_e164_tr(customer.phone)
    if not to:
        return

    plate = order.plate_text or (order.vehicle.plate if order.vehicle else "-")
    msg = (
        f"Merhaba {customer.full_name}.\n"
        f"Araciniz ({plate}) hazir ✅\n"
        f"Islem: {order.get_kind_display()}\n"
        f"Toplam: {order.grand_total} TL\n"
        f"Tarih: {timezone.localtime(order.updated_at).strftime('%d.%m.%Y %H:%M')}"
    )
    send_whatsapp(order.branch_id, to, msg)


def due_tirehotel_reminders(days_ahead: int = 7):
    """Lastik otel due_at yaklasan kayitlar icin WhatsApp hatirlatma.

    Bu fonksiyon cron/management command ile gunluk calistirilmak icin tasarlandi.
    """
    today = timezone.localdate()
    until = today + timedelta(days=days_ahead)
    qs = (
        TireHotelEntry.objects.filter(is_active=True, due_at__isnull=False, due_at__range=(today, until))
        .select_related("customer")
        .order_by("due_at")
    )
    for x in qs:
        c = x.customer
        if not c or not c.phone:
            continue
        to = to_e164_tr(c.phone)
        if not to:
            continue

        plate = x.plate_text or (x.vehicle.plate if x.vehicle else "-")
        msg = (
            f"Merhaba {c.full_name}.\n"
            f"Lastik otel kaydiniz icin hatirlatma 🔔\n"
            f"Plaka: {plate}\n"
            f"Konum: Depo1 {x.rack_code}/{x.slot_code}\n"
            f"Son tarih: {x.due_at.strftime('%d.%m.%Y')}"
        )
        send_whatsapp(x.branch_id, to, msg)


def on_workorder_created(order: WorkOrder) -> None:
    """İş emri açılınca WhatsApp bildirimi."""
    customer = order.customer
    if not customer or not customer.phone:
        return
    to = to_e164_tr(customer.phone)
    if not to:
        return
    plate = order.plate_text or (order.vehicle.plate if order.vehicle else "-")
    msg = (
        f"Merhaba {customer.full_name}.\n"
        f"Aracınız servise alındı ✅\n"
        f"Plaka: {plate}\n"
        f"İşlem: {order.get_kind_display()}\n"
        f"Tarih: {timezone.localtime(order.created_at).strftime('%d.%m.%Y %H:%M')}"
    )
    send_whatsapp(branch_id=order.branch_id, to=to, message=msg)


def on_tirehotel_created(entry: TireHotelEntry) -> None:
    """Lastik otele alınınca WhatsApp bildirimi."""
    customer = getattr(entry, "customer", None)
    if not customer or not getattr(customer, "phone", None):
        return
    to = to_e164_tr(customer.phone)
    if not to:
        return
    plate = getattr(entry, "plate_text", None) or getattr(entry, "plate", None) or "-"
    loc = f"{getattr(entry,'rack_code','')}/{getattr(entry,'slot_code','')}".strip("/")
    msg = (
        f"Merhaba {customer.full_name}.\n"
        f"Lastikleriniz depoya alındı ✅\n"
        f"Plaka: {plate}\n"
        f"Konum: {loc or '-'}\n"
        f"Tarih: {timezone.localtime(entry.created_at).strftime('%d.%m.%Y %H:%M')}"
    )
    send_whatsapp(branch_id=entry.branch_id, to=to, message=msg)


def on_tirehotel_delivered(entry: TireHotelEntry) -> None:
    """Lastik teslim edilince WhatsApp bildirimi."""
    customer = getattr(entry, "customer", None)
    if not customer or not getattr(customer, "phone", None):
        return
    to = to_e164_tr(customer.phone)
    if not to:
        return
    plate = getattr(entry, "plate_text", None) or getattr(entry, "plate", None) or "-"
    msg = (
        f"Merhaba {customer.full_name}.\n"
        f"Lastikleriniz teslim edildi ✅\n"
        f"Plaka: {plate}\n"
        f"Tarih: {timezone.localtime(timezone.now()).strftime('%d.%m.%Y %H:%M')}"
    )
    send_whatsapp(branch_id=entry.branch_id, to=to, message=msg)
