import json
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"

NEGOCIOS_META = {
    "NEG-UIO-0001": {"nombre": "Tienda Doña Mercedes Pichasaca", "ciudad": "Quito", "emoji": "🏪"},
    "NEG-UIO-0002": {"nombre": "Taller Andino Motor", "ciudad": "Quito", "emoji": "🔧"},
    "NEG-UIO-0003": {"nombre": "Cafetería BuenaVista", "ciudad": "Quito", "emoji": "☕"},
    "NEG-GYE-0001": {"nombre": "Mundo Mascotas Guayaquil", "ciudad": "Guayaquil", "emoji": "🐾"},
}

FILE_MAP = {
    "NEG-UIO-0001": DATA_DIR / "tienda_mercedes.json",
    "NEG-UIO-0002": DATA_DIR / "taller_andino.json",
    "NEG-UIO-0003": DATA_DIR / "cafeteria_buenavista.json",
    "NEG-GYE-0001": DATA_DIR / "mundo_mascotas.json",
}

_dataframes: dict[str, pd.DataFrame] = {}


def load_all() -> dict[str, pd.DataFrame]:
    global _dataframes
    for neg_id, filepath in FILE_MAP.items():
        with open(filepath, encoding="utf-8") as f:
            records = json.load(f)
        df = pd.DataFrame(records)
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0.0)
        df["hora"] = df["hora"].astype(str)
        _dataframes[neg_id] = df
    return _dataframes


def get_df(id_negocio: str) -> pd.DataFrame:
    return _dataframes.get(id_negocio, pd.DataFrame())


def get_negocios_list() -> list[dict]:
    return [
        {
            "id_negocio": neg_id,
            "nombre": meta["nombre"],
            "ciudad": meta["ciudad"],
            "emoji": meta["emoji"],
        }
        for neg_id, meta in NEGOCIOS_META.items()
    ]
