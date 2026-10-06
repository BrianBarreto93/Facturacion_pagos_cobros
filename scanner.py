"""Módulo para escanear y descubrir la estructura de carpetas de encuestas en OneDrive.
Detecta años y meses cronológicamente para ubicar el corte más reciente o periodos específicos.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("etl_factura_cobro")

MONTH_NAME_TO_INT: dict[str, int] = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


@dataclass
class MonthFolderInfo:
    year: int
    month: int
    month_name: str
    folder_name: str
    folder_path: Path
    period_key: str  # YYYY-MM (e.g. 2026-08)


def parse_month_folder(folder_name: str, year: int, folder_path: Path) -> MonthFolderInfo | None:
    """Extrae el número y nombre del mes a partir de nombres como '08. Agosto', '01.Enero', '09.Septiembre'."""
    clean_name = folder_name.strip()
    match = re.match(r"^(\d{1,2})[\.\s_-]*(.+)$", clean_name, re.IGNORECASE)
    if match:
        month_num = int(match.group(1))
        m_name = match.group(2).strip()
        period_key = f"{year:04d}-{month_num:02d}"
        return MonthFolderInfo(
            year=year,
            month=month_num,
            month_name=m_name,
            folder_name=folder_name,
            folder_path=folder_path,
            period_key=period_key,
        )

    # Fallback por nombre textual del mes
    for name, num in MONTH_NAME_TO_INT.items():
        if name in clean_name.lower():
            period_key = f"{year:04d}-{num:02d}"
            return MonthFolderInfo(
                year=year,
                month=num,
                month_name=name.capitalize(),
                folder_name=folder_name,
                folder_path=folder_path,
                period_key=period_key,
            )

    return None


def scan_available_months(base_path: Path) -> list[MonthFolderInfo]:
    """Escanea el directorio base de OneDrive y retorna todas las carpetas de meses ordenadas cronológicamente."""
    if not base_path.exists():
        raise FileNotFoundError(f"La ruta base de OneDrive no existe: {base_path}")

    discovered: list[MonthFolderInfo] = []

    for item in base_path.iterdir():
        if item.is_dir() and item.name.isdigit() and len(item.name) == 4:
            year = int(item.name)
            for m_item in item.iterdir():
                if m_item.is_dir():
                    info = parse_month_folder(m_item.name, year, m_item)
                    if info:
                        # Verificar que contenga al menos un archivo Excel
                        has_excel = any(
                            f.is_file() and not f.name.startswith("~$") and f.suffix.lower() in [".xlsx", ".xls"]
                            for f in m_item.iterdir()
                        )
                        if has_excel:
                            discovered.append(info)

    # Ordenar cronológicamente (año, mes)
    discovered.sort(key=lambda x: (x.year, x.month))
    return discovered


def get_latest_month_folder(base_path: Path) -> MonthFolderInfo:
    """Obtiene la carpeta del mes más reciente con archivos disponibles."""
    months = scan_available_months(base_path)
    if not months:
        raise FileNotFoundError(f"No se encontraron carpetas mensuales con archivos en: {base_path}")
    latest = months[-1]
    logger.info(f"📅 Mes más reciente detectado: {latest.period_key} ({latest.folder_name} en {latest.year})")
    return latest


def get_specific_month_folder(base_path: Path, year: int, month: int) -> MonthFolderInfo:
    """Busca una carpeta mensual específica por año y mes."""
    months = scan_available_months(base_path)
    for m in months:
        if m.year == year and m.month == month:
            return m
    raise FileNotFoundError(f"No se encontró la carpeta para el periodo {year:04d}-{month:02d} en: {base_path}")
