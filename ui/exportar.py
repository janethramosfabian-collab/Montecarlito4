"""Pestaña 4: exportar, replicar en @RISK y comparar contra @RISK."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from core.estadistica import comparar_con_externo
from core.exportar import excel_bytes, tabla_supuestos
from . import graficos as g


def render_exportar(entradas: dict[str, pd.DataFrame]) -> None:
    sim = st.session_state.get("sim")
    if sim is None:
        st.info("Primero corre una simulación con **▶ Simular** en la barra lateral.")
        return
    res, s = sim["resultados"], sim["supuestos"]
    tabla = st.session_state.get("tabla_resumen")

    st.subheader("📤 Exportar")
    st.caption("El Excel incluye supuestos, determinístico, resumen estocástico y las primeras 20,000 iteraciones de cada escenario.")
    firma = sim["firma"]
    if st.button("Preparar archivo Excel", key="prep_xlsx"):
        with st.spinner("Generando Excel…"):
            st.session_state["xlsx"] = (firma, excel_bytes(sim["entradas"], s, tabla, res))
    paquete = st.session_state.get("xlsx")
    if paquete and paquete[0] == firma:
        st.download_button("⬇️ Descargar Excel", paquete[1], file_name="simulacion_montecarlo.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    nombre = st.selectbox("CSV de iteraciones de un escenario", list(res), key="csv_esc")
    st.download_button("⬇️ Descargar CSV", res[nombre].to_csv(index=False).encode("utf-8"),
                       file_name=f"iteraciones_{nombre}.csv", mime="text/csv")

    st.divider()
    st.subheader("🔁 Replicar el modelo en @RISK")
    st.markdown("Para que los resultados sean comparables, usa **los mismos supuestos** en @RISK:")
    st.dataframe(tabla_supuestos(s), hide_index=True, width="stretch")
    with st.expander("Fórmulas para armar el mismo modelo en @RISK", expanded=False):
        pre = {
            "Triangular": "=RiskTriang(1+mín, 1+más_probable, 1+máx)   (mín, más probable y máx en decimales: −0.20, 0, 0.20)",
            "Uniforme": "=RiskUniform(1+mín, 1+máx)",
            "Normal": "=RiskNormal(1, σ, RiskTruncate(0.05,))",
            "Lognormal": "=RiskLognorm(1, CV)",
        }[s.precio_dist]
        cer = {
            "Triangular": "=RiskTriang(c−Δ, c, c+Δ)   (c = certeza de la tabla, Δ = ± puntos; acotada a 0–100 %)",
            "Uniforme": "=RiskUniform(c−Δ, c+Δ)",
            "Normal": "=RiskNormal(c, Δ, RiskTruncate(0,1))",
        }[s.certeza_dist]
        st.markdown(
            f"""
**Una sola celda de precio** (el mismo mercado para los 3 escenarios):
`Factor precio` {pre}

**Por cada zona** (si «misma zona = mismo sorteo» está activo, usa la *misma* celda en los 3 escenarios):
- `Certeza zona` {cer}
- `Factor ley zona` {('`=RiskLognorm(1, ' + str(s.k_dispersion) + ' * (1 − Certeza zona))`') if s.efecto_certeza == 'dispersion' else '`= Certeza zona / certeza de la tabla`'}

**Cálculo (igual que el Excel, por zona):**
- Onzas `= TMS × Ley × Factor ley × Recuperación / 31.1035`
- Valorizado `= Precio × Factor precio × Onzas`
- Costo total `= Costo explotación × TMS`
- Utilidad `= Valorizado − Costo total` y en la celda total: `=RiskOutput("Utilidad Escenario 1") + suma de utilidades`

**Configuración de @RISK:** {s.n_iter:,} iteraciones, muestreo *Latin Hypercube*. {'Para la correlación ρ = ' + str(s.rho_zonas) + ' entre las leyes de las zonas usa una matriz RiskCorrmat con ese valor.' if s.rho_zonas > 0 else ''}

**Cómo comparar:** las medias deben coincidir dentro de ~3 errores estándar. Con semillas distintas no esperes igualdad decimal a decimal.
"""
        )

    st.divider()
    st.subheader("⚖️ Comparar con los resultados de @RISK")
    st.caption("Exporta desde @RISK los valores simulados de la utilidad (una columna) a Excel o CSV y súbelos aquí.")
    arch = st.file_uploader("Archivo con las iteraciones de @RISK", type=["csv", "xlsx"], key="up_risk")
    if arch is None:
        return
    try:
        ext = pd.read_csv(arch, sep=None, engine="python") if arch.name.lower().endswith(".csv") else pd.read_excel(arch)
    except Exception as e:  # noqa: BLE001
        st.error(f"No pude leer el archivo: {e}")
        return
    num = [c for c in ext.columns if pd.api.types.is_numeric_dtype(ext[c])]
    if not num:
        st.error("El archivo no tiene columnas numéricas.")
        return
    c1, c2 = st.columns(2)
    esc = c1.selectbox("Escenario a comparar", list(res), key="cmp_esc")
    col = c2.selectbox("Columna de @RISK", num, key="cmp_col")
    externo = ext[col].dropna().to_numpy(dtype=float)
    propio = res[esc]["Utilidad (US$)"].to_numpy()
    umbral = st.session_state.get("umbrales", {}).get(esc, float(np.median(propio)))
    out = comparar_con_externo(propio, externo, umbral)
    st.dataframe(out, hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(format="%.4f") for c in out.columns[1:]})
    z = out.loc[out["Estadístico"] == "Media", "Diferencia en errores estándar"].iloc[0]
    if abs(z) <= 3:
        st.success(f"Las medias son compatibles (diferencia = {z:+.2f} errores estándar).")
    else:
        st.warning(f"Las medias difieren en {z:+.1f} errores estándar: revisa que los supuestos sean los mismos en ambos programas.")
    st.plotly_chart(g.fig_comparar(propio, externo, umbral), width="stretch", key="graf_cmp")
