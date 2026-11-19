"""
Tes normalize_wa dan mode simulasi WhatsApp (TUGAS 4 - whatsapp).
"""
import os
import pytest
from app.services.whatsapp import normalize_wa, get_wa_mode, send_wa_message


def test_normalize_wa_format_08():
    assert normalize_wa("08123456789") == "628123456789"


def test_normalize_wa_format_8():
    assert normalize_wa("8123456789") == "628123456789"


def test_normalize_wa_format_62():
    assert normalize_wa("628123456789") == "628123456789"


def test_normalize_wa_format_plus62():
    assert normalize_wa("+62 812-3456-789") == "628123456789"


def test_normalize_wa_empty():
    assert normalize_wa("") == ""
    assert normalize_wa(None) == ""


def test_normalize_wa_spasi_dan_dash():
    assert normalize_wa("0812 3456 789") == "628123456789"


def test_get_wa_mode_default_simulasi(monkeypatch):
    """Tanpa token apapun, mode harus simulasi."""
    monkeypatch.delenv("FONNTE_TOKEN", raising=False)
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("WA_PROVIDER", raising=False)
    assert get_wa_mode() == "simulasi"


def test_get_wa_mode_fonnte(monkeypatch):
    monkeypatch.setenv("FONNTE_TOKEN", "tok123")
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("WA_PROVIDER", raising=False)
    assert get_wa_mode() == "fonnte"


def test_get_wa_mode_n8n(monkeypatch):
    monkeypatch.delenv("FONNTE_TOKEN", raising=False)
    monkeypatch.setenv("N8N_WEBHOOK_URL", "https://n8n.example.com/webhook/abc")
    monkeypatch.delenv("WA_PROVIDER", raising=False)
    assert get_wa_mode() == "n8n"


def test_get_wa_mode_provider_explicit_simulasi(monkeypatch):
    monkeypatch.setenv("WA_PROVIDER", "simulasi")
    monkeypatch.setenv("FONNTE_TOKEN", "tok123")  # ada token tapi provider=simulasi
    assert get_wa_mode() == "simulasi"


def test_simulasi_tidak_mengirim_ke_wa(monkeypatch):
    """Mode simulasi harus mengembalikan True (simulasi sukses) tapi BUKAN mengirim ke API."""
    monkeypatch.delenv("FONNTE_TOKEN", raising=False)
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("WA_PROVIDER", raising=False)

    ok, msg = send_wa_message("08123456789", "Halo!")
    assert ok is True
    assert "Simulasi" in msg or "simulasi" in msg.lower()


def test_nomor_tidak_valid_ditolak():
    ok, msg = send_wa_message("123", "Halo!")
    assert ok is False
    assert "tidak valid" in msg


def test_nomor_kosong_ditolak():
    ok, msg = send_wa_message("", "Halo!")
    assert ok is False
