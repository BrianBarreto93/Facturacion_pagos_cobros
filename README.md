# ETL: Ingesta y Consolidación de Encuestas Factura, Pago y Cobro en Oracle DB

Sistema modular, automatizado y de alto rendimiento en Python para la detección, consolidación y carga de encuestas de **Factura, Pago y Cobro** (Hogar y Móvil) hacia la base de datos **Oracle**.

---

## 📌 Arquitectura y Características

1. **Detección Automática del Mes Más Reciente:**
   - Escanea el directorio compartido de OneDrive: `CoE Experiencia Clientes - 07. Factura, Pago y Cobro`.
   - Identifica carpetas de años (`2024`, `2025`, `2026`...) y subcarpetas de meses (`01. Enero`, `02. Febrero`, ..., `08. Agosto`).
   - Por defecto, ubica e ingesta automáticamente el corte más reciente sin intervención manual.

2. **Consolidación Unificada (Hogar + Móvil):**
   - Extrae automáticamente los archivos correspondientes a **Hogar** (`BDD Fact Hogar_*.xlsx`) y **Móvil** (`BDD Fact Mo_*.xlsx` / `BDD Fact Mov_*.xlsx`).
   - Lee prioritariamente la hoja `'Encuesta Efectiva'`.
   - Homologa los 69+ campos y preguntas de la encuesta a un esquema canónico estándar.
   - Añade metadatos de auditoría y trazabilidad (`TIPO_BASE`, `NOMBRE_ARCHIVO`, `ANIO_CORTE`, `MES_CORTE`, `ANIO_MES_CORTE`, `FECHA_CARGA_ETL`).

3. **Optimización en Oracle SQL y Rendimiento:**
   - Conexión nativa en **modo Thin** con `oracledb` (sin necesidad de Oracle Instant Client instalado).
   - Inserción masiva optimizada por lotes (`executemany` con chunking de hasta 5,000 registros).
   - **Idempotencia Garantizada:** Limpieza previa automática del periodo (`ANIO_MES_CORTE`) antes de insertar, evitando duplicidades al reejecutar.
   - Auto-creación de tabla `TBL_ENC_FACT_PAGOS_COBROS` e índices B-Tree para acelerar consultas analíticas (`ANIO_MES_CORTE`, `REGISTRO_ID`).

4. **Reutilización de Credenciales `.env`:**
   - Utiliza automáticamente el archivo `.env` configurado en el proyecto vecino `claro_nps_auto` (`ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_DBNAME`).

---

## 📂 Estructura del Proyecto

```text
d:\1. CX\Proyectos\cargue_bases_factura_pagos_cobro\
├── config.py             # Configuración central, rutas de OneDrive, .env y esquema de columnas
├── db.py                 # Conexión Oracle (Thin mode), DDL, validación de tablas e índices
├── scanner.py            # Detección cronológica de carpetas y meses en OneDrive
├── transformer.py        # Lectura de Excel, normalización de preguntas, casting y consolidación
├── loader.py             # Inserción masiva por lotes (executemany) e idempotencia
├── main.py                       # Orquestador y CLI principal con flags de ejecución
├── ejecutar_mes_mas_reciente.bat # Script Windows 1-clic para cargar el mes más reciente
├── ejecutar_mes_especifico.bat   # Script Windows interactivo para cargar un año y mes puntual
├── requirements.txt              # Dependencias de Python
└── README.md                     # Documentación técnica y funcional
```

---

## 🚀 Guía de Uso

### 1. Ejecución con Doble Clic (Archivos `.bat`)

- **Para cargar el mes más reciente automáticamente:**
  Haz doble clic en [`ejecutar_mes_mas_reciente.bat`](file:///d:/1.%20CX/Proyectos/cargue_bases_factura_pagos_cobro/ejecutar_mes_mas_reciente.bat).
  
- **Para cargar un mes específico (ej. Julio 2026):**
  Haz doble clic en [`ejecutar_mes_especifico.bat`](file:///d:/1.%20CX/Proyectos/cargue_bases_factura_pagos_cobro/ejecutar_mes_especifico.bat). Te solicitará en pantalla el año y número de mes.

---

### 2. Ejecución por Consola / Terminal (CLI)

#### Requisitos y Entorno Virtual
Se recomienda utilizar el entorno virtual existente o crear uno nuevo:
```powershell
# Activar entorno virtual
& "d:\1. CX\Proyectos\claro_nps_auto\.venv\Scripts\Activate.ps1"

# O instalar dependencias
pip install -r requirements.txt
```

#### Ejecutar la Carga del Mes Más Reciente (Por defecto)
```powershell
python main.py
```
*El script detectará la carpeta del año en curso y el mes más reciente (ej. `2026/08. Agosto`), consolidará las bases de Hogar y Móvil y las cargará en Oracle.*

### 3. Modos y Parámetros Adicionales

#### A. Simulación sin escribir en Oracle (`--dry-run`)
Valida la lectura, consolidación y mapeo sin alterar la base de datos:
```powershell
python main.py --dry-run
```

#### B. Cargar un mes específico (`--year` y `--month`)
```powershell
python main.py --year 2026 --month 7
```

#### C. Ingesta masiva de todo el histórico (`--all`)
```powershell
python main.py --all
```

#### D. Especificar tabla destino personalizada (`--table`)
```powershell
python main.py --table TBL_ENC_FACT_PAGOS_COBROS
```

---

## 📊 Diccionario de Datos (`TBL_ENC_FACT_PAGOS_COBROS`)

| Columna Oracle | Tipo de Dato | Descripción / Pregunta Origen |
|---|---|---|
| `TIPO_BASE` | `VARCHAR2(50)` | Segmento consolidado (`HOGAR` o `MOVIL`) |
| `NOMBRE_ARCHIVO` | `VARCHAR2(250)` | Nombre del archivo fuente de Excel |
| `ANIO_CORTE` | `NUMBER(4)` | Año del corte (ej. 2026) |
| `MES_CORTE` | `NUMBER(2)` | Mes del corte (1..12) |
| `ANIO_MES_CORTE` | `VARCHAR2(7)` | Llave de periodo (ej. `'2026-08'`) |
| `FECHA_CARGA_ETL` | `TIMESTAMP` | Fecha y hora exacta de la ingesta |
| `REGISTRO_ID` | `NUMBER(19)` | Identificador único del registro de encuesta |
| `DET_CAMPANA` | `VARCHAR2(150)` | Detalle de la campaña |
| `FECHA_HORA_GESTION` | `TIMESTAMP` | Fecha y hora de gestión de la encuesta |
| `NUMERO_CUENTA` | `VARCHAR2(50)` | Número de cuenta del cliente |
| `IDENTIFICACION` | `VARCHAR2(50)` | Cédula o NIT del cliente |
| `NOMBRE` | `VARCHAR2(150)` | Nombre del cliente |
| `APELLIDO` | `VARCHAR2(150)` | Apellido del cliente |
| `CORREO` | `VARCHAR2(250)` | Correo electrónico |
| `TELEFONO` | `VARCHAR2(50)` | Teléfono de contacto |
| `SEGMENTO` | `VARCHAR2(100)` | Segmento comercial |
| `REGION` | `VARCHAR2(100)` | Región geográfica |
| `CIUDAD` | `VARCHAR2(100)` | Ciudad |
| `ANTIGUEDAD` | `VARCHAR2(100)` | Antigüedad del cliente |
| `TIPO_CLIENTE` | `VARCHAR2(100)` | Tipo de cliente |
| `DES_MEDIO` | `VARCHAR2(100)` | Medio de contacto |
| `DES_CANAL` | `VARCHAR2(100)` | Canal de atención |
| `COD_MEDIO` | `VARCHAR2(100)` | Código del medio |
| `BASE_ORIGEN` | `VARCHAR2(100)` | Base de origen |
| `ID_LLAMADA` | `VARCHAR2(100)` | Identificador de llamada |
| `ANALISTA_GESTIONA` | `VARCHAR2(150)` | Analista que gestiona |
| `DOC_ANALISTA` | `VARCHAR2(50)` | Documento del analista |
| `NIVEL_1` | `VARCHAR2(150)` | Tipificación Nivel 1 |
| `NIVEL_2` | `VARCHAR2(150)` | Tipificación Nivel 2 |
| `OBSERVACION` | `VARCHAR2(4000)` | Observaciones abiertas |
| `P1_SATISFACCION_FACTURA` | `NUMBER(5)` | 1. Satisfacción con facturación |
| `P1_1_MOTIVO_CALIF` | `VARCHAR2(4000)` | 1.1 Motivo calificación |
| `P1_2_MOTIVO_CALIF` | `VARCHAR2(4000)` | 1.2 Motivo calificación |
| `P2_FACILIDAD_ENTENDER` | `NUMBER(5)` | 2. Facilidad de entender la factura |
| `P2_1_DETALLE_DIFICIL` | `VARCHAR2(4000)` | 2.1 Detalle de lo que fue difícil |
| `P2_2_DETALLE_DIFICIL` | `VARCHAR2(4000)` | 2.2 Detalle de lo que fue difícil |
| `P3_VALORES_ACORDES_PLAN` | `VARCHAR2(100)` | 3. Valores acordes al plan |
| `P3_1_CONCEPTOS_ERRONEOS` | `VARCHAR2(4000)` | 3.1 Conceptos cobrados erróneos |
| `P3_2_PROFUNDIZACION` | `VARCHAR2(4000)` | 3.2 Profundización |
| `P4_TIEMPO_SUFICIENTE_REVISAR`| `VARCHAR2(100)`| 4. Factura llegó a tiempo para revisar |
| `P5_SATISFACCION_PAGO` | `NUMBER(5)` | 5. Satisfacción con proceso de pago |
| `P5_1_MOTIVO_CALIF` | `VARCHAR2(4000)` | 5.1 Motivo calificación pago |
| `P5_2_MOTIVO_CALIF` | `VARCHAR2(4000)` | 5.2 Motivo calificación pago |
| `P6_FACILIDAD_PAGO` | `NUMBER(5)` | 6. Facilidad al realizar el pago |
| `P6_1_DETALLE_DIFICIL` | `VARCHAR2(4000)` | 6.1 Detalle dificultad pago |
| `P6_2_DETALLE_DIFICIL` | `VARCHAR2(4000)` | 6.2 Detalle dificultad pago |
| `P7_CLARIDAD_PAGO` | `NUMBER(5)` | 7. Claridad proceso de pago |
| `P7_1_ASPECTO_ERRADO_1` | `VARCHAR2(4000)` | 7.1 Aspecto información errada (1) |
| `P7_1_OTRO_CUAL` | `VARCHAR2(4000)` | 7.1 Otro cual |
| `P7_2_MOTIVO_FALTA_CLARIDAD` | `VARCHAR2(4000)` | 7.2 Motivo falta claridad |
| `P7_2_1_MOTIVO_FALTA_CLARIDAD`| `VARCHAR2(4000)`| 7.2.1 Motivo falta claridad |
| `P7_3_ASPECTO_ERRADO_2` | `VARCHAR2(4000)` | 7.3 Aspecto información errada (2) |
| `P7_3_OTRO_CUAL` | `VARCHAR2(4000)` | 7.3 Otro cual |
| `P7_4_MOTIVO_FALTA_CLARIDAD` | `VARCHAR2(4000)` | 7.4 Motivo falta claridad |
| `P7_4_OTRO` | `VARCHAR2(4000)` | 7.4 Otro |
| `P8_RECIBIO_RECORDATORIOS` | `VARCHAR2(100)` | 8. Recibió recordatorios de pago |
| `P9_SATISFACCION_COBRO` | `NUMBER(5)` | 9. Satisfacción con proceso de cobro |
| `P9_1_MOTIVO_CALIF` | `VARCHAR2(4000)` | 9.1 Motivo calificación cobro |
| `P9_1_OTRO` | `VARCHAR2(4000)` | 9.1 Otro |
| `P10_EMOCIONES_PROCESO` | `VARCHAR2(4000)` | 10. Emociones generadas en el proceso |
| `P10_1_OTRO` | `VARCHAR2(4000)` | 10.1 Otro |
| `P10_2_EMOCIONES` | `VARCHAR2(4000)` | 10.2 Emociones |
| `P10_3_ASPECTO` | `VARCHAR2(4000)` | 10.3 Aspecto |
| `P10_3_OTRO` | `VARCHAR2(4000)` | 10.3 Otro |
| `P10_4_EMOCIONES` | `VARCHAR2(4000)` | 10.4 Emociones |
| `P11_RECOMENDACION_NPS` | `NUMBER(5)` | 11. Disposición a recomendar (NPS) |
| `P11_2_MOTIVO_CALIF` | `VARCHAR2(4000)` | 11.2 Motivo calificación recomendación |
| `P11_2_OTRO` | `VARCHAR2(4000)` | 11.2 Otro |
| `SAT` | `VARCHAR2(100)` | Clasificación SAT |
| `ESF` | `VARCHAR2(100)` | Clasificación Esfuerzo |
| `SAT_PAGO` | `VARCHAR2(100)` | Clasificación SAT Pago |
| `ESF_PAGO` | `VARCHAR2(100)` | Clasificación Esfuerzo Pago |
| `SAT_COBRO` | `VARCHAR2(100)` | Clasificación SAT Cobro |
| `NPS` | `VARCHAR2(100)` | Clasificación NPS (Promotor, Neutro, Detractor) |
| `MES_ENCUESTA` | `VARCHAR2(50)` | Nombre del mes en la encuesta |

---

## 🔍 Consultas de Validación en Oracle

Para validar los datos cargados directamente en Oracle SQL Developer o DBeaver:

```sql
-- 1. Resumen de registros por periodo y segmento
SELECT 
    ANIO_MES_CORTE,
    TIPO_BASE,
    COUNT(*) AS TOTAL_REGISTROS,
    MIN(FECHA_HORA_GESTION) AS PRIMERA_GESTION,
    MAX(FECHA_HORA_GESTION) AS ULTIMA_GESTION
FROM TBL_ENC_FACT_PAGOS_COBROS
GROUP BY ANIO_MES_CORTE, TIPO_BASE
ORDER BY ANIO_MES_CORTE DESC, TIPO_BASE;

-- 2. Distribución de NPS consolidado
SELECT 
    ANIO_MES_CORTE,
    TIPO_BASE,
    NPS,
    COUNT(*) AS CANTIDAD,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY ANIO_MES_CORTE, TIPO_BASE), 2) AS PORCENTAJE
FROM TBL_ENC_FACT_PAGOS_COBROS
GROUP BY ANIO_MES_CORTE, TIPO_BASE, NPS
ORDER BY ANIO_MES_CORTE DESC, TIPO_BASE, CANTIDAD DESC;
```
