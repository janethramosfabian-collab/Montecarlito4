"""Pestañas 1 y 2: ingreso de escenarios (zonas) y supuestos de incertidumbre."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import Supuestos, limpiar_tabla, tabla_determinista, totales_deterministas, validar_tabla
from core.ejemplo import escenarios_ejemplo, tabla_vacia
from core.modelo import (
    COL_CERTEZA, COL_COSTO, COL_LEY, COL_PRECIO, COL_REC, COL_TMS, COL_ZONA, DIST_CERTEZA, DIST_PRECIO,
)


# ------------------------------------------------------------------ estado
def _nuevo_id() -> int:
    st.session_state["_next_id"] = st.session_state.get("_next_id", 0) + 1
    return st.session_state["_next_id"]


def cargar_ejemplo() -> None:
    st.session_state["esc"] = [
        {"id": _nuevo_id(), "nombre": n, "base": df.copy(), "ver": 0} for n, df in escenarios_ejemplo().items()
    ]
    st.session_state.pop("sim", None)


def init_estado() -> None:
    if "esc" not in st.session_state:
        cargar_ejemplo()


def _agregar(copiar: bool) -> None:
    esc = st.session_state["esc"]
    base = esc[-1]["base"].copy() if (copiar and esc) else tabla_vacia()
    esc.append({"id": _nuevo_id(), "nombre": f"Escenario {len(esc) + 1}", "base": base, "ver": 0})


def _eliminar(i: int) -> None:
    if len(st.session_state["esc"]) > 1:
        st.session_state["esc"].pop(i)


# ------------------------------------------------------------------ pestaña 1
_CONFIG = {
    COL_ZONA: st.column_config.TextColumn("Zona", required=True),
    COL_TMS: st.column_config.NumberColumn("TMS (t)", min_value=0, format="%.0f"),
    COL_LEY: st.column_config.NumberColumn("Ley (g-Au/t)", min_value=0, format="%.2f"),
    COL_REC: st.column_config.NumberColumn("Recuperación (%)", min_value=0, max_value=100, format="%.1f"),
    COL_PRECIO: st.column_config.NumberColumn("Precio (US$/oz)", min_value=0, format="%.0f"),
    COL_COSTO: st.column_config.NumberColumn("Costo explotación (US$/t)", min_value=0, format="%.1f"),
    COL_CERTEZA: st.column_config.NumberColumn("Certeza geológica (%)", min_value=0, max_value=100, format="%.0f"),
}

_FORMATOS = {
    "TMS": "{:,.0f}", "Ley (g/t)": "{:,.2f}", "Recuperación (%)": "{:,.1f}", "Onzas (oz)": "{:,.0f}",
    "Precio (US$/oz)": "{:,.0f}", "Valorizado (US$)": "{:,.0f}", "Costo explotación (US$/t)": "{:,.1f}",
    "Costo total (US$)": "{:,.0f}", "Utilidad (US$)": "{:,.0f}", "Certeza geológica (%)": "{:,.1f}",
}
def tabla_con_totales(df: pd.DataFrame) -> pd.DataFrame:
    det = tabla_determinista(df)
    fila = {"Zona": "TOTAL", "Costo explotación (US$/t)": float("nan"), **totales_deterministas(df)}
    return pd.concat([det, pd.DataFrame([fila])], ignore_index=True)


def render_escenarios() -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Dibuja las tablas editables y devuelve ({nombre: tabla limpia}, errores)."""
    st.markdown(
        "Ingresa **TMS, ley, recuperación, precio, costo de explotación y certeza geológica** de cada zona. "
        "Las onzas, el valorizado, el costo total y la utilidad se calculan solos con las fórmulas de tu Excel."
    )
    esc = st.session_state["esc"]
    entradas: dict[str, pd.DataFrame] = {}
    errores: list[str] = []
    vistos: set[str] = set()

    tabs = st.tabs([e["nombre"] for e in esc])
    for i, (tab, e) in enumerate(zip(tabs, esc)):
        with tab:
            c1, c2 = st.columns([5, 3], vertical_alignment="bottom")
            nombre = c1.text_input("Nombre del escenario", value=e["nombre"], key=f"nom_{e['id']}")
            e["nombre"] = nombre.strip() or f"Escenario {i + 1}"
            c2.button("🗑️ Eliminar escenario", key=f"del_{e['id']}", on_click=_eliminar, args=(i,),
                      disabled=len(esc) == 1, width="stretch")

            editado = st.data_editor(
                e["base"], column_config=_CONFIG, num_rows="dynamic", hide_index=True,
                width="stretch", key=f"ed_{e['id']}_{e['ver']}",
            )
            limpio = limpiar_tabla(editado)
            if e["nombre"] in vistos:
                errores.append(f"Hay dos escenarios llamados «{e['nombre']}»: cambia uno de los nombres.")
            vistos.add(e["nombre"])
            errs = validar_tabla(limpio, e["nombre"])
            errores += errs
            if errs:
                for m in errs:
                    st.error(m)
                continue
            entradas[e["nombre"]] = limpio

            st.markdown("**Cálculo determinístico** (igual que tu Excel; la fila TOTAL pondera con las TMS de este escenario)")
            st.dataframe(tabla_con_totales(limpio).style.format(_FORMATOS, na_rep=""), hide_index=True, width="stretch")

    b1, b2, b3 = st.columns([2, 2, 3])
    b1.button("➕ Añadir escenario (copia del último)", on_click=_agregar, args=(True,), width="stretch")
    b2.button("➕ Añadir escenario vacío", on_click=_agregar, args=(False,), width="stretch")
    b3.button("↺ Volver al ejemplo de 3 escenarios", on_click=cargar_ejemplo, width="stretch")
    if len(entradas) > 6:
        st.warning("Con más de 6 escenarios los colores de los gráficos se vuelven difíciles de distinguir.")
    return entradas, errores


# ------------------------------------------------------------------ pestaña 2
def render_supuestos(entradas: dict[str, pd.DataFrame]) -> Supuestos:
    st.markdown(
        "En **cada iteración** de Montecarlo se sortean dos cosas: el **precio** y la **certeza geológica** de cada zona. "
        "Todo lo demás (TMS, recuperación, costos) queda fijo, como indicó el ingeniero."
    )
    s = Supuestos()
    col_p, col_c, col_s = st.columns(3)

    with col_p:
        with st.container(border=True):
            st.subheader("💲 Precio")
            s.precio_dist = st.selectbox("Distribución", DIST_PRECIO, index=0, key="p_dist",
                                         help="El precio se sortea como un % de variación respecto al precio de la tabla.")
            if s.precio_dist == "Triangular":
                s.precio_min_pct = st.number_input("Mínimo (%)", value=-20.0, step=1.0, key="p_min")
                s.precio_moda_pct = st.number_input("Más probable (%)", value=0.0, step=1.0, key="p_moda")
                s.precio_max_pct = st.number_input("Máximo (%)", value=20.0, step=1.0, key="p_max")
            elif s.precio_dist == "Uniforme":
                s.precio_min_pct = st.number_input("Mínimo (%)", value=-20.0, step=1.0, key="p_min")
                s.precio_max_pct = st.number_input("Máximo (%)", value=20.0, step=1.0, key="p_max")
            else:
                s.precio_sd_pct = st.number_input(
                    "Desviación estándar (%)" if s.precio_dist == "Normal" else "Coef. de variación (%)",
                    value=10.0, min_value=0.1, step=1.0, key="p_sd")
            if entradas:
                ref = float(pd.concat(entradas.values())[COL_PRECIO].mean())
                if s.precio_dist in ("Triangular", "Uniforme"):
                    st.caption(f"Con US\\$ {ref:,.0f}/oz → entre US\\$ {ref * (1 + s.precio_min_pct / 100):,.0f} "
                               f"y US$ {ref * (1 + s.precio_max_pct / 100):,.0f}/oz.")
                else:
                    st.caption(f"Con US\\$ {ref:,.0f}/oz → ±1σ ≈ US\\$ {ref * s.precio_sd_pct / 100:,.0f}/oz.")

    with col_c:
        with st.container(border=True):
            st.subheader("🪨 Certeza geológica")
            s.certeza_dist = st.selectbox("Distribución", DIST_CERTEZA, index=0, key="c_dist",
                                          help="Alrededor del valor de la tabla de cada zona.")
            s.certeza_delta_pp = st.slider("Se mueve ± (puntos %)", 0, 30, 10, key="c_delta",
                                           help="Ej.: una zona con 75 % se sortea entre 65 % y 85 %.")
            efecto = st.radio(
                "¿Cómo afecta la certeza al resultado?",
                ["Dispersión de la ley (recomendado)", "Proporcional: ley × certeza sim. / certeza de tabla"],
                key="c_efecto",
                help="**Dispersión:** menos certeza = la ley real puede alejarse más del valor de la tabla (hacia arriba o abajo). "
                     "**Proporcional:** si la certeza simulada sale más baja que la de la tabla, la ley baja en esa proporción. "
                     "Confirma con el ingeniero cuál refleja mejor su criterio.")
            s.efecto_certeza = "dispersion" if efecto.startswith("Dispersión") else "proporcional"
            s.k_dispersion = st.slider("Efecto sobre la ley (k)", 0.0, 1.0, 0.5, 0.05, key="c_k",
                                       disabled=s.efecto_certeza == "proporcional",
                                       help="CV de la ley = k × (1 − certeza). Con k = 0.5, una zona con 50 % de "
                                            "certeza tiene la ley con ±25 % de dispersión y otra con 90 %, ±5 %.")
            s.rho_zonas = st.slider("Correlación entre zonas (ρ)", 0.0, 0.95, 0.0, 0.05, key="c_rho",
                                    help="0 = las zonas se comportan de forma independiente.")
            st.caption("⚠️ k y ± son supuestos de trabajo: conviene calibrarlos con tus datos de perforación o con el ingeniero.")

    with col_s:
        with st.container(border=True):
            st.subheader("⚙️ Simulación")
            s.n_iter = st.select_slider("Iteraciones", [1000, 2000, 5000, 10000, 20000, 50000], value=10000, key="n_it")
            s.semilla = int(st.number_input("Semilla (para repetir resultados)", value=42, step=1, key="semilla"))
            s.compartir_geologia = st.checkbox(
                "Misma zona = mismo sorteo en todos los escenarios", value=True, key="compartir",
                help="Recomendado: la Zona 1 del Escenario 1 y la del Escenario 2 son la misma roca, así que "
                     "salen iguales en cada iteración y la comparación entre escenarios es justa.")

    with st.expander("¿Cómo se calcula cada iteración?"):
        st.markdown(
            """
1. **Precio:** se sortea un factor (p. ej. 0.93 = −7 %) y el precio de cada zona se multiplica por él. Es el mismo para todos los escenarios (es el mercado).
2. **Certeza de cada zona:** se sortea alrededor del valor de la tabla.
3. **Ley real de cada zona:** `ley × F`.
   - *Dispersión:* `F` es lognormal con media 1 y dispersión `k × (1 − certeza sorteada)`. Menos certeza → ley más variable.
   - *Proporcional:* `F = certeza sorteada / certeza de la tabla`.
   En ambos casos `F` tiene media ≈ 1, así que no se sesga el resultado.
4. **Onzas** `= TMS × ley real × recuperación / 31.1035`, **valorizado** `= onzas × precio sorteado`, **costo** `= costo/t × TMS` y **utilidad** `= valorizado − costo`.
5. Se repite miles de veces. La **probabilidad** de un escenario es el % de iteraciones que cumplen el criterio (p. ej. utilidad ≥ umbral).
"""
        )
    mensajes = []
    if s.precio_dist == "Triangular" and not (s.precio_min_pct <= s.precio_moda_pct <= s.precio_max_pct):
        mensajes.append("Precio triangular: debe cumplirse mínimo ≤ más probable ≤ máximo.")
    if s.precio_dist == "Uniforme" and s.precio_min_pct >= s.precio_max_pct:
        mensajes.append("Precio uniforme: el mínimo debe ser menor que el máximo.")
    if s.precio_dist in ("Triangular", "Uniforme") and s.precio_min_pct <= -100:
        mensajes.append("El mínimo del precio no puede llegar a −100 %.")
    for m in mensajes:
        st.error(m)
    st.session_state["errores_supuestos"] = mensajes
    return s
