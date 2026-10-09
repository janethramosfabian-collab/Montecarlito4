import pandas as pd
import numpy as np
import plotly.graph_objects as go

def calcular_sensibilidad(df_resultado, columna_objetivo):
    """
    Calcula la correlación de Spearman para el análisis de tornado.
    """
    if df_resultado.empty or columna_objetivo not in df_resultado.columns:
        return pd.DataFrame()
    
    # 1. Seleccionar únicamente columnas numéricas que tengan variabilidad
    df_num = df_resultado.select_dtypes(include=[np.number]).dropna()
    
    if df_num.shape[1] <= 1:
        return pd.DataFrame()
    
    # 2. Filtrar columnas donde el valor sea constante (sin varianza)
    df_num = df_num.loc[:, df_num.std() > 0]
    
    if columna_objetivo not in df_num.columns:
        return pd.DataFrame()
    
    # 3. Calcular la correlación de Spearman
    correlaciones = df_num.corr(method='spearman')[columna_objetivo].drop(columna_objetivo)
    
    df_corr = pd.DataFrame({
        'Variable': correlaciones.index,
        'Correlacion': correlaciones.values
    }).sort_values(by='Correlacion', key=abs, ascending=True)
    
    return df_corr

def generar_grafico_tornado(df_corr):
    """
    Genera el gráfico Tornado con estética estilo @RISK (Azul/Verde positivo, Rojo negativo).
    """
    colors = ['#E74C3C' if val < 0 else '#2ECC71' for val in df_corr['Correlacion']]
    fig = go.Figure(go.Bar(
        x=df_corr['Correlacion'],
        y=df_corr['Variable'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='#2C3E50', width=1)
        ),
        text=[f"{val:+.3f}" for val in df_corr['Correlacion']],
        textposition='auto',
    ))
    fig.update_layout(
        title="<b>Análisis de Sensibilidad (Correlación de Rangos de Spearman)</b>",
        xaxis=dict(title="Coeficiente de Correlación", range=[-1, 1], zeroline=True, zerolinecolor='#2C3E50', gridcolor='#E0E0E0'),
        yaxis=dict(title="Variables de Entrada"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=50, b=50),
        font=dict(color='#2C3E50')
    )
    
    return fig
