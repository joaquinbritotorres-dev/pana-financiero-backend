from __future__ import annotations
import re
from datetime import timedelta
import pandas as pd


class PanaAnalytics:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        if not df.empty:
            self._hoy = df["fecha"].max().normalize()
        else:
            self._hoy = pd.Timestamp("2025-01-01")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _ingresos(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["tipo_movimiento"] == "ingreso"]

    def _egresos(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["tipo_movimiento"] == "egreso"]

    def _week_range(self, offset: int = 0) -> tuple[pd.Timestamp, pd.Timestamp]:
        monday = self._hoy - timedelta(days=self._hoy.dayofweek) - timedelta(weeks=offset)
        return monday, monday + timedelta(days=6)

    def _month_range(self, offset: int = 0) -> tuple[pd.Timestamp, pd.Timestamp]:
        first = (self._hoy.replace(day=1) - pd.DateOffset(months=offset)).normalize()
        last = (first + pd.DateOffset(months=1) - timedelta(days=1)).normalize()
        return first, last

    def _filter_period(self, df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        return df[(df["fecha"] >= start) & (df["fecha"] <= end)]

    # ── 1. ventas_del_dia ─────────────────────────────────────────────────────

    def ventas_del_dia(self, fecha: str = "hoy") -> dict:
        if self.df.empty:
            return {"total": 0, "num_tx": 0, "ticket_promedio": 0, "primera_hora": None, "ultima_hora": None, "comparacion": None}

        target = self._hoy if fecha == "hoy" else pd.Timestamp(fecha).normalize()
        day_df = self._ingresos(self._filter_period(self.df, target, target))

        if day_df.empty:
            return {"total": 0, "num_tx": 0, "ticket_promedio": 0, "primera_hora": None, "ultima_hora": None, "fecha": str(target.date()), "comparacion": None}

        total = round(float(day_df["monto"].sum()), 2)
        num_tx = int(len(day_df))
        ticket = round(total / num_tx, 2) if num_tx else 0
        primera = day_df["hora"].min()
        ultima = day_df["hora"].max()

        # mismo dia semana anterior
        prev = target - timedelta(weeks=1)
        prev_df = self._ingresos(self._filter_period(self.df, prev, prev))
        comparacion = None
        if not prev_df.empty:
            prev_total = round(float(prev_df["monto"].sum()), 2)
            diff_pct = round((total - prev_total) / prev_total * 100, 1) if prev_total else None
            comparacion = {"total_semana_anterior": prev_total, "diferencia_pct": diff_pct}

        return {
            "fecha": str(target.date()),
            "total": total,
            "num_tx": num_tx,
            "ticket_promedio": ticket,
            "primera_hora": primera,
            "ultima_hora": ultima,
            "comparacion": comparacion,
        }

    # ── 2. comparar_periodos ──────────────────────────────────────────────────

    def comparar_periodos(self, periodo: str = "semana") -> dict:
        if self.df.empty:
            return {}

        if periodo == "semana":
            s_act, e_act = self._week_range(0)
            s_ant, e_ant = self._week_range(1)
            label_act, label_ant = "esta semana", "semana anterior"
        else:
            s_act, e_act = self._month_range(0)
            s_ant, e_ant = self._month_range(1)
            label_act = s_act.strftime("%B %Y")
            label_ant = s_ant.strftime("%B %Y")

        def _stats(start, end):
            chunk = self._ingresos(self._filter_period(self.df, start, end))
            total = round(float(chunk["monto"].sum()), 2)
            return {"total": total, "num_tx": int(len(chunk)), "ticket_promedio": round(total / len(chunk), 2) if len(chunk) else 0}

        act = _stats(s_act, e_act)
        ant = _stats(s_ant, e_ant)
        diff_abs = round(act["total"] - ant["total"], 2)
        diff_pct = round(diff_abs / ant["total"] * 100, 1) if ant["total"] else None

        return {
            "periodo_actual": {**act, "label": label_act},
            "periodo_anterior": {**ant, "label": label_ant},
            "diferencia_abs": diff_abs,
            "diferencia_pct": diff_pct,
        }

    # ── 3. balance_neto ───────────────────────────────────────────────────────

    def balance_neto(self, periodo: str = "semana") -> dict:
        if self.df.empty:
            return {"ingresos": 0, "egresos": 0, "balance": 0, "periodo": periodo}

        if periodo == "semana":
            start, end = self._week_range(0)
        else:
            start, end = self._month_range(0)

        chunk = self._filter_period(self.df, start, end)
        ingresos = round(float(self._ingresos(chunk)["monto"].sum()), 2)
        egresos = round(float(self._egresos(chunk)["monto"].sum()), 2)

        return {
            "ingresos": ingresos,
            "egresos": egresos,
            "balance": round(ingresos - egresos, 2),
            "periodo": periodo,
            "desde": str(start.date()),
            "hasta": str(end.date()),
        }

    # ── 4. top_caseritos ──────────────────────────────────────────────────────

    def top_caseritos(self, periodo: str = "mes", limite: int = 3) -> list[dict]:
        if self.df.empty:
            return []

        if periodo == "semana":
            start, end = self._week_range(0)
        else:
            start, end = self._month_range(0)

        chunk = self._ingresos(self._filter_period(self.df, start, end))
        if chunk.empty:
            return []

        grp = chunk.groupby("id_cliente")["monto"].agg(["sum", "count"]).reset_index()
        grp.columns = ["id_cliente", "total_gastado", "num_visitas"]
        grp["ticket_promedio"] = (grp["total_gastado"] / grp["num_visitas"]).round(2)
        grp["total_gastado"] = grp["total_gastado"].round(2)
        top = grp.sort_values("total_gastado", ascending=False).head(limite)
        return top.to_dict("records")

    # ── 5. clientes_inactivos ─────────────────────────────────────────────────

    def clientes_inactivos(self, dias_umbral: int = 14) -> list[dict]:
        if self.df.empty:
            return []

        ingresos = self._ingresos(self.df)
        if ingresos.empty:
            return []

        grp = ingresos.groupby("id_cliente")
        result = []
        for cliente, g in grp:
            if len(g) < 5:
                continue
            ultima_compra = g["fecha"].max()
            dias_sin = (self._hoy - ultima_compra).days
            if dias_sin <= dias_umbral:
                continue
            fechas_sorted = g["fecha"].sort_values()
            diffs = fechas_sorted.diff().dropna().dt.days
            intervalo_tipico = int(diffs.median()) if not diffs.empty else 0
            result.append({
                "id_cliente": cliente,
                "dias_sin_venir": int(dias_sin),
                "intervalo_tipico": intervalo_tipico,
                "total_historico": round(float(g["monto"].sum()), 2),
            })

        return sorted(result, key=lambda x: x["dias_sin_venir"], reverse=True)[:10]

    # ── 6. patron_horario ─────────────────────────────────────────────────────

    def patron_horario(self) -> dict:
        if self.df.empty:
            return {"franjas_pico": [], "hora_mas_floja": None}

        ing = self._ingresos(self.df).copy()
        if ing.empty:
            return {"franjas_pico": [], "hora_mas_floja": None}

        ing["hora_int"] = ing["hora"].str.split(":").str[0].astype(int, errors="ignore")
        by_hour = ing.groupby("hora_int")["monto"].sum()
        total = by_hour.sum()

        franjas = []
        for hora, monto in by_hour.nlargest(3).items():
            franjas.append({
                "hora_inicio": f"{int(hora):02d}:00",
                "hora_fin": f"{int(hora):02d}:59",
                "pct_del_total": round(float(monto) / float(total) * 100, 1) if total else 0,
            })

        hora_floja = int(by_hour.idxmin()) if not by_hour.empty else None

        return {
            "franjas_pico": franjas,
            "hora_mas_floja": f"{hora_floja:02d}:00" if hora_floja is not None else None,
        }

    # ── 7. mejor_peor_dia ─────────────────────────────────────────────────────

    def mejor_peor_dia(self, periodo: str = "mes") -> dict:
        if self.df.empty:
            return {"mejor": None, "peor": None, "dia_semana_flojo": None}

        if periodo == "semana":
            start, end = self._week_range(0)
        else:
            start, end = self._month_range(0)

        chunk = self._ingresos(self._filter_period(self.df, start, end))
        if chunk.empty:
            return {"mejor": None, "peor": None, "dia_semana_flojo": None}

        by_day = chunk.groupby("fecha")["monto"].sum()
        mejor_fecha = by_day.idxmax()
        peor_fecha = by_day.idxmin()

        # dia semana estructuralmente flojo (histórico)
        hist = self._ingresos(self.df).copy()
        hist["dow"] = hist["fecha"].dt.day_name()
        dow_avg = hist.groupby("dow")["monto"].mean()
        global_avg = float(dow_avg.mean()) if not dow_avg.empty else 1
        dia_flojo = dow_avg.idxmin() if not dow_avg.empty else None
        pct_vs = round((float(dow_avg.min()) - global_avg) / global_avg * 100, 1) if global_avg else None

        return {
            "mejor": {"fecha": str(mejor_fecha.date()), "monto": round(float(by_day.max()), 2)},
            "peor": {"fecha": str(peor_fecha.date()), "monto": round(float(by_day.min()), 2)},
            "dia_semana_flojo": {"dia": dia_flojo, "pct_vs_promedio": pct_vs},
        }

    # ── 8. resumen_egresos ────────────────────────────────────────────────────

    def resumen_egresos(self, periodo: str = "semana") -> dict:
        if self.df.empty:
            return {"total": 0, "num_tx": 0, "top_categorias": [], "sin_comentario": {"num_tx": 0, "monto": 0}}

        if periodo == "semana":
            start, end = self._week_range(0)
        else:
            start, end = self._month_range(0)

        chunk = self._egresos(self._filter_period(self.df, start, end))
        if chunk.empty:
            return {"total": 0, "num_tx": 0, "top_categorias": [], "sin_comentario": {"num_tx": 0, "monto": 0}}

        total = round(float(chunk["monto"].sum()), 2)
        num_tx = int(len(chunk))

        con_com = chunk[chunk["comentarios_transaccion"].astype(str).str.strip() != ""]
        sin_com = chunk[chunk["comentarios_transaccion"].astype(str).str.strip() == ""]

        # extraer palabras clave (quitar stopwords básicas)
        stopwords = {"de", "la", "el", "en", "a", "para", "con", "por", "y", "e", "del", "los", "las", "un", "una"}
        word_monto: dict[str, float] = {}
        word_count: dict[str, int] = {}
        for _, row in con_com.iterrows():
            words = re.findall(r"[a-záéíóúñ]+", row["comentarios_transaccion"].lower())
            words = [w for w in words if w not in stopwords and len(w) > 2]
            for w in set(words):
                word_monto[w] = word_monto.get(w, 0) + float(row["monto"])
                word_count[w] = word_count.get(w, 0) + 1

        top_cats = sorted(word_monto.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total": total,
            "num_tx": num_tx,
            "top_categorias": [
                {"nombre": w, "monto": round(m, 2), "num_tx": word_count[w]}
                for w, m in top_cats
            ],
            "sin_comentario": {
                "num_tx": int(len(sin_com)),
                "monto": round(float(sin_com["monto"].sum()), 2),
            },
        }

    # ── 9. proyeccion_mes_actual ──────────────────────────────────────────────

    def proyeccion_mes_actual(self) -> dict:
        if self.df.empty:
            return {}

        start_mes, end_mes = self._month_range(0)
        mes_act = self._ingresos(self._filter_period(self.df, start_mes, self._hoy))
        acumulado = round(float(mes_act["monto"].sum()), 2)

        # promedio diario ultimos 14 dias
        start_14 = self._hoy - timedelta(days=13)
        ultimos14 = self._ingresos(self._filter_period(self.df, start_14, self._hoy))
        dias_con_datos = int(ultimos14["fecha"].nunique()) or 1
        promedio_diario = float(ultimos14["monto"].sum()) / dias_con_datos

        dias_transcurridos = int((self._hoy - start_mes).days) + 1
        dias_en_mes = int((end_mes - start_mes).days) + 1
        dias_restantes = max(0, dias_en_mes - dias_transcurridos)

        proyeccion_min = round(acumulado + promedio_diario * 0.8 * dias_restantes, 2)
        proyeccion_max = round(acumulado + promedio_diario * 1.2 * dias_restantes, 2)

        # mes anterior
        s_ant, e_ant = self._month_range(1)
        mes_ant = round(float(self._ingresos(self._filter_period(self.df, s_ant, e_ant))["monto"].sum()), 2)

        return {
            "acumulado_actual": acumulado,
            "dias_transcurridos": dias_transcurridos,
            "dias_restantes": dias_restantes,
            "proyeccion_min": proyeccion_min,
            "proyeccion_max": proyeccion_max,
            "mes_anterior_total": mes_ant,
        }

    # ── 10. buscar_transacciones ──────────────────────────────────────────────

    def buscar_transacciones(self, query: str, limite: int = 10) -> list[dict]:
        if self.df.empty or not query:
            return []

        q = query.lower()
        mask = (
            self.df["comentarios_transaccion"].astype(str).str.lower().str.contains(q, na=False)
            | self.df["id_cliente"].astype(str).str.lower().str.contains(q, na=False)
        )
        found = self.df[mask].head(limite)
        if found.empty:
            return []

        return [
            {
                "fecha": str(row["fecha"].date()),
                "hora": row["hora"],
                "monto": round(float(row["monto"]), 2),
                "tipo_movimiento": row["tipo_movimiento"],
                "comentario": row["comentarios_transaccion"],
                "id_cliente": row["id_cliente"],
            }
            for _, row in found.iterrows()
        ]
