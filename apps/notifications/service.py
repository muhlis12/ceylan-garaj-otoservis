from django.conf import settings
from django.db.utils import OperationalError

from .models import NotificationLog
from .providers import get_sms_provider, get_whatsapp_provider
from typing import Optional



def _try_create_log(**kwargs):
    """Create NotificationLog if table exists; if not, return None."""
    try:
        return NotificationLog.objects.create(**kwargs)
    except OperationalError:
        return None


def _try_update_log(log: NotificationLog | None, **fields):
    if not log:
        return
    try:
        for k, v in fields.items():
            setattr(log, k, v)
        log.save(update_fields=list(fields.keys()))
    except OperationalError:
        # table missing; ignore
        return


def send_sms(branch_id: int, to_e164: str, message: str):
    """Send SMS and (if possible) store a NotificationLog."""
    log = _try_create_log(
        branch_id=branch_id,
        channel=NotificationLog.CHANNEL_SMS,
        to=to_e164,
        message=message,
        provider=getattr(settings, "NOTIFY_SMS_PROVIDER", "generic"),
    )

    res = get_sms_provider().send_text(to_e164, message)
    if res.ok:
        _try_update_log(log, status=NotificationLog.STATUS_SENT, provider_message_id=res.message_id, error="")
    else:
        _try_update_log(log, status=NotificationLog.STATUS_FAILED, error=res.error)

    return log


def send_whatsapp(branch_id: int, to: str, message: str, template_key: Optional[str] = None) -> bool:
    """
    Backward/forward compatible wrapper.
    triggers.py artık send_whatsapp(branch_id, to=..., message=...) kullanabilir.
    """
    provider = get_whatsapp_provider()
    if not provider:
        return False

    # Provider imzaları farklı olabilir -> güvenli çağrı
    try:
        # bazı provider'lar (to, message) bekler
        return provider.send(to=to, message=message, template_key=template_key)
    except TypeError:
        try:
            # bazı provider'lar (phone, text) bekler
            return provider.send(phone=to, text=message)
        except TypeError:
            # bazı provider'lar (to_phone, body) bekler
            return provider.send(to_phone=to, body=message)