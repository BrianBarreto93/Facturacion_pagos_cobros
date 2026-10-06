"""Orquestador principal del pipeline ETL de Factura, Pago y Cobro.
Permite la detección automática del mes más reciente en OneDrive,
consolidación de bases Hogar y Móvil, y carga optimizada en Oracle.
"""
from __future__ import annotations

import sys
import time
import argparse
import logging
from pathlib import Path

from config import (
    DEFAULT_ONEDRIVE_PATH,
    ORACLE_TARGET_TABLE,
)
from scanner import (
    get_latest_month_folder,
    get_specific_month_folder,
    scan_available_months,
    MonthFolderInfo,
)
from transformer import load_and_consolidate_month
from loader import insert_dataframe_to_oracle


def setup_logger(verbose: bool = False) -> logging.Logger:
    """Configura el logger de la aplicación con formato legible y soporte UTF-8 en Windows."""
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr.encoding.lower() != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    logger = logging.getLogger("etl_factura_cobro")
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


def process_single_month(
    month_info: MonthFolderInfo,
    table_name: str = ORACLE_TARGET_TABLE,
    dry_run: bool = False,
    logger: logging.Logger | None = None,
) -> int:
    """Ejecuta el flujo ETL para un mes específico."""
    if logger is None:
        logger = logging.getLogger("etl_factura_cobro")

    logger.info("=" * 70)
    logger.info(f"▶ PROCESANDO PERIODO: {month_info.period_key} ({month_info.folder_name})")
    logger.info("=" * 70)

    # 1. Transformar y consolidar
    df = load_and_consolidate_month(month_info)

    # 2. Cargar en Oracle
    inserted = insert_dataframe_to_oracle(
        df=df,
        table_name=table_name,
        dry_run=dry_run,
    )
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ETL Factura, Pago y Cobro: Carga mensual hacia Oracle DB.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--path",
        type=str,
        default=str(DEFAULT_ONEDRIVE_PATH),
        help="Ruta base de OneDrive donde se ubican las carpetas anuales y mensuales.",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Año específico a procesar (ej. 2026). Si no se indica, se detecta el más reciente.",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=None,
        help="Mes específico a procesar (1..12). Si no se indica, se detecta el más reciente.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Procesa e ingesta todos los meses históricos encontrados secuencialmente.",
    )
    parser.add_argument(
        "--table",
        type=str,
        default=ORACLE_TARGET_TABLE,
        help="Nombre de la tabla destino en Oracle.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula la extracción y transformación sin modificar la base de datos Oracle.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Activa logging detallado (DEBUG).",
    )

    args = parser.parse_args()
    logger = setup_logger(verbose=args.verbose)

    logger.info("=" * 70)
    logger.info("🚀 INICIANDO ETL: FACTURA, PAGO Y COBRO -> ORACLE DB")
    logger.info(f"📍 Ruta base: {args.path}")
    logger.info(f"🎯 Tabla destino: {args.table}")
    if args.dry_run:
        logger.info("⚠️ MODO DRY-RUN ACTIVADO (No se insertarán registros en Oracle)")
    logger.info("=" * 70)

    base_path = Path(args.path)
    start_total = time.time()
    total_inserted = 0

    try:
        if args.all:
            # Procesar todos los meses disponibles
            months = scan_available_months(base_path)
            logger.info(f"📚 Se encontraron {len(months)} meses disponibles para procesar.")
            for m in months:
                total_inserted += process_single_month(
                    month_info=m,
                    table_name=args.table,
                    dry_run=args.dry_run,
                    logger=logger,
                )
        elif args.year is not None and args.month is not None:
            # Procesar un mes específico
            target_month = get_specific_month_folder(base_path, args.year, args.month)
            total_inserted = process_single_month(
                month_info=target_month,
                table_name=args.table,
                dry_run=args.dry_run,
                logger=logger,
            )
        else:
            # Comportamiento por defecto: Mes más reciente
            latest_month = get_latest_month_folder(base_path)
            total_inserted = process_single_month(
                month_info=latest_month,
                table_name=args.table,
                dry_run=args.dry_run,
                logger=logger,
            )

        elapsed = time.time() - start_total
        logger.info("=" * 70)
        logger.info("🎉 RESUMEN DE EJECUCIÓN ETL")
        logger.info(f"   • Total de registros procesados/cargados: {total_inserted:,}")
        logger.info(f"   • Tiempo total transcurrido: {elapsed:.2f} segundos")
        logger.info(f"   • Estado: {'SIMULADO CON ÉXITO' if args.dry_run else 'COMPLETADO SATISFACTORIAMENTE'}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Error fatal en la ejecución del ETL: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
