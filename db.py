"""Módulo de conexión y operaciones DDL/DML optimizadas en Oracle.
Utiliza modo Thin de oracledb (sin necesidad de Instant Client).
"""
from __future__ import annotations

import logging
from typing import Any
import oracledb

from config import (
    ORACLE_HOST,
    ORACLE_PORT,
    ORACLE_USER,
    ORACLE_PASSWORD,
    ORACLE_DBNAME,
    ORACLE_CONNECT_TIMEOUT_S,
    ORACLE_CALL_TIMEOUT_S,
    ORACLE_TARGET_TABLE,
    ORACLE_SCHEMA_COLUMNS,
)

logger = logging.getLogger("etl_factura_cobro")


def get_oracle_connection() -> oracledb.Connection:
    """Crea y retorna una conexión a la base de datos Oracle."""
    if not all([ORACLE_HOST, ORACLE_USER, ORACLE_PASSWORD, ORACLE_DBNAME]):
        raise ValueError(
            "Faltan credenciales de Oracle en el entorno (.env). "
            "Asegúrate de configurar ORACLE_HOST, ORACLE_PORT, ORACLE_USER, ORACLE_PASSWORD y ORACLE_DBNAME."
        )

    logger.debug(f"Conectando a Oracle ({ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_DBNAME}) como {ORACLE_USER}...")
    con = oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_DBNAME}",
        tcp_connect_timeout=ORACLE_CONNECT_TIMEOUT_S,
    )
    con.call_timeout = ORACLE_CALL_TIMEOUT_S * 1000  # En milisegundos
    return con


def parse_table_name(full_table_name: str) -> tuple[str | None, str]:
    """Separa el esquema y la tabla si viene en formato ESQUEMA.TABLA o TABLA."""
    clean_name = full_table_name.strip().replace('"', '')
    if "." in clean_name:
        parts = clean_name.split(".", 1)
        return parts[0].upper(), parts[1].upper()
    return None, clean_name.upper()


def check_table_exists(con: oracledb.Connection, table_name: str) -> bool:
    """Verifica si la tabla existe en Oracle."""
    schema, tbl = parse_table_name(table_name)
    with con.cursor() as cur:
        if schema:
            cur.execute(
                "SELECT COUNT(*) FROM all_tables WHERE owner = :1 AND table_name = :2",
                [schema, tbl],
            )
        else:
            cur.execute(
                "SELECT COUNT(*) FROM user_tables WHERE table_name = :1",
                [tbl],
            )
        count = cur.fetchone()[0]
        return count > 0


def ensure_table_exists(
    con: oracledb.Connection,
    table_name: str = ORACLE_TARGET_TABLE,
    schema_cols: dict[str, str] = ORACLE_SCHEMA_COLUMNS,
) -> None:
    """Verifica si la tabla existe; si no existe, la crea con todos sus campos e índices."""
    if check_table_exists(con, table_name):
        logger.info(f"✓ Tabla destino en Oracle '{table_name}' verificada (ya existe).")
        return

    logger.info(f"⚡ Creando tabla '{table_name}' en Oracle...")
    cols_def = [f"    {col} {dtype}" for col, dtype in schema_cols.items()]
    ddl = f"CREATE TABLE {table_name} (\n" + ",\n".join(cols_def) + "\n)"

    with con.cursor() as cur:
        cur.execute(ddl)
        logger.info(f"✓ Tabla '{table_name}' creada exitosamente.")

        # Crear índices para optimizar consultas analíticas
        idx_name = f"IDX_{table_name.split('.')[-1][:20]}_PER"
        try:
            cur.execute(f"CREATE INDEX {idx_name} ON {table_name} (ANIO_MES_CORTE, REGISTRO_ID)")
            logger.info(f"✓ Índice {idx_name} creado exitosamente.")
        except Exception as e:
            logger.warning(f"No se pudo crear el índice {idx_name}: {e}")

    con.commit()


def delete_period_data(
    con: oracledb.Connection,
    table_name: str,
    anio_mes_corte: str,
) -> int:
    """Elimina los datos existentes de un periodo antes de cargarlo (idempotencia).
    Retorna la cantidad de registros eliminados.
    """
    logger.info(f"Verificando idempotencia para el periodo '{anio_mes_corte}' en {table_name}...")
    with con.cursor() as cur:
        cur.execute(
            f"DELETE FROM {table_name} WHERE ANIO_MES_CORTE = :1",
            [anio_mes_corte],
        )
        deleted_count = cur.rowcount
        con.commit()
        if deleted_count > 0:
            logger.info(f"🗑️ Se eliminaron {deleted_count:,} registros previos del periodo {anio_mes_corte}.")
        else:
            logger.info(f"ℹ️ No existían registros previos para el periodo {anio_mes_corte}.")
        return deleted_count
