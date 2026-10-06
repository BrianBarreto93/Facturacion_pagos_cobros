"""Módulo de transformación y consolidación de archivos Excel (Hogar y Móvil).
Estandariza columnas, normaliza tipos de datos y prepara el dataset canónico para Oracle.
"""
from __future__ import annotations

import re
import datetime
import logging
import unicodedata
from pathlib import Path
import pandas as pd
import numpy as np

from config import ORACLE_SCHEMA_COLUMNS
from scanner import MonthFolderInfo

logger = logging.getLogger("etl_factura_cobro")


def clean_text_header(s: str) -> str:
    """Normaliza texto eliminando acentos y convirtiendo a mayúsculas."""
    s = str(s).strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.upper()


def map_raw_header_to_oracle(raw_col: str) -> str:
    """Mapea dinámicamente un encabezado de Excel a la columna canónica de Oracle."""
    c = clean_text_header(raw_col)

    # 1. Mapeo jerárquico por prefijo de pregunta (de mayor especificidad a menor)
    if c.startswith("7.2.1"): return "P7_2_1_MOTIVO_FALTA_CLARIDAD"
    if c.startswith("7.2"): return "P7_2_MOTIVO_FALTA_CLARIDAD"
    if c.startswith("7.1") and "OTRO" in c: return "P7_1_OTRO_CUAL"
    if c.startswith("7.1"): return "P7_1_ASPECTO_ERRADO_1"
    if c.startswith("7.3") and "OTRO" in c: return "P7_3_OTRO_CUAL"
    if c.startswith("7.3"): return "P7_3_ASPECTO_ERRADO_2"
    if c.startswith("7.4") and "OTRO" in c: return "P7_4_OTRO"
    if c.startswith("7.4"): return "P7_4_MOTIVO_FALTA_CLARIDAD"
    if c.startswith("7."): return "P7_CLARIDAD_PAGO"

    if c.startswith("10.1"): return "P10_1_OTRO"
    if c.startswith("10.2"): return "P10_2_EMOCIONES"
    if c.startswith("10.3") and "OTRO" in c: return "P10_3_OTRO"
    if c.startswith("10.3"): return "P10_3_ASPECTO"
    if c.startswith("10.4"): return "P10_4_EMOCIONES"
    if c.startswith("10."): return "P10_EMOCIONES_PROCESO"

    if c.startswith("11.2") and "OTRO" in c: return "P11_2_OTRO"
    if c.startswith("11.2"): return "P11_2_MOTIVO_CALIF"
    if c.startswith("11.") or "RECOMENDAR" in c or "DISPUESTO" in c: return "P11_RECOMENDACION_NPS"

    if c.startswith("1.1"): return "P1_1_MOTIVO_CALIF"
    if c.startswith("1.2"): return "P1_2_MOTIVO_CALIF"
    if c.startswith("1."): return "P1_SATISFACCION_FACTURA"

    if c.startswith("2.1"): return "P2_1_DETALLE_DIFICIL"
    if c.startswith("2.2"): return "P2_2_DETALLE_DIFICIL"
    if c.startswith("2."): return "P2_FACILIDAD_ENTENDER"

    if c.startswith("3.1"): return "P3_1_CONCEPTOS_ERRONEOS"
    if c.startswith("3.2"): return "P3_2_PROFUNDIZACION"
    if c.startswith("3."): return "P3_VALORES_ACORDES_PLAN"

    if c.startswith("4."): return "P4_TIEMPO_SUFICIENTE_REVISAR"

    if c.startswith("5.1"): return "P5_1_MOTIVO_CALIF"
    if c.startswith("5.2"): return "P5_2_MOTIVO_CALIF"
    if c.startswith("5."): return "P5_SATISFACCION_PAGO"

    if c.startswith("6.1"): return "P6_1_DETALLE_DIFICIL"
    if c.startswith("6.2"): return "P6_2_DETALLE_DIFICIL"
    if c.startswith("6."): return "P6_FACILIDAD_PAGO"

    if c.startswith("8."): return "P8_RECIBIO_RECORDATORIOS"

    if c.startswith("9.1") and "OTRO" in c: return "P9_1_OTRO"
    if c.startswith("9.1"): return "P9_1_MOTIVO_CALIF"
    if c.startswith("9.") or c.startswith("9 "): return "P9_SATISFACCION_COBRO"

    # 2. Datos del cliente, llamada y metadata
    if "REGISTROID" in c: return "REGISTRO_ID"
    if "DETCAMPANA" in c: return "DET_CAMPANA"
    if "FECHA" in c and "GESTION" in c: return "FECHA_HORA_GESTION"
    if "NUMERO" in c and "CUENTA" in c: return "NUMERO_CUENTA"
    if "IDENTIFICAC" in c: return "IDENTIFICACION"
    if c == "NOMBRE": return "NOMBRE"
    if c == "APELLIDO": return "APELLIDO"
    if c == "CORREO": return "CORREO"
    if c == "TELEFONO": return "TELEFONO"
    if c == "SEGMENTO": return "SEGMENTO"
    if c == "REGION": return "REGION"
    if c == "CIUDAD": return "CIUDAD"
    if "ANTIGUEDAD" in c: return "ANTIGUEDAD"
    if c == "TIPO": return "TIPO_CLIENTE"
    if "DES_MEDIO" in c: return "DES_MEDIO"
    if "DES_CANAL" in c: return "DES_CANAL"
    if "COD_MEDIO" in c: return "COD_MEDIO"
    if c == "BASE": return "BASE_ORIGEN"
    if "LLAMADA" in c: return "ID_LLAMADA"
    if "ANALISTA" in c and "DOC" not in c: return "ANALISTA_GESTIONA"
    if "DOCANALISTA" in c: return "DOC_ANALISTA"
    if "NIVEL 1" in c or "NIVEL_1" in c: return "NIVEL_1"
    if "NIVEL 2" in c or "NIVEL_2" in c: return "NIVEL_2"
    if "OBSERVACION" in c: return "OBSERVACION"

    # 3. Métricas directas
    if c == "SAT": return "SAT"
    if c == "ESF": return "ESF"
    if c == "SAT PAGO": return "SAT_PAGO"
    if c == "ESF PAGO": return "ESF_PAGO"
    if c == "SAT COBRO": return "SAT_COBRO"
    if c == "NPS": return "NPS"
    if c == "MES": return "MES_ENCUESTA"

    # 4. Fallback limpio
    norm = re.sub(r"[^A-Z0-9_]", "_", c)
    norm = re.sub(r"_+", "_", norm).strip("_")
    return norm[:30]


def detect_file_segment(filename: str) -> str:
    """Identifica si el archivo corresponde a Hogar o Móvil a partir de su nombre."""
    fn = filename.lower()
    if "hogar" in fn:
        return "HOGAR"
    elif "mo_" in fn or "mov" in fn or "postpago" in fn or "celular" in fn:
        return "MOVIL"
    return "GENERAL"


def read_survey_excel(file_path: Path) -> pd.DataFrame:
    """Lee el archivo Excel seleccionando prioritariamente la hoja 'Encuesta Efectiva'."""
    xl = pd.ExcelFile(file_path)
    sheet_name = None
    for s in xl.sheet_names:
        if "encuesta efectiva" in s.lower() or "efectiva" in s.lower():
            sheet_name = s
            break

    if not sheet_name:
        sheet_name = xl.sheet_names[0]

    logger.debug(f"Leyendo archivo: {file_path.name} | Hoja: '{sheet_name}'...")
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    return df


def clean_and_cast_dataframe(
    df: pd.DataFrame,
    segment: str,
    file_name: str,
    month_info: MonthFolderInfo,
) -> pd.DataFrame:
    """Normaliza columnas, tipos de datos y añade metadatos de auditoría."""
    # Renombrar columnas según mapeo
    col_mapping = {col: map_raw_header_to_oracle(col) for col in df.columns}
    df = df.rename(columns=col_mapping)

    # Eliminar duplicados de columnas si existieran en el origen
    df = df.loc[:, ~df.columns.duplicated()]

    # Agregar columnas de auditoría ETL
    df["TIPO_BASE"] = segment
    df["NOMBRE_ARCHIVO"] = file_name
    df["ANIO_CORTE"] = month_info.year
    df["MES_CORTE"] = month_info.month
    df["ANIO_MES_CORTE"] = month_info.period_key
    df["FECHA_CARGA_ETL"] = datetime.datetime.now()

    # Asegurar que todas las columnas del esquema Oracle existan en el DataFrame
    for col in ORACLE_SCHEMA_COLUMNS.keys():
        if col not in df.columns:
            df[col] = None

    # Reordenar y recortar solo a las columnas definidas en el esquema
    df = df[list(ORACLE_SCHEMA_COLUMNS.keys())].copy()

    # Limpieza de tipos de datos
    # 1. Fechas
    if "FECHA_HORA_GESTION" in df.columns:
        df["FECHA_HORA_GESTION"] = pd.to_datetime(df["FECHA_HORA_GESTION"], errors="coerce")
        # Convertir a objetos datetime nativos de Python o None (para compatibilidad con oracledb)
        df["FECHA_HORA_GESTION"] = df["FECHA_HORA_GESTION"].apply(
            lambda x: x.to_pydatetime() if pd.notnull(x) else None
        )

    # 2. Identificadores y numéricos enteros
    integer_cols = [
        "REGISTRO_ID",
        "ANIO_CORTE",
        "MES_CORTE",
        "P1_SATISFACCION_FACTURA",
        "P2_FACILIDAD_ENTENDER",
        "P5_SATISFACCION_PAGO",
        "P6_FACILIDAD_PAGO",
        "P7_CLARIDAD_PAGO",
        "P9_SATISFACCION_COBRO",
        "P11_RECOMENDACION_NPS",
    ]
    for col in integer_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            df[col] = df[col].apply(lambda x: int(x) if pd.notnull(x) else None)

    # 3. Textos y cadenas (manejo de None y truncamiento según tamaño máximo en Oracle)
    for col, col_type in ORACLE_SCHEMA_COLUMNS.items():
        if "VARCHAR2" in col_type:
            # Obtener longitud máxima permitida e.g. VARCHAR2(4000) -> 4000
            match = re.search(r"VARCHAR2\((\d+)\)", col_type)
            max_len = int(match.group(1)) if match else 4000
            
            # Limpiar floats/NaN/enteros a string limpio
            def _clean_str(val, m_len=max_len):
                if val is None or pd.isna(val):
                    return None
                s = str(val).strip()
                if s.lower() in ("nan", "none", "null", ""):
                    return None
                # Si es un float terminado en .0 (como teléfonos o cédulas leídas como float)
                if s.endswith(".0") and re.match(r"^\d+\.0$", s):
                    s = s[:-2]
                return s[:m_len]

            df[col] = df[col].apply(_clean_str)

    return df


def load_and_consolidate_month(month_info: MonthFolderInfo) -> pd.DataFrame:
    """Busca los archivos de Hogar y Móvil en la carpeta del mes, los procesa y consolida en un solo DataFrame."""
    folder = month_info.folder_path
    excel_files = [
        f for f in folder.iterdir()
        if f.is_file() and not f.name.startswith("~$") and f.suffix.lower() in [".xlsx", ".xls"]
    ]

    if not excel_files:
        raise FileNotFoundError(f"No se encontraron archivos Excel en la carpeta: {folder}")

    logger.info(f"📂 Procesando carpeta: {month_info.folder_name} ({len(excel_files)} archivo(s) detectado(s))")

    dfs: list[pd.DataFrame] = []
    for fpath in excel_files:
        segment = detect_file_segment(fpath.name)
        logger.info(f"  📄 Archivo: {fpath.name} | Segmento detectado: {segment}")
        raw_df = read_survey_excel(fpath)
        logger.info(f"     Filas leídas: {len(raw_df):,} | Columnas: {len(raw_df.columns)}")
        clean_df = clean_and_cast_dataframe(raw_df, segment, fpath.name, month_info)
        dfs.append(clean_df)

    consolidated_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"✨ Consolidación completada: Total {len(consolidated_df):,} registros listos para cargar.")
    
    # Resumen por segmento
    resumen = consolidated_df["TIPO_BASE"].value_counts().to_dict()
    for seg, count in resumen.items():
        logger.info(f"     • {seg}: {count:,} registros")

    return consolidated_df
