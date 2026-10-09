import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from code_editor import code_editor

from core.parser import generarVariables
from core.engine import ejecutar_simulacion
from core.sensitivity import calcular_sensibilidad, generar_grafico_tornado

def render_simulator():
    """
    Renderiza la interfaz completa del Simulador de Montecarlo adaptada al diseño financiero institucional.
    """
    # Título principal de la aplicación (Título en blanco puro por CSS)
    st.title(':material/analytics: Simulador de Montecarlo')
    
    # Contenedor para los parámetros de la simulación
    with st.container(border=True, key="panel-parametros"):
        st.subheader(':material/function: Parámetros de la simulación')
        
        c1, c2 = st.columns([2, 8], vertical_alignment="center")
        
        with c1:
            parVariableResultado = st.text_input('Variable resultado', 'Resultado')
            
        with c2:
            st.write('##### Fórmula de la simulación')
            
            # Llamada segura y limpia a code_editor compatible con todas sus versiones
            parformula = code_editor(
                '', 
                lang='python', 
                response_mode='blur'
            )
            
        st.info('Ingrese la fórmula de la simulación. Utilice las variables entre llaves dobles. Por ejemplo, si la fórmula es `X1+X2`, debe ingresar `{{X1}}+{{X2}}`', icon=":material/info:")
        
        parNumSimulaciones = st.number_input('Número de simulaciones', min_value=1, value=1000)
        
        dfVariables = pd.DataFrame()
        formulaSimulacion = ""
        listaNombreVariables = []
        minValorParametros = 1.0
        usar_escenarios = False
        dfEscenarios = pd.DataFrame()
        
        if parformula and parformula.get("text"):
            formulaSimulacion, listaNombreVariables = generarVariables(parformula["text"])
            
            if len(listaNombreVariables) == 0:
                st.error("No se encontraron variables en la fórmula. Todas las variables deben tener el formato {{variable}}", icon=":material/warning:")
                st.stop()
                
            dfBase = pd.DataFrame({
                'Variable': listaNombreVariables, 
                "Distribucion": "Normal", 
                "Tipo Datos": "Decimales", 
                "Param 1": 0.0000, 
                "Param 2": 0.000, 
                "Param 3": 0.000
            })
            
            columns = st.columns(2)
            with columns[0]:
                dfVariables = st.data_editor(
                    dfBase,
                    column_config={
                        "Variable": st.column_config.TextColumn("Variable", disabled=True),
                        "Distribucion": st.column_config.SelectboxColumn(
                            "Distribución",
                            help="Distribución de probabilidad de la simulación",
                            width="medium",
                            options=["Normal", "Uniforme", "Binomial", "Triangular", "Exponencial", "Poisson", "Log-Normal"],
                            required=True,
                        ),
                        "Tipo Datos": st.column_config.SelectboxColumn(
                            "Tipo de Datos",
                            help="Tipo de datos de la variable",
                            width="medium",
                            options=["Entero", "Decimales"],
                            required=True,
                        )
                    },
                    hide_index=True, use_container_width=True
                )
                
                with st.expander("🔗 Configuración Avanzada: Variables Correlacionadas / Escenarios Conjuntos", expanded=False):
                    st.write("Si tus variables dependen de un escenario conjunto (discreto), habilítalo y define tus propias columnas y valores.")
                    usar_escenarios = st.checkbox("Habilitar Escenarios Conjuntos para variables dependientes")
                    
                    if usar_escenarios:
                        datos_vacia = {
                            "Escenario": ["Escenario 1", "Escenario 2"],
                            "Probabilidad": [0.5, 0.5],
                        }
                        st.info("Agrega las columnas con el nombre exacto de tus variables (ej. el nombre que uses en la fórmula con {{ }}).", icon=":material/info:")
                        dfEscenarios = st.data_editor(pd.DataFrame(datos_vacia), num_rows="dynamic", use_container_width=True)
                
                btnSimular = st.button('Simular', type="primary", key="btn_simular_principal")
                
                if not dfVariables.empty:
                    minValorParametros = dfVariables.apply(lambda x: x["Param 1"] + x["Param 2"] + x["Param 3"], axis=1).min()
                    if minValorParametros == 0:
                        st.error("Algunas de las variables tienen los parámetros principales en cero", icon=":material/warning:")
                    
            with columns[1]:
                textoDistribuciones = """### Distribuciones
**Normal:** Distribución en forma de campana, valores cerca de la media.
* **Param 1:** Media
* **Param 2:** Desviación estándar
---
**Distribución Uniforme:** Resultados en un rango con igual probabilidad.
* **Param 1:** Mínimo
* **Param 2:** Máximo
---
**Distribución Binomial:** Éxitos en ensayos con dos resultados posibles.
* **Param 1:** Ensayos
* **Param 2:** Probabilidad
---
**Distribución Triangular:** Valores más probables en un rango.
* **Param 1:** Mínimo
* **Param 2:** Moda
* **Param 3:** Máximo
---
**Exponencial:** Tiempo entre eventos.
* **Param 1:** Escala
---
**Poisson:** Conteo de eventos en un intervalo.
* **Param 1:** Tasa ($\lambda$)
---
**Log-Normal:** Variables cuyo logaritmo es normal.
* **Param 1:** Media log
* **Param 2:** Desv log
                """
                with st.container(height=420):
                    st.markdown(textoDistribuciones)
                    
            if 'resultado' not in st.session_state:
                st.session_state.resultado = pd.DataFrame()
                
            # LÓGICA DE EJECUCIÓN DE LA SIMULACIÓN
            if 'btnSimular' in locals() and (btnSimular or len(st.session_state.resultado) > 0):
                if minValorParametros == 0 and btnSimular:
                    st.stop()
                    
                if len(st.session_state.resultado) == 0 or btnSimular:
                    dfResultado = ejecutar_simulacion(
                        df_variables=dfVariables,
                        formula_compilada=formulaSimulacion,
                        num_simulaciones=parNumSimulaciones,
                        usar_escenarios=usar_escenarios,
                        df_escenarios=dfEscenarios
                    )
                    # Renombrar la columna interna al nombre de variable resultado especificado
                    if 'resultado_evaluado' in dfResultado.columns:
                        dfResultado[parVariableResultado] = dfResultado['resultado_evaluado']
                        dfResultado = dfResultado.drop(columns=['resultado_evaluado'])
                        
                    st.session_state.resultado = dfResultado
                else:
                    dfResultado = st.session_state.resultado
                    
                # --- SECCIÓN DE RESULTADOS ---
                if not dfResultado.empty:
                    st.subheader('Resultados de la Simulación')
                    st.markdown('<div class="window-risk">', unsafe_allow_html=True)
                    tabAnalisis, tabSensibilidad, tabDatos = st.tabs(["📊 Histograma y Frecuencia", "🌪️ Sensibilidad (Tornado)", "📋 Datos de Simulaciones"])
                    
                    with tabAnalisis:
                        if parVariableResultado in dfResultado.columns:
                            vals = dfResultado[parVariableResultado].dropna()
                            col_grafico, col_stats = st.columns([7, 3])
                            
                            with col_grafico:
                                rangoPercentiles = [2.5, 5, 25, 50, 75, 95, 97.5]
                                percentiles = np.percentile(vals, rangoPercentiles)
                                
                                min_val = float(vals.min())
                                max_val = float(vals.max())
                                if min_val == max_val:
                                    max_val += 0.01
                                
                                parMontoProbabilidad = st.slider(
                                    'Rango de Delimitadores (Cutoffs)', 
                                    min_val, max_val,
                                    (float(percentiles[0]), float(percentiles[-1]))
                                )
                                
                                dfRango = dfResultado[(dfResultado[parVariableResultado] >= parMontoProbabilidad[0]) & 
                                                      (dfResultado[parVariableResultado] <= parMontoProbabilidad[1])]
                                probabilidadMonto = len(dfRango) / len(dfResultado) if len(dfResultado) > 0 else 0
                                
                                m_cols = st.columns(3)
                                m_cols[0].metric(label="Probabilidad (Likelihood)", value=f"{probabilidadMonto:,.2%}")
                                m_cols[1].metric(label="Corte Inferior", value=f"{parMontoProbabilidad[0]:,.2f}")
                                m_cols[2].metric(label="Corte Superior", value=f"{parMontoProbabilidad[1]:,.2f}")
                                
                                fig_hist = go.Figure()
                                df_fuera = dfResultado[(dfResultado[parVariableResultado] < parMontoProbabilidad[0]) | 
                                                      (dfResultado[parVariableResultado] > parMontoProbabilidad[1])]
                                
                                fig_hist.add_trace(go.Histogram(x=df_fuera[parVariableResultado], marker=dict(color='#38BDF8'), showlegend=False))
                                fig_hist.add_trace(go.Histogram(x=dfRango[parVariableResultado], marker=dict(color='#0066FF'), showlegend=False))
                                fig_hist.add_vline(x=parMontoProbabilidad[0], line_dash="dash", line_color="#EF4444", line_width=2)
                                fig_hist.add_vline(x=parMontoProbabilidad[1], line_dash="dash", line_color="#EF4444", line_width=2)
                                fig_hist.update_layout(
                                    title=dict(text=f"<b>Simulation Results: {parVariableResultado}</b>", font=dict(color='#FFFFFF', size=16)),
                                    barmode='overlay',
                                    plot_bgcolor='#111A30',
                                    paper_bgcolor='#111A30',
                                    margin=dict(l=10, r=10, t=40, b=10),
                                    xaxis=dict(title=f"Valores de {parVariableResultado}", gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='#FFFFFF')),
                                    yaxis=dict(title="Frecuencia", gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='#FFFFFF')),
                                    font=dict(color='#FFFFFF')
                                )
                                
                                st.plotly_chart(fig_hist, use_container_width=True)
                                
                            with col_stats:
                                st.markdown("#### Estadísticas")
                                st.metric(label="Simulaciones", value=f"{len(dfResultado):,}")
                                st.metric(label="Media", value=f"{vals.mean():,.2f}")
                                st.metric(label="Desv. Estándar", value=f"{vals.std():,.2f}")
                                
                                dfPercentiles = pd.DataFrame({"Percentil": [f"{i}%" for i in rangoPercentiles], "Valor": percentiles})
                                st.dataframe(dfPercentiles, use_container_width=True, hide_index=True)
                                
                    with tabSensibilidad:
                        st.markdown("#### Análisis de Sensibilidad (Tornado)")
                        df_corr = calcular_sensibilidad(dfResultado, parVariableResultado)
                        if not df_corr.empty:
                            fig_tornado = generar_grafico_tornado(df_corr)
                            fig_tornado.update_layout(
                                plot_bgcolor='#111A30',
                                paper_bgcolor='#111A30',
                                font=dict(color='#FFFFFF')
                            )
                            st.plotly_chart(fig_tornado, use_container_width=True)
                            
                    with tabDatos:
                        st.dataframe(dfResultado, use_container_width=True)
                        
                    st.markdown('</div>', unsafe_allow_html=True)
