from urllib.parse import quote

def wa_text_workorder_created(customer_name, plate, subject, wo_id, total):
    msg = f"Merhaba {customer_name}%0ACEYLAN GARAJ VIP%0Aİş emri oluşturuldu%0ANo:#{wo_id}%0APlaka:{plate}%0AKonu:{subject}%0ATutar:{total} ₺"
    return quote(msg)

def wa_text_workorder_done(customer_name, plate, wo_id, total):
    msg = f"Merhaba {customer_name}%0ACEYLAN GARAJ VIP%0Aİş emri tamamlandı%0ANo:#{wo_id}%0APlaka:{plate}%0AToplam:{total} ₺"
    return quote(msg)
