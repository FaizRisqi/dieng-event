import os
import re
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("whatsapp")


def normalize_wa(number: str) -> str:
    """Bersihkan karakter non-digit dan sesuaikan prefix internasional 62."""
    if not number:
        return ""
    cleaned = re.sub(r"\D", "", number)
    if cleaned.startswith("08"):
        cleaned = "62" + cleaned[1:]
    elif cleaned.startswith("8"):
        cleaned = "62" + cleaned
    return cleaned


def get_wa_mode() -> str:
    """Mengembalikan mode aktif: 'fonnte', 'n8n', atau 'simulasi'."""
    provider = os.getenv("WA_PROVIDER", "").strip().lower()
    fonnte_token = os.getenv("FONNTE_TOKEN", "").strip()
    n8n_url = os.getenv("N8N_WEBHOOK_URL", "").strip()

    if provider == "simulasi":
        return "simulasi"
    if provider == "fonnte" and fonnte_token:
        return "fonnte"
    if provider == "n8n" and n8n_url:
        return "n8n"
    if not provider:
        if fonnte_token:
            return "fonnte"
        if n8n_url:
            return "n8n"
    return "simulasi"


def send_wa_message(target: str, message: str) -> tuple[bool, str]:
    """
    Kirim pesan WhatsApp menggunakan provider yang aktif:
    - Fonnte: FONNTE_TOKEN (POST https://api.fonnte.com/send)
    - n8n: N8N_WEBHOOK_URL (POST webhook JSON)
    - Mode simulasi: Catat di logger
    """
    phone = normalize_wa(target)
    if not phone or len(phone) < 10:
        return False, f"Nomor WhatsApp '{target}' tidak valid."

    mode = get_wa_mode()

    # 1. Integrasi Fonnte
    if mode == "fonnte":
        fonnte_token = os.getenv("FONNTE_TOKEN", "").strip()
        try:
            url = "https://api.fonnte.com/send"
            payload = json.dumps({"target": phone, "message": message}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Authorization": fonnte_token,
                    "Content-Type": "application/json",
                    "User-Agent": "Dieng-Event-App/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if result.get("status") is True:
                    return True, "Terkirim via Fonnte"
                return False, result.get("reason", "Gagal kirim via Fonnte")
        except Exception as e:
            logger.error(f"Error kirim WA via Fonnte ke {phone}: {e}")
            return False, f"Error koneksi Fonnte: {str(e)}"

    # 2. Integrasi n8n Webhook
    elif mode == "n8n":
        n8n_url = os.getenv("N8N_WEBHOOK_URL", "").strip()
        try:
            payload = json.dumps({
                "target": phone,
                "message": message,
                "app": "Dieng Event",
            }).encode("utf-8")
            req = urllib.request.Request(
                n8n_url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Dieng-Event-App/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return True, "Terkirim via webhook n8n"
        except Exception as e:
            logger.error(f"Error kirim WA via n8n ke {phone}: {e}")
            return False, f"Error koneksi n8n: {str(e)}"

    # 3. Fallback / Mode Simulasi (untuk development & pengujian)
    else:
        logger.info(f"[SIMULASI WA] Ke: {phone} | Pesan: {message}")
        return True, "Simulasi: Pesan tersimpan di log"
