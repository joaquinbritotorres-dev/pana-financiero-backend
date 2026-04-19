from __future__ import annotations
import re
from datetime import timedelta
import pandas as pd

CLIENTE_MAP = [
    "Juan Pérez", "María García", "José Loor", "Carmen Rodríguez", "Luis Chiriboga",
    "Rosa Espinoza", "Carlos Vera", "Ana Cevallos", "Jorge Intriago", "Elena Mendoza",
    "Pedro Castillo", "Martha Villavicencio", "Francisco Noboa", "Lucía Guerrero", "Manuel Valdivieso",
    "Teresa Aguiar", "Ricardo Freire", "Silvia Ortiz", "Wilson Caicedo", "Gladys Murillo",
    "Andrés Cárdenas", "Isabel Solórzano", "Fabian Paredes", "Mónica Figueroa", "Diego Santamaría"
]


class PanaAnalytics:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        if not df.empty:
            self._hoy = df["fecha"].max().normalize()
        else:
            self._hoy = pd.Timestamp("2025-01-01")

    def _get_cliente_nombre(self, id_cliente: str) -> str:
        if not id_cliente or not isinstance(id_cliente, str):
            return "Consumidor Final"
        try:
            # Extraer el número del ID (ej: CLI-0040 -> 40)
            num = int(re.sub(r"[^0-9]", "", id_cliente))
            return CLIENTE_MAP[num % len(CLIENTE_MAP)]
        except:
            return "Caserito Anónimo"

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

    def _week_range_aligned(self, offset: int = 0) -> tuple[pd.Timestamp, pd.Timestamp]:
        monday_this = self._hoy - timedelta(days=self._hoy.dayofweek)
        days_elapsed = (self._hoy - monday_this).days
        if offset == 0:
            return monday_this, self._hoy
        else:
            monday_prev = monday_this - timedelta(weeks=offset)
            return monday_prev, monday_prev + timedelta(days=days_elapsed)

    def _month_range_aligned(self, offset: int = 0) -> tuple[pd.Timestamp, pd.Timestamp]:
        first_this = self._hoy.replace(day=1).normalize()
        days_elapsed = (self._hoy - first_this).days
        if offset == 0:
            return first_this, self._hoy
        else:
            first_prev = (first_this - pd.DateOffset(months=offset)).normalize()
            end_prev = first_prev + timedelta(days=days_elapsed)
            last_prev = (first_prev + pd.DateOffset(months=1) - timedelta(days=1)).normalize()
            return first_prev, min(end_prev, last_prev)

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

        days_elapsed = (self._hoy - (self._hoy - timedelta(days=self._hoy.dayofweek))).days + 1

        if periodo == "semana":
            s_act, e_act = self._week_range_aligned(0)
            s_ant, e_ant = self._week_range_aligned(1)
            label_act = f"esta semana ({days_elapsed} días)"
            label_ant = f"mismos {days_elapsed} días de la semana anterior"
        else:
            s_act, e_act = self._month_range_aligned(0)
            s_ant, e_ant = self._month_range_aligned(1)
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
            start, end = self._week_range_aligned(0)
        else:
            start, end = self._month_range_aligned(0)

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
            start, end = self._week_range_aligned(0)
        else:
            start, end = self._month_range_aligned(0)

        chunk = self._ingresos(self._filter_period(self.df, start, end))
        if chunk.empty:
            return []

        grp = chunk.groupby("id_cliente")["monto"].agg(["sum", "count"]).reset_index()
        grp.columns = ["id_cliente", "total_gastado", "num_visitas"]
        grp["ticket_promedio"] = (grp["total_gastado"] / grp["num_visitas"]).round(2)
        grp["total_gastado"] = grp["total_gastado"].round(2)
        top = grp.sort_values("total_gastado", ascending=False).head(limite)
        
        # Agregar nombres legibles
        result = top.to_dict("records")
        for r in result:
            r["nombre_cliente"] = self._get_cliente_nombre(r["id_cliente"])
        return result

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
                "nombre_cliente": self._get_cliente_nombre(cliente),
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

        ing["hora_int"] = pd.to_numeric(
            ing["hora"].str.split(":").str[0], errors="coerce"
        ).fillna(0).astype(int)
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
            start, end = self._week_range_aligned(0)
        else:
            start, end = self._month_range_aligned(0)

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
            start, end = self._week_range_aligned(0)
        else:
            start, end = self._month_range_aligned(0)

        chunk = self._egresos(self._filter_period(self.df, start, end))
        if chunk.empty:
            return {"total": 0, "num_tx": 0, "top_categorias": [], "sin_comentario": {"num_tx": 0, "monto": 0}}

        total = round(float(chunk["monto"].sum()), 2)
        num_tx = int(len(chunk))

        con_com = chunk[chunk["comentarios_transaccion"].astype(str).str.strip() != ""].copy()
        sin_com = chunk[chunk["comentarios_transaccion"].astype(str).str.strip() == ""]

        import unicodedata

        def _norm(s: str) -> str:
            s = unicodedata.normalize("NFD", str(s).lower())
            s = "".join(c for c in s if unicodedata.category(c) != "Mn")
            s = re.sub(r"[^a-z0-9\s]", " ", s)
            return re.sub(r"\s+", " ", s).strip()

        con_com["_categoria"] = con_com["comentarios_transaccion"].apply(_norm)

        grp = con_com.groupby("_categoria").agg(
            monto=("monto", "sum"),
            num_tx=("monto", "count"),
            ejemplo=("comentarios_transaccion", "first"),
        ).reset_index()
        grp = grp.sort_values("monto", ascending=False).head(5)

        return {
            "total": total,
            "num_tx": num_tx,
            "top_categorias": [
                {
                    "nombre": row["ejemplo"],
                    "monto": round(float(row["monto"]), 2),
                    "num_tx": int(row["num_tx"]),
                }
                for _, row in grp.iterrows()
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

        start_14 = self._hoy - timedelta(days=13)
        ultimos14 = self._ingresos(self._filter_period(self.df, start_14, self._hoy))
        dias_con_datos = int(ultimos14["fecha"].nunique()) or 1
        promedio_diario = float(ultimos14["monto"].sum()) / dias_con_datos

        dias_transcurridos = int((self._hoy - start_mes).days) + 1
        dias_en_mes = int((end_mes - start_mes).days) + 1
        dias_restantes = max(0, dias_en_mes - dias_transcurridos)

        mes_cerrado = dias_restantes == 0

        if mes_cerrado:
            proyeccion_min = acumulado
            proyeccion_max = acumulado
        else:
            proyeccion_min = round(acumulado + promedio_diario * 0.8 * dias_restantes, 2)
            proyeccion_max = round(acumulado + promedio_diario * 1.2 * dias_restantes, 2)

        s_ant, e_ant = self._month_range(1)
        mes_ant = round(float(self._ingresos(self._filter_period(self.df, s_ant, e_ant))["monto"].sum()), 2)

        return {
            "acumulado_actual": acumulado,
            "dias_transcurridos": dias_transcurridos,
            "dias_restantes": dias_restantes,
            "proyeccion_min": proyeccion_min,
            "proyeccion_max": proyeccion_max,
            "mes_anterior_total": mes_ant,
            "mes_cerrado": mes_cerrado,
            "mes": start_mes.strftime("%B %Y"),
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
        found = self.df[mask].sort_values("fecha", ascending=False).head(limite)
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
                "nombre_cliente": self._get_cliente_nombre(row["id_cliente"]),
            }
            for _, row in found.iterrows()
        ]

    # ── 11. capacidad_prestamo ────────────────────────────────────────────────

    def capacidad_prestamo(self) -> dict:
        """
        Calcula si el comerciante puede pedir un préstamo
        y cuánto. Usa los últimos 6 meses de datos para
        que sea más representativo.
        """
        if self.df.empty:
            return {}

        # Últimos 6 meses desde el último dato
        hoy = self._hoy
        hace_6_meses = hoy - pd.DateOffset(months=6)

        periodo = self._filter_period(self.df, hace_6_meses, hoy)

        ingresos_6m = round(float(
            self._ingresos(periodo)["monto"].sum()), 2)
        egresos_6m = round(float(
            self._egresos(periodo)["monto"].sum()), 2)
        utilidad_6m = round(ingresos_6m - egresos_6m, 2)

        # Promedios mensuales
        meses = max(1, int((hoy - hace_6_meses).days / 30))
        ingreso_mensual = round(ingresos_6m / meses, 2)
        egreso_mensual = round(abs(egresos_6m) / meses, 2)
        utilidad_mensual = round(utilidad_6m / meses, 2)

        # Capacidad de pago: 40% de la utilidad mensual
        # (criterio estándar de bancos ecuatorianos)
        capacidad_pago = round(utilidad_mensual * 0.40, 2)

        # Monto estimado de préstamo
        # Los bancos dan entre 12 y 24 cuotas típicamente
        prestamo_conservador = round(capacidad_pago * 12, 2)
        prestamo_optimo = round(capacidad_pago * 18, 2)

        # Semáforo de salud financiera
        if utilidad_mensual > 0 and capacidad_pago > 50:
            estado = "verde"
            mensaje = "Tu negocio está en buena posición para pedir un préstamo"
        elif utilidad_mensual > 0 and capacidad_pago > 0:
            estado = "amarillo"
            mensaje = "Puedes pedir un préstamo pequeño, tu margen es ajustado"
        else:
            estado = "rojo"
            mensaje = "Por ahora no es recomendable pedir un préstamo"

        return {
            "periodo_analizado": "últimos 6 meses",
            "ingresos_totales_6m": ingresos_6m,
            "egresos_totales_6m": abs(egresos_6m),
            "utilidad_total_6m": utilidad_6m,
            "ingreso_mensual_promedio": ingreso_mensual,
            "egreso_mensual_promedio": egreso_mensual,
            "utilidad_mensual_promedio": utilidad_mensual,
            "capacidad_pago_mensual": capacidad_pago,
            "prestamo_estimado_minimo": prestamo_conservador,
            "prestamo_estimado_maximo": prestamo_optimo,
            "estado": estado,
            "mensaje": mensaje,
            "documentos_para_banco": [
                "Cédula de identidad",
                "RUC activo",
                "Este reporte de Pana Financiero",
                "Últimos 3 meses de movimientos Deuna"
            ]
        }

    # ── 12. ultima_transaccion ────────────────────────────────────────────────

    def ultima_transaccion(self, tipo: str = "ingreso") -> dict:
        if self.df.empty:
            return {}
        if tipo == "ingreso":
            subset = self._ingresos(self.df)
        elif tipo == "egreso":
            subset = self._egresos(self.df)
        else:
            subset = self.df

        if subset.empty:
            return {}

        row = subset.sort_values(["fecha", "hora"], ascending=False).iloc[0]
        return {
            "fecha": str(row["fecha"].date()),
            "hora": row["hora"],
            "monto": round(float(row["monto"]), 2),
            "tipo_movimiento": row["tipo_movimiento"],
            "id_cliente": row["id_cliente"],
            "nombre_cliente": self._get_cliente_nombre(row["id_cliente"]),
            "comentario": row["comentarios_transaccion"],
        }

    # ── 13. comisiones_deuna ──────────────────────────────────────────────────

    def comisiones_deuna(self, periodo: str = "mes") -> dict:
        """
        Calcula cuánto se fue en comisiones de Deuna (2% por transacción de ingreso).
        """
        if self.df.empty:
            return {}

        if periodo == "semana":
            start, end = self._week_range_aligned(0)
        else:
            start, end = self._month_range_aligned(0)

        chunk = self._ingresos(self._filter_period(self.df, start, end))

        if chunk.empty:
            return {
                "periodo": periodo,
                "desde": str(start.date()),
                "hasta": str(end.date()),
                "total_ingresos": 0,
                "num_transacciones": 0,
                "tasa_comision_pct": 2.0,
                "total_comision": 0,
                "promedio_comision_por_tx": 0,
            }

        total_ingresos = round(float(chunk["monto"].sum()), 2)
        num_tx = int(len(chunk))
        tasa = 0.02
        total_comision = round(total_ingresos * tasa, 2)
        promedio_por_tx = round(total_comision / num_tx, 4) if num_tx else 0

        return {
            "periodo": periodo,
            "desde": str(start.date()),
            "hasta": str(end.date()),
            "total_ingresos": total_ingresos,
            "num_transacciones": num_tx,
            "tasa_comision_pct": 2.0,
            "total_comision": total_comision,
            "promedio_comision_por_tx": promedio_por_tx,
        }
