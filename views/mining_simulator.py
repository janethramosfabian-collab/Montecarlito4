import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from core.engine import simular_escenario_minero

def render_mining_simulator():
    st.title(':material/landscape: Simulador Minero (LOM)')
    st.write("Análisis Estocástico de Escenarios de Vida de Mina y Riesgo Geológico.")
    
    # Pre-cargar datos base de los 3 escenarios
    def crear_datos_base(tms_zonas):
        return pd.DataFrame({
            "Zona": ["Zona 1", "Zona 2", "Zona 3"],
            "TMS": tms_zonas,
            "Ley (g-Au/t)": [7.0, 5.0, 9.0],
            "Recuperación (%)": [95, 90, 75],
            "Precio ($)": [4500, 4500, 4500],
            "Costo Explotación ($/t)": [80, 60, 40],
            "Certeza Geológica (%)": [50, 75, 90]
        })

    datos_e1 = crear_datos_base([10000, 10000, 10000])
    datos_e2 = crear_datos_base([7000, 10000, 13000])
    datos_e3 = crear_datos_base([15000, 3000, 12000])

    with st.container(border=True):
        st.subheader(":material/settings: Configuración de Escenarios LOM")
        num_sims = st.number_input("Iteraciones de Montecarlo", min_value=100, value=2000, step=100)
        
        t1, t2, t3 = st.tabs(["Escenario 1", "Escenario 2", "Escenario 3"])
        with t1: df_e1 = st.data_editor(datos_e1, use_container_width=True, hide_index=True, key="e1")
        with t2: df_e2 = st.data_editor(datos_e2, use_container_width=True, hide_index=True, key="e2")
        with t3: df_e3 = st.data_editor(datos_e3, use_container_width=True, hide_index=True, key="e3")
            
        btn_simular = st.button("Ejecutar Optimización Estocástica", type="primary")

    if btn_simular:
        with st.spinner("Procesando incertidumbre geológica y simulando LOM..."):
            st.session_state['mining_res'] = {
                "Escenario 1": simular_escenario_minero(df_e1, num_sims),
                "Escenario 2": simular_escenario_minero(df_e2, num_sims),
                "Escenario 3": simular_escenario_minero(df_e3, num_sims)
            }

    # SECCIÓN DE RESULTADOS
    if 'mining_res' in st.session_state:
        st.markdown('<div class="window-risk">', unsafe_allow_html=True)
        st.subheader("Resultados de la Simulación")
        
        res = st.session_state['mining_res']
        
        # Medias para gráfico comparativo
        vna_means = [res["Escenario 1"]["VNA"].mean(), res["Escenario 2"]["VNA"].mean(), res["Escenario 3"]["VNA"].mean()]
        onz_means = [res["Escenario 1"]["Onzas"].mean(), res["Escenario 2"]["Onzas"].mean(), res["Escenario 3"]["Onzas"].mean()]
        
        t_comp, t_a1, t_a2, t_a3 = st.tabs(["📊 Comparativa Global", "🔍 Riesgo E1", "🔍 Riesgo E2", "🔍 Riesgo E3"])
        
        with t_comp:
            st.write("#### VNA vs Onzas Recuperables (Promedio Esperado)")
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(x=["Escenario 1", "Escenario 2", "Escenario 3"], y=vna_means, name="VNA ($)", marker_color='#93C572', yaxis='y'))
            fig_comp.add_trace(go.Scatter(x=["Escenario 1", "Escenario 2", "Escenario 3"], y=onz_means, name="Onzas (koz)", marker=dict(color='#ffcc00', size=10), line=dict(color='#ffcc00', width=3), yaxis='y2'))
            fig_comp.update_layout(
                plot_bgcolor='#111A30', paper_bgcolor='#111A30', font=dict(color='#FFFFFF'),
                yaxis=dict(title="VNA ($)", gridcolor='rgba(255,255,255,0.1)'),
                yaxis2=dict(title="Onzas", overlaying='y', side='right'),
                legend=dict(x=0, y=1.1, orientation="h")
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        # Función para pestañas individuales con histograma y slider
        def crear_pestana_riesgo(nombre, df_res):
            st.write(f"#### Histograma de Riesgo Financiero: {nombre}")
            vals = df_res["VNA"].dropna()
            
            min_val, max_val = float(vals.min()), float(vals.max())
            perc_5, perc_95 = float(np.percentile(vals, 5)), float(np.percentile(vals, 95))
            
            rango = st.slider(f'Delimitadores de Probabilidad (VNA)', min_val, max_val, (perc_5, perc_95), key=f"sld_{nombre}")
            
            df_dentro = df_res[(df_res["VNA"] >= rango[0]) & (df_res["VNA"] <= rango[1])]
            prob = len(df_dentro) / len(df_res)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Probabilidad de Cumplimiento", f"{prob:,.2%}")
            c2.metric("VNA Esperado ($)", f"{vals.mean():,.0f}")
            c3.metric("Riesgo a la Baja (P5)", f"{perc_5:,.0f}")
            
            fig = go.Figure()
            df_fuera = df_res[(df_res["VNA"] < rango[0]) | (df_res["VNA"] > rango[1])]
            fig.add_trace(go.Histogram(x=df_fuera["VNA"], marker_color='#38BDF8', name="Fuera de rango"))
            fig.add_trace(go.Histogram(x=df_dentro["VNA"], marker_color='#0066FF', name="Dentro de rango"))
            fig.add_vline(x=rango[0], line_dash="dash", line_color="#EF4444")
            fig.add_vline(x=rango[1], line_dash="dash", line_color="#EF4444")
            fig.update_layout(barmode='overlay', plot_bgcolor='#111A30', paper_bgcolor='#111A30', font=dict(color='#FFFFFF'), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with t_a1: crear_pestana_riesgo("Escenario 1", res["Escenario 1"])
        with t_a2: crear_pestana_riesgo("Escenario 2", res["Escenario 2"])
        with t_a3: crear_pestana_riesgo("Escenario 3", res["Escenario 3"])
            
        st.markdown('</div>', unsafe_allow_html=True)
