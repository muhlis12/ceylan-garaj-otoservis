import re


def to_e164_tr(number: str) -> str:
    """Telefonu Turkiye icin kaba E.164'e cevirir.

    Kabul edilen ornekler:
    - 0505...
    - 505...
    - +90505...
    - 90505...

    Bu fonksiyon sadece yardimci; nihai dogrulama SMS/WhatsApp provider tarafinda.
    """
    s = (number or "").strip()
    if not s:
        return ""

    # sadece rakam ve + kalsin
    s = re.sub(r"[^0-9+]", "", s)

    if s.startswith("+"):
        return s
    if s.startswith("00"):
        return "+" + s[2:]
    if s.startswith("90") and len(s) >= 12:
        return "+" + s
    if s.startswith("0") and len(s) >= 11:
        return "+90" + s[1:]
    if len(s) == 10 and s.startswith("5"):
        return "+90" + s
    return s
