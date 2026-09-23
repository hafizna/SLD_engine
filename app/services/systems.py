"""Which transmission system (Jamali / Sumatera) and region a subsystem is in.

One rule for the dashboard and for ingest, read off a subsystem's `apb`
string. Sumatera is checked first: "Sumbagteng" must never be read as
"Tengah", nor a Sumatera Barat asset as Jawa Barat.
"""
from __future__ import annotations


def system_of_apb(apb: str | None) -> str:
    value = (apb or "").upper()
    if "SUMBAG" in value or "SUMATERA" in value or value in {"SBU", "SBT", "SBS"}:
        return "SUMATERA"
    return "JAMALI"


def region_key(apb: str | None) -> str:
    value = (apb or "").upper()
    if system_of_apb(apb) == "SUMATERA":
        if "SUMBAGUT" in value or value == "SBU":
            return "SUMBAGUT"
        if "SUMBAGTENG" in value or value == "SBT":
            return "SUMBAGTENG"
        if "SUMBAGSEL" in value or value == "SBS":
            return "SUMBAGSEL"
        return "SUMATERA_LAIN"
    if "JAKARTA" in value or "BANTEN" in value or value == "JBB":
        return "JAKARTA_BANTEN"
    if "BARAT" in value or "JABAR" in value:
        return "JAWA_BARAT"
    if "TENGAH" in value or "DIY" in value or "JATENG" in value:
        return "JAWA_TENGAH_DIY"
    if "TIMUR" in value or "JATIM" in value:
        return "JAWA_TIMUR"
    if "BALI" in value:
        return "BALI"
    return "BELUM_DIPETAKAN"
