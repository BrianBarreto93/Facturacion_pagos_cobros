"""Configuración central para el ETL de Factura, Pago y Cobro.
Carga automáticamente las credenciales desde el archivo .env del proyecto claro_nps_auto
o del entorno local.
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Resolución de Rutas de Entorno y Configuración
PROJECT_ROOT = Path(__file__).resolve().parent
CLARO_NPS_AUTO_ENV = Path(r"d:\1. CX\Proyectos\claro_nps_auto\.env")
LOCAL_ENV = PROJECT_ROOT / ".env"

# Cargar .env de claro_nps_auto con prioridad, o local
if CLARO_NPS_AUTO_ENV.exists():
    load_dotenv(dotenv_path=CLARO_NPS_AUTO_ENV, override=False)
elif LOCAL_ENV.exists():
    load_dotenv(dotenv_path=LOCAL_ENV, override=False)
else:
    load_dotenv(override=False)

# 2. Rutas de Origen de Datos (OneDrive)
DEFAULT_ONEDRIVE_PATH = Path(
    os.getenv(
        "ONEDRIVE_FACTURA_BASE_PATH",
        r"D:\OneDrive\OneDrive - Comunicacion Celular S.A.- Comcel S.A\CoE Experiencia Clientes - 07. Factura, Pago y Cobro",
    )
)

# 3. Configuración Oracle
ORACLE_HOST = os.getenv("ORACLE_HOST", "")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))
ORACLE_USER = os.getenv("ORACLE_USER", "")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
ORACLE_DBNAME = os.getenv("ORACLE_DBNAME", "")

ORACLE_CONNECT_TIMEOUT_S = int(os.getenv("ORACLE_CONNECT_TIMEOUT_S", "10"))
ORACLE_CALL_TIMEOUT_S = int(os.getenv("ORACLE_CALL_TIMEOUT_S", "60"))

# Tabla destino en Oracle (Default TBL_ENC_FACT_PAGOS_COBROS)
ORACLE_TARGET_TABLE = os.getenv("ORACLE_TARGET_TABLE", "TBL_ENC_FACT_PAGOS_COBROS").strip()

# Tamaño de batch para executemany masivo en Oracle
BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", "5000"))

# 4. Esquema canónico de columnas y tipos en Oracle
ORACLE_SCHEMA_COLUMNS: dict[str, str] = {
    # Auditoría / Metadatos ETL
    "TIPO_BASE": "VARCHAR2(50)",
    "NOMBRE_ARCHIVO": "VARCHAR2(250)",
    "ANIO_CORTE": "NUMBER(4)",
    "MES_CORTE": "NUMBER(2)",
    "ANIO_MES_CORTE": "VARCHAR2(7)",
    "FECHA_CARGA_ETL": "TIMESTAMP",
    
    # Identificadores y Datos del Cliente
    "REGISTRO_ID": "NUMBER(19)",
    "DET_CAMPANA": "VARCHAR2(150)",
    "FECHA_HORA_GESTION": "TIMESTAMP",
    "NUMERO_CUENTA": "VARCHAR2(50)",
    "IDENTIFICACION": "VARCHAR2(50)",
    "NOMBRE": "VARCHAR2(150)",
    "APELLIDO": "VARCHAR2(150)",
    "CORREO": "VARCHAR2(250)",
    "TELEFONO": "VARCHAR2(50)",
    "SEGMENTO": "VARCHAR2(100)",
    "REGION": "VARCHAR2(100)",
    "CIUDAD": "VARCHAR2(100)",
    "ANTIGUEDAD": "VARCHAR2(100)",
    "TIPO_CLIENTE": "VARCHAR2(100)",
    "DES_MEDIO": "VARCHAR2(100)",
    "DES_CANAL": "VARCHAR2(100)",
    "COD_MEDIO": "VARCHAR2(100)",
    "BASE_ORIGEN": "VARCHAR2(100)",
    "ID_LLAMADA": "VARCHAR2(100)",
    "ANALISTA_GESTIONA": "VARCHAR2(150)",
    "DOC_ANALISTA": "VARCHAR2(50)",
    "NIVEL_1": "VARCHAR2(150)",
    "NIVEL_2": "VARCHAR2(150)",
    "OBSERVACION": "VARCHAR2(4000)",

    # Preguntas de Encuesta
    "P1_SATISFACCION_FACTURA": "NUMBER(5)",
    "P1_1_MOTIVO_CALIF": "VARCHAR2(4000)",
    "P1_2_MOTIVO_CALIF": "VARCHAR2(4000)",
    "P2_FACILIDAD_ENTENDER": "NUMBER(5)",
    "P2_1_DETALLE_DIFICIL": "VARCHAR2(4000)",
    "P2_2_DETALLE_DIFICIL": "VARCHAR2(4000)",
    "P3_VALORES_ACORDES_PLAN": "VARCHAR2(100)",
    "P3_1_CONCEPTOS_ERRONEOS": "VARCHAR2(4000)",
    "P3_2_PROFUNDIZACION": "VARCHAR2(4000)",
    "P4_TIEMPO_SUFICIENTE_REVISAR": "VARCHAR2(100)",
    "P5_SATISFACCION_PAGO": "NUMBER(5)",
    "P5_1_MOTIVO_CALIF": "VARCHAR2(4000)",
    "P5_2_MOTIVO_CALIF": "VARCHAR2(4000)",
    "P6_FACILIDAD_PAGO": "NUMBER(5)",
    "P6_1_DETALLE_DIFICIL": "VARCHAR2(4000)",
    "P6_2_DETALLE_DIFICIL": "VARCHAR2(4000)",
    "P7_CLARIDAD_PAGO": "NUMBER(5)",
    "P7_1_ASPECTO_ERRADO_1": "VARCHAR2(4000)",
    "P7_1_OTRO_CUAL": "VARCHAR2(4000)",
    "P7_2_MOTIVO_FALTA_CLARIDAD": "VARCHAR2(4000)",
    "P7_2_1_MOTIVO_FALTA_CLARIDAD": "VARCHAR2(4000)",
    "P7_3_ASPECTO_ERRADO_2": "VARCHAR2(4000)",
    "P7_3_OTRO_CUAL": "VARCHAR2(4000)",
    "P7_4_MOTIVO_FALTA_CLARIDAD": "VARCHAR2(4000)",
    "P7_4_OTRO": "VARCHAR2(4000)",
    "P8_RECIBIO_RECORDATORIOS": "VARCHAR2(100)",
    "P9_SATISFACCION_COBRO": "NUMBER(5)",
    "P9_1_MOTIVO_CALIF": "VARCHAR2(4000)",
    "P9_1_OTRO": "VARCHAR2(4000)",
    "P10_EMOCIONES_PROCESO": "VARCHAR2(4000)",
    "P10_1_OTRO": "VARCHAR2(4000)",
    "P10_2_EMOCIONES": "VARCHAR2(4000)",
    "P10_3_ASPECTO": "VARCHAR2(4000)",
    "P10_3_OTRO": "VARCHAR2(4000)",
    "P10_4_EMOCIONES": "VARCHAR2(4000)",
    "P11_RECOMENDACION_NPS": "NUMBER(5)",
    "P11_2_MOTIVO_CALIF": "VARCHAR2(4000)",
    "P11_2_OTRO": "VARCHAR2(4000)",

    # Métricas y Cierre
    "SAT": "VARCHAR2(100)",
    "ESF": "VARCHAR2(100)",
    "SAT_PAGO": "VARCHAR2(100)",
    "ESF_PAGO": "VARCHAR2(100)",
    "SAT_COBRO": "VARCHAR2(100)",
    "NPS": "VARCHAR2(100)",
    "MES_ENCUESTA": "VARCHAR2(50)",
}
