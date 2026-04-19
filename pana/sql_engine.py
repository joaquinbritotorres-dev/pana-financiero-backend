from __future__ import annotations
import sqlite3
import re
import pandas as pd
from .loader import get_df
from .analytics import CLIENTE_MAP


def _build_connection(id_negocio: str) -> sqlite3.Connection:
    """Crea una conexión SQLite en memoria con los datos del negocio."""
    df = get_df(id_negocio)
    if df.empty:
        raise ValueError(f"No hay datos para el negocio {id_negocio}")
    conn = sqlite3.connect(":memory:")
    df_copy = df.copy()
    df_copy["fecha"] = df_copy["fecha"].astype(str)
    if "localidad" in df_copy.columns:
        df_copy["localidad"] = df_copy["localidad"].apply(str)
    
    # Agregar nombres de clientes para mejor lectura del LLM
    def _get_name(cid):
        if not isinstance(cid, str): return "Desconocido"
        try:
            num = int(re.sub(r"[^0-9]", "", cid))
            return CLIENTE_MAP[num % len(CLIENTE_MAP)]
        except: return "Caserito"
    
    df_copy["nombre_cliente"] = df_copy["id_cliente"].apply(_get_name)
    
    df_copy.to_sql("transacciones", conn, index=False, if_exists="replace")
    return conn


def _extract_sql(raw: str) -> str:
    """Extrae solo la query SQL del texto que devuelve el LLM."""
    raw = raw.strip()
    match = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    lines = [l for l in raw.splitlines() if l.strip().upper().startswith(
        ("SELECT", "WITH", "INSERT", "UPDATE", "DELETE")
    )]
    if lines:
        return "\n".join(lines).strip()
    return raw


def run_sql_query(sql: str, id_negocio: str) -> pd.DataFrame:
    """Ejecuta una query SQL sobre los datos del negocio y devuelve un DataFrame."""
    conn = _build_connection(id_negocio)
    try:
        result = pd.read_sql_query(sql, conn)
        return result
    except Exception as e:
        raise ValueError(f"Error ejecutando SQL: {e}\nQuery: {sql}")
    finally:
        conn.close()


SCHEMA_DESCRIPTION = """
Tabla: transacciones
Columnas:
- id_negocio: TEXT — identificador del negocio
- id_empleado: TEXT — identificador del empleado
- nombre: TEXT — nombre del negocio
- monto: REAL — monto de la transacción (siempre positivo)
- hora: TEXT — hora en formato HH:MM
- fecha: TEXT — fecha en formato YYYY-MM-DD
- tipo_movimiento: TEXT — 'ingreso' para ventas, 'egreso' para gastos, 'visualizacion' para consultas sin monto
- localidad: TEXT — coordenadas geográficas
- comentarios_transaccion: TEXT — descripción o comentario de la transacción
- id_cliente: TEXT — identificador del cliente
- nombre_cliente: TEXT — nombre legible del cliente (usar este en las respuestas)

Reglas importantes:
- "ventas" siempre significa WHERE tipo_movimiento = 'ingreso'
- "gastos" siempre significa WHERE tipo_movimiento = 'egreso'
- Los montos son siempre positivos tanto para ingresos como egresos
- Para la última transacción usa ORDER BY fecha DESC, hora DESC LIMIT 1
- Para totales usa SUM(monto)
- Para rankings usa ORDER BY DESC con LIMIT
- Para clientes usa GROUP BY id_cliente
- NUNCA uses tipo_movimiento = 'visualizacion' en cálculos financieros
"""
