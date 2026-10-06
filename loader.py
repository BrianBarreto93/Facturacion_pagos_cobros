"""Módulo de carga optimizada hacia la base de datos Oracle.
Implementa batching masivo con executemany, control de transacciones y medición de rendimiento.
"""
from __future__ import annotations

import time
import logging
from typing import Any
import pandas as pd
import oracledb

from config import (
    ORACLE_TARGET_TABLE,
    ORACLE_SCHEMA_COLUMNS,
    BATCH_SIZE,
)
from db import (
    get_oracle_connection,
    ensure_table_exists,
    delete_period_data,
)

logger = logging.getLogger("etl_factura_cobro")


def prepare_rows_for_oracle(df: pd.DataFrame) -> list[tuple[Any, ...]]:
    """Convierte un DataFrame de pandas a una lista de tuplas con tipos nativos de Python."""
    columns = list(ORACLE_SCHEMA_COLUMNS.keys())
    
    # Reemplazar NaN / NaT con None
    records = []
    for row in df[columns].itertuples(index=False):
        row_clean = []
        for val in row:
            if pd.isna(val):
                row_clean.append(None)
            else:
                row_clean.append(val)
        records.append(tuple(row_clean))
    return records


def insert_dataframe_to_oracle(
    df: pd.DataFrame,
    table_name: str = ORACLE_TARGET_TABLE,
    batch_size: int = BATCH_SIZE,
    dry_run: bool = False,
) -> int:
    """Inserta el DataFrame consolidado en la tabla de Oracle utilizando executemany por lotes."""
    if df.empty:
        logger.warning("El DataFrame está vacío. No hay registros para insertar.")
        return 0

    total_rows = len(df)
    columns = list(ORACLE_SCHEMA_COLUMNS.keys())
    placeholders = ", ".join([f":{i+1}" for i in range(len(columns))])
    col_names = ", ".join(columns)
    sql_insert = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

    if dry_run:
        logger.info(f"🔎 [DRY-RUN] Simulación de carga exitosa: {total_rows:,} registros preparados para {table_name}.")
        return total_rows

    logger.info(f"🚀 Iniciando inserción masiva en Oracle: {total_rows:,} filas en {table_name} (lotes de {batch_size:,})...")
    start_time = time.time()

    records = prepare_rows_for_oracle(df)

    con = get_oracle_connection()
    try:
        # Asegurar existencia de la tabla e índices
        ensure_table_exists(con, table_name=table_name)

        # Idempotencia: Limpiar datos previos del periodo si existen
        periodo = df["ANIO_MES_CORTE"].iloc[0]
        delete_period_data(con, table_name, periodo)

        inserted_count = 0
        with con.cursor() as cur:
            # Procesar en bloques para optimizar memoria y tiempo de respuesta en Oracle
            for i in range(0, total_rows, batch_size):
                batch = records[i : i + batch_size]
                cur.executemany(sql_insert, batch)
                inserted_count += len(batch)
                logger.info(f"   ↳ Lote insertado: {inserted_count:,} / {total_rows:,} registros...")

        con.commit()
        elapsed = time.time() - start_time
        rate = total_rows / elapsed if elapsed > 0 else total_rows
        logger.info(f"✅ Carga en Oracle finalizada exitosamente: {inserted_count:,} registros en {elapsed:.2f}s ({rate:.0f} filas/s).")
        return inserted_count

    except Exception as e:
        logger.error(f"❌ Error durante la inserción en Oracle: {e}", exc_info=True)
        try:
            con.rollback()
            logger.warning("↺ Transacción revertida (ROLLBACK).")
        except Exception:
            pass
        raise
    finally:
        con.close()
