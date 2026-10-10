"""Gráficos Plotly: un eje por panel, color fijo por escenario, rejilla discreta."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Paleta categórica en orden fijo (tema oscuro). Los 3 primeros escenarios validan entre sí;
# cada escenario conserva SIEMPRE su color en toda la app.
PALETA = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
TEXTO = "#c3c2b7"
TEXTO_FUERTE = "#f0efec"
REJILLA = "rgba(240,239,236,0.10)"
POSITIVO, NEGATIVO = "#3987e5", "#e66767"


def color_de(i: int) -> str:
    return PALETA[i % len(PALETA)]


def rgba(hex_: str, alpha: float) -> str:
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def escala(valores) -> tuple[float, str]:
    """Divisor y sufijo legibles para US$ (M, k o unidades)."""
    m = float(np.nanmax(np.abs(valores))) if len(valores) else 0.0
    if m >= 1e6:
        return 1e6, "M"
    if m >= 1e3:
        return 1e3, "k"
    return 1.0, ""


def _base(fig: go.Figure, alto: int = 380, titulo: str | None = None) -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, x=0.0, font=dict(size=15, color=TEXTO_FUERTE)) if titulo else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXTO, size=13),
        height=alto,
        margin=dict(l=10, r=10, t=50 if titulo else 20, b=10),
        legend=dict(orientation="h", y=-0.18, x=0, font=dict(color=TEXTO)),
        hoverlabel=dict(bgcolor="#2a2a28", font=dict(color=TEXTO_FUERTE)),
    )
    fig.update_xaxes(gridcolor=REJILLA, zerolinecolor="rgba(240,239,236,0.25)", linecolor=REJILLA)
    fig.update_yaxes(gridcolor=REJILLA, zerolinecolor="rgba(240,239,236,0.25)", linecolor=REJILLA)
    return fig


# ----------------------------------------------------------------------------------
def fig_determinista(nombres, utilidad, onzas) -> go.Figure:
    """Caso determinístico: utilidad (arriba) y onzas recuperables (abajo)."""
    div, suf = escala(utilidad)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, row_heights=[0.6, 0.4])
    for i, n in enumerate(nombres):
        fig.add_bar(
            x=[n], y=[utilidad[i] / div], name=n, marker_color=color_de(i), width=0.38, row=1, col=1,
            text=[f"{utilidad[i] / div:,.2f}"], textposition="outside", textfont=dict(color=TEXTO_FUERTE),
            hovertemplate=f"<b>{n}</b><br>Utilidad: US$ %{{y:,.3f}} {suf}<extra></extra>",
        )
        fig.add_bar(
            x=[n], y=[onzas[i]], name=n, marker_color=color_de(i), width=0.38, row=2, col=1, showlegend=False,
            text=[f"{onzas[i]:,.0f}"], textposition="outside", textfont=dict(color=TEXTO_FUERTE),
            hovertemplate=f"<b>{n}</b><br>Onzas: %{{y:,.0f}} oz<extra></extra>",
        )
    fig.update_yaxes(title_text=f"Utilidad (US$ {suf})".replace(" )", ")"), rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title_text="Onzas recuperables (oz)", rangemode="tozero", row=2, col=1)
    ymax = max(utilidad) / div
    fig.update_yaxes(range=[0, ymax * 1.18], row=1, col=1)
    fig.update_yaxes(range=[0, max(onzas) * 1.25], row=2, col=1)
    fig.update_layout(barmode="overlay")
    return _base(fig, 470, "Caso determinístico: un solo resultado por escenario")


def fig_probabilidad(nombres, utilidad_det, p5, p95, probs, umbrales) -> go.Figure:
    """Toque estocástico: utilidad con su rango P5–P95 (arriba) y probabilidad de cumplir el umbral (abajo)."""
    div, suf = escala(utilidad_det)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, row_heights=[0.55, 0.45])
    for i, n in enumerate(nombres):
        c = color_de(i)
        fig.add_bar(
            x=[n], y=[utilidad_det[i] / div], name=n, marker_color=rgba(c, 0.45), width=0.38, row=1, col=1,
            hovertemplate=f"<b>{n}</b><br>Determinístico: US$ %{{y:,.3f}} {suf}<extra></extra>",
        )
        fig.add_scatter(
            x=[n, n], y=[p5[i] / div, p95[i] / div], mode="lines+markers", name=n, showlegend=False,
            line=dict(color=c, width=3), marker=dict(size=9, color=c, line=dict(color="#1a1a19", width=2)),
            hovertemplate=f"<b>{n}</b><br>%{{y:,.3f}} {suf} (P5 → P95)<extra></extra>", row=1, col=1,
        )
        fig.add_bar(
            x=[n], y=[probs[i] * 100], name=n, marker_color=c, width=0.38, row=2, col=1, showlegend=False,
            text=[f"{probs[i] * 100:,.1f}%"], textposition="outside", textfont=dict(color=TEXTO_FUERTE),
            hovertemplate=(f"<b>{n}</b><br>Prob. de utilidad ≥ US$ {umbrales[i] / div:,.2f} {suf}: "
                           f"%{{y:,.1f}}%<extra></extra>"),
        )
    fig.update_yaxes(title_text=f"Utilidad (US$ {suf})", row=1, col=1)
    fig.update_yaxes(title_text="Probabilidad de cumplir (%)", range=[0, 118], row=2, col=1)
    fig.update_layout(barmode="overlay")
    return _base(fig, 470, "Con incertidumbre: rango P5–P95 y probabilidad de cumplir")


def fig_scurves(resultados: dict, columna: str, umbrales: dict[str, float], orden: list[str]) -> go.Figure:
    """Curvas de excedencia P(X ≥ x). El rombo marca la probabilidad en el umbral de cada escenario."""
    todo = np.concatenate([resultados[n][columna].to_numpy() for n in orden])
    div, suf = escala(todo)
    fig = go.Figure()
    for i, n in enumerate(orden):
        x = np.sort(resultados[n][columna].to_numpy())
        p = 1.0 - np.arange(len(x)) / len(x)
        paso = max(1, len(x) // 400)
        fig.add_scatter(
            x=x[::paso] / div, y=p[::paso] * 100, mode="lines", name=n, line=dict(color=color_de(i), width=2.5),
            hovertemplate=f"<b>{n}</b><br>US$ %{{x:,.2f}} {suf}<br>Prob. de superarlo: %{{y:,.1f}}%<extra></extra>",
        )
        um = umbrales[n]
        pu = float(np.mean(x >= um)) * 100
        fig.add_scatter(
            x=[um / div], y=[pu], mode="markers", showlegend=False,
            marker=dict(symbol="diamond", size=11, color=color_de(i), line=dict(color="#1a1a19", width=2)),
            hovertemplate=f"<b>{n}</b> · umbral US$ %{{x:,.2f}} {suf}<br>Prob. ≥ umbral: %{{y:,.1f}}%<extra></extra>",
        )
    fig.update_xaxes(title_text=f"Utilidad (US$ {suf})")
    fig.update_yaxes(title_text="Probabilidad de superar el valor (%)", range=[0, 100])
    return _base(fig, 400, "Curvas de excedencia (◆ = umbral de cada escenario)")


def fig_histograma(x: np.ndarray, rango: tuple[float, float], det: float, color: str, titulo: str,
                   etiqueta: str = "Utilidad") -> go.Figure:
    """Histograma con las barras dentro del rango resaltadas (la 'barra de probabilidad')."""
    div, suf = escala(x)
    cuentas, bordes = np.histogram(x, bins=60)
    centros = (bordes[:-1] + bordes[1:]) / 2
    dentro = (centros >= rango[0]) & (centros <= rango[1])
    colores = [rgba(color, 0.95) if d else rgba(color, 0.25) for d in dentro]
    fig = go.Figure(go.Bar(
        x=centros / div, y=cuentas / len(x) * 100, marker_color=colores, width=(bordes[1] - bordes[0]) / div * 0.96,
        hovertemplate=f"US$ %{{x:,.2f}} {suf}<br>%{{y:,.2f}}% de las iteraciones<extra></extra>", showlegend=False,
    ))
    for v in rango:
        fig.add_vline(x=v / div, line_dash="dash", line_color=TEXTO_FUERTE, line_width=1.5)
    fig.add_vline(x=det / div, line_color="#c98500", line_width=2.5, annotation_text="Determinístico",
                  annotation_position="top", annotation_font=dict(color="#c98500"))
    fig.update_xaxes(title_text=f"{etiqueta} (US$ {suf})")
    fig.update_yaxes(title_text="% de iteraciones")
    return _base(fig, 360, titulo)


def fig_tornado(df, titulo: str = "Sensibilidad (correlación de rangos de Spearman)") -> go.Figure:
    nombres = []
    for v in df["Variable"]:
        v = (v.replace("Factor precio", "Precio").replace("Factor ley ", "Ley · ").replace("Certeza ", "Certeza · "))
        nombres.append(v)
    fig = go.Figure(go.Bar(
        x=df["Correlación"], y=nombres, orientation="h", width=0.55,
        marker_color=[POSITIVO if v >= 0 else NEGATIVO for v in df["Correlación"]],
        text=[f"{v:+.2f}" for v in df["Correlación"]], textposition="outside", textfont=dict(color=TEXTO_FUERTE),
        hovertemplate="%{y}<br>Correlación con la utilidad: %{x:+.3f}<extra></extra>",
    ))
    fig.update_xaxes(range=[-1.1, 1.1], title_text="Correlación con la utilidad")
    return _base(fig, max(260, 60 + 42 * len(df)), titulo)


def fig_comparar(propio: np.ndarray, externo: np.ndarray, umbral: float) -> go.Figure:
    div, suf = escala(np.concatenate([propio, externo]))
    fig = go.Figure()
    for nombre, x, c in [("Plataforma", propio, PALETA[0]), ("@RISK / externo", externo, PALETA[1])]:
        xs = np.sort(x)
        p = 1.0 - np.arange(len(xs)) / len(xs)
        paso = max(1, len(xs) // 400)
        fig.add_scatter(x=xs[::paso] / div, y=p[::paso] * 100, mode="lines", name=nombre, line=dict(color=c, width=2.5))
    fig.add_vline(x=umbral / div, line_dash="dash", line_color=TEXTO_FUERTE, line_width=1.2)
    fig.update_xaxes(title_text=f"Utilidad (US$ {suf})")
    fig.update_yaxes(title_text="Probabilidad de superar (%)", range=[0, 100])
    return _base(fig, 360, "Curvas de excedencia: plataforma vs. externo")
