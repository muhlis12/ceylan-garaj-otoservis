"""Notification provider layer.

WhatsApp: Resmi API (Meta WhatsApp Cloud API) icin iskelet
SMS: Provider'a gore degisecek generic iskelet

Uretimde: requests ile API'ye cagrilar atilir. Burada sadece arayuz + ornek payloadlari var.
"""

from dataclasses import dataclass
from typing import Optional

from django.conf import settings
import requests


@dataclass
class SendResult:
    ok: bool
    message_id: str = ""
    error: str = ""


class WhatsAppProvider:
    name = "base"

    def send_text(self, to_e164: str, text: str) -> SendResult:
        raise NotImplementedError


class SmsProvider:
    name = "base"

    def send_text(self, to_e164: str, text: str) -> SendResult:
        raise NotImplementedError


class MetaWhatsAppCloudProvider(WhatsAppProvider):
    name = "meta_cloud"

    def send_text(self, to_e164: str, text: str) -> SendResult:
        """Meta WhatsApp Cloud API ile text mesaj gonderir.

        Not: Token/Phone Number ID .env'den gelir.
        """
        token = getattr(settings, "WHATSAPP_TOKEN", "")
        phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
        version = getattr(settings, "WHATSAPP_API_VERSION", "v19.0")

        if not token or not phone_number_id:
            return SendResult(ok=False, error="WHATSAPP_TOKEN veya WHATSAPP_PHONE_NUMBER_ID eksik")

        url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_e164.replace("+", ""),
            "type": "text",
            "text": {"body": text},
        }

        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            if resp.status_code >= 200 and resp.status_code < 300:
                data = resp.json() if resp.content else {}
                msg_id = ""
                # response: {messages:[{id:"..."}]}
                try:
                    msg_id = (data.get("messages") or [{}])[0].get("id") or ""
                except Exception:
                    msg_id = ""
                return SendResult(ok=True, message_id=msg_id)
            return SendResult(ok=False, error=f"HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            return SendResult(ok=False, error=str(e))


class GenericSmsProvider(SmsProvider):
    name = "generic"

    def send_text(self, to_e164: str, text: str) -> SendResult:
        if not settings.SMS_API_KEY:
            return SendResult(ok=False, error="SMS_API_KEY eksik")
        return SendResult(ok=False, error="Provider iskeleti: SMS API cagrisi eklenmedi")


def get_whatsapp_provider() -> WhatsAppProvider:
    if getattr(settings, "NOTIFY_WHATSAPP_PROVIDER", "meta_cloud") == "meta_cloud":
        return MetaWhatsAppCloudProvider()
    return MetaWhatsAppCloudProvider()


def get_sms_provider() -> SmsProvider:
    if getattr(settings, "NOTIFY_SMS_PROVIDER", "generic") == "generic":
        return GenericSmsProvider()
    return GenericSmsProvider()
