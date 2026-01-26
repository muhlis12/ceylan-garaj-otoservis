# OtoServis Pro (Scaffold)

Bu paket; **oto yikama takibi + lastik tamir/arac tamir takibi + lastik otel** icin hazir Django iskeletidir.

## Ozellikler
- Web + mobil uyumlu arayuz (Bootstrap) + PWA (ana ekrana eklenir)
- Tek sube ile baslar, cok subeye hazir (Branch)
- Is Emri akisi: Beklemede -> Islemde -> Teslim (gelen siraya gore)
- Lastik Otel: Depo1 (Raf + Goz kodu)
- SMS + WhatsApp (Resmi API) altyapisi: provider arayuzu + log kaydi

## Kurulum
```bash
cd otoservis_pro
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# (opsiyonel) python-dotenv kullanmak icin manage.py icine dotenv load ekleyebilirsin

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Notlar
- WhatsApp Cloud API ve SMS provider cagrilari `apps/notifications/providers.py` icinde iskelet olarak var.
- Uretime cikmadan once Postgres + gunicorn + nginx ile konuslandirin.
