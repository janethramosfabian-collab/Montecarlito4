"""Pestaña 3: resultados determinísticos y estocásticos, por escenario."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from core import totales_deterministas
from core.estadistica import COL_U, prob_mayor_igual, resumen, sensibilidad, umbral_escenario
from . import graficos as g

COL_O = "Onzas (oz)"


def _fmt_det(entradas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """La columna 'Total' del Excel, para cada escenario."""
    tot = {n: totales_deterministas(df) for n, df in entradas.items()}
    return pd.DataFrame(tot)


def render_resultados(entradas: dict[str, pd.DataFrame]) -> None:
    nombres = list(entradas)
    det = _fmt_det(entradas)
    st.subheader("1 · Caso determinístico")
    c1, c2 = st.columns([5, 4])
    with c1:
        st.plotly_chart(
            g.fig_determinista(nombres, [det[n]["Utilidad (US$)"] for n in nombres],
                               [det[n]["Onzas (oz)"] for n in nombres]),
            width="stretch", key="graf_det")
    with c2:
        st.markdown("**Totales por escenario** (como la columna *Total* del Excel)")
        st.dataframe(det.style.format("{:,.2f}"), width="stretch")
        st.caption("Este caso usa un solo valor de precio y de certeza: no dice qué tan probable es cumplirlo.")

    sim = st.session_state.get("sim")
    st.divider()
    st.subheader("2 · Caso estocástico (Montecarlo)")
    if sim is None:
        st.info("Configura los escenarios y los supuestos y pulsa **▶ Simular** en la barra lateral.")
        return
    if sim["firma"] != st.session_state.get("firma_actual"):
        st.warning("Cambiaste datos o supuestos después de la última simulación. Pulsa **▶ Simular** para actualizar; "
                   "abajo se muestran los resultados anteriores.")

    res, entradas_s, s = sim["resultados"], sim["entradas"], sim["supuestos"]
    orden = list(res)
    det_u = {n: totales_deterministas(entradas_s[n])["Utilidad (US$)"] for n in orden}
    div, suf = g.escala(list(det_u.values()))

    # ---- criterio de éxito (umbral)
    with st.container(border=True):
        st.markdown("**¿Qué significa «cumplir»?** Define el umbral de utilidad con el que se calcula la probabilidad.")
        k1, k2 = st.columns([3, 4], vertical_alignment="center")
        modo_txt = k1.radio("Criterio", ["% del determinístico de cada escenario", "Monto fijo para todos"],
                            key="u_modo", label_visibility="collapsed")
        if modo_txt.startswith("%"):
            modo = "pct"
            valor = k2.slider("Umbral (% del valor determinístico)", 50, 120, 90, 1, key="u_pct",
                              help="100 % = igualar el valor determinístico. 90 % = no perder más del 10 %.")
        else:
            modo = "monto"
            por_defecto = round(min(det_u.values()) * 0.9 / div, 2)
            v = k2.number_input(f"Monto mínimo de utilidad (US$ {suf})", value=por_defecto,
                                step=max(round(por_defecto / 50, 2), 0.01), key=f"u_monto_{suf}")
            valor = v * div
    umbrales = {n: umbral_escenario(det_u[n], modo, valor) for n in orden}
    st.session_state["umbrales"] = umbrales

    tabla = resumen(res, det_u, modo, valor)

    # ---- gráficos comparativos
    a, b = st.columns(2)
    with a:
        st.plotly_chart(
            g.fig_probabilidad(orden, [det_u[n] for n in orden], tabla["P5"].tolist(), tabla["P95"].tolist(),
                               tabla["Prob. ≥ umbral"].tolist(), [umbrales[n] for n in orden]),
            width="stretch", key="graf_prob")
    with b:
        st.plotly_chart(g.fig_scurves(res, COL_U, umbrales, orden), width="stretch", key="graf_scurve")

    # ---- lectura para decidir
    mejor_prob = tabla.loc[tabla["Prob. ≥ umbral"].idxmax()]
    mejor_media = tabla.loc[tabla["Media (US$)"].idxmax()]
    mas_ganador = tabla.loc[tabla["Prob. de ser el mejor"].idxmax()]
    menos_riesgo = tabla.loc[tabla["Prob. de pérdida (<0)"].idxmin()]
    st.markdown("**Lectura rápida**")
    st.markdown(
        f"- Mayor utilidad esperada: **{mejor_media['Escenario']}** (US\\$ {mejor_media['Media (US$)'] / div:,.2f} {suf}).\n"
        f"- Mayor probabilidad de cumplir el umbral: **{mejor_prob['Escenario']}** ({mejor_prob['Prob. ≥ umbral']:.1%}).\n"
        f"- Es el mejor en más iteraciones: **{mas_ganador['Escenario']}** ({mas_ganador['Prob. de ser el mejor']:.1%} de las veces).\n"
        f"- Menor probabilidad de pérdida: **{menos_riesgo['Escenario']}** ({menos_riesgo['Prob. de pérdida (<0)']:.2%})."
    )

    mostrar = tabla.copy()
    dinero = ["Determinístico (US$)", "Media (US$)", "Desv. estándar (US$)", "P5", "P10", "P50", "P90", "P95",
              "Umbral (US$)", "Error estándar de la media (US$)"]
    for c in dinero:
        mostrar[c] = mostrar[c] / div
    renombre = {c: (c.replace("(US$)", f"(US$ {suf})") if "(US$)" in c else f"{c} (US$ {suf})") for c in dinero}
    mostrar = mostrar.rename(columns=renombre)
    cfg = {nuevo: st.column_config.NumberColumn(format="%.3f") for nuevo in renombre.values()}
    for c in ["Prob. ≥ umbral", "Prob. de pérdida (<0)", "Prob. de ser el mejor"]:
        mostrar[c] = mostrar[c] * 100
        cfg[c] = st.column_config.NumberColumn(c, format="%.1f%%")
    cfg["Onzas medias (oz)"] = st.column_config.NumberColumn(format="%.0f")
    st.dataframe(mostrar, column_config=cfg, hide_index=True, width="stretch")
    st.caption(f"{s.n_iter:,} iteraciones · semilla {s.semilla}. Con esta cantidad, la media tiene un error estándar de "
               f"≈ US\\$ {tabla['Error estándar de la media (US$)'].max() / div:,.3f} {suf}.")
    st.session_state["tabla_resumen"] = tabla

    # ---- detalle por escenario
    st.divider()
    st.subheader("3 · Detalle por escenario")
    tabs = st.tabs([f"🔍 {n}" for n in orden])
    for i, (tab, n) in enumerate(zip(tabs, orden)):
        with tab:
            _detalle(n, i, res[n], entradas_s[n], det_u[n], umbrales[n], div, suf)


def _detalle(n, i, df, entrada, det_u, umbral, div, suf) -> None:
    x = df[COL_U].to_numpy()
    p5, p50, p95 = np.percentile(x, [5, 50, 95])
    m = st.columns(5)
    m[0].metric("Determinístico", f"{det_u / div:,.2f} {suf}")
    m[1].metric("Media simulada", f"{x.mean() / div:,.2f} {suf}")
    m[2].metric("P5 (caso adverso)", f"{p5 / div:,.2f} {suf}")
    m[3].metric("P95 (caso favorable)", f"{p95 / div:,.2f} {suf}")
    m[4].metric("Prob. de pérdida", f"{np.mean(x < 0):.2%}")

    st.markdown("##### 🎚️ Barra de probabilidad: elige un rango de utilidad y mira qué tan probable es")
    lo_min, hi_max = float(x.min()) / div, float(x.max()) / div
    paso = max((hi_max - lo_min) / 400, 1e-6)
    ini = (float(np.clip(umbral / div, lo_min, hi_max)), hi_max)
    rango = st.slider(f"Rango de utilidad (US$ {suf})", lo_min, hi_max, ini, step=paso,
                      key=f"rng_{n}_{int(umbral)}", format="%.2f")
    lo, hi = rango[0] * div, rango[1] * div
    dentro = float(np.mean((x >= lo) & (x <= hi)))
    c = st.columns(3)
    c[0].metric("Probabilidad dentro del rango", f"{dentro:.1%}")
    c[1].metric("Por debajo del rango", f"{np.mean(x < lo):.1%}")
    c[2].metric("Por encima del rango", f"{np.mean(x > hi):.1%}")

    conf = st.slider("O al revés: nivel de confianza deseado (%)", 50, 99, 80, key=f"conf_{n}",
                     help="Monto de utilidad que se supera con esa probabilidad.")
    st.info(f"Con **{conf}% de confianza**, la utilidad de **{n}** será de al menos "
            f"**US\\$ {np.percentile(x, 100 - conf) / div:,.2f} {suf}**.")

    a, b = st.columns(2)
    with a:
        st.plotly_chart(g.fig_histograma(x, (lo, hi), det_u, g.color_de(i), f"Distribución de la utilidad · {n}"),
                        width="stretch", key=f"hist_{n}")
    with b:
        sens = sensibilidad(df)
        if sens.empty:
            st.info("No hay variables inciertas para mostrar sensibilidad.")
        else:
            st.plotly_chart(g.fig_tornado(sens), width="stretch", key=f"torn_{n}")

    st.markdown("**Por zona**")
    filas = []
    for _, z in entrada.iterrows():
        nombre = str(z["Zona"])
        col = f"Utilidad {nombre}"
        oz = z["TMS"] * z["Ley (g/t)"] * z["Recuperación (%)"] / 100 / 31.1035
        util_det = oz * z["Precio (US$/oz)"] - z["Costo explotación (US$/t)"] * z["TMS"]
        filas.append({
            "Zona": nombre, "Certeza tabla (%)": z["Certeza geológica (%)"],
            "Certeza simulada media (%)": df[f"Certeza {nombre}"].mean(),
            f"Utilidad determinística (US$ {suf})": util_det / div,
            f"Utilidad media (US$ {suf})": df[col].mean() / div,
            f"P5 (US$ {suf})": df[col].quantile(0.05) / div,
            f"P95 (US$ {suf})": df[col].quantile(0.95) / div,
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch",
                 column_config={k: st.column_config.NumberColumn(format="%.2f")
                                for k in pd.DataFrame(filas).columns if k != "Zona"})
    st.caption(f"Onzas recuperables: media {df[COL_O].mean():,.0f} oz · P5 {df[COL_O].quantile(.05):,.0f} · "
               f"P95 {df[COL_O].quantile(.95):,.0f}.")
