import streamlit as st
import plotly.express as px

def local_css(file_name, backgroundcolor=None):
    """
    Lee un archivo CSS externo y lo inyecta en la aplicación de Streamlit.
    """
    with open(file_name) as f:
        if backgroundcolor:
            st.markdown(f'<style>{f.read().replace("[backgroundcolor]", backgroundcolor)}</style>', unsafe_allow_html=True)
        else:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def aplicarFormatoChart(fig, controls=False, legend=False, hoverTemplate=None, backgroundColor=None, textcolor=None):
    """
    Aplica configuraciones estándar de formato y diseño estético a los gráficos de Plotly.
    """
    fig.update_layout(paper_bgcolor=backgroundColor)
    fig.update_layout(plot_bgcolor=backgroundColor)
    fig.update_layout(showlegend=legend)
    fig.update_layout(title_pad_l=20)
    fig.update_layout(
        title_font_family="verdana",
        title_font_color=textcolor,
        title_font_size=20,
        font_size=15,
    )
    
    if hoverTemplate:
        if hoverTemplate == "%":
            fig.update_traces(hovertemplate='<b>%{x}</b> <br> %{y:,.2%}')
        elif hoverTemplate == "$":
            fig.update_traces(hovertemplate='<b>%{x}</b> <br> $ %{y:,.1f}')
        elif hoverTemplate == "#":
            fig.update_traces(hovertemplate='<b>%{x}</b> <br> %{y:,.0f}')
            
    if controls:
        fig.update_xaxes(
            rangeslider_visible=True           
        )
        
    fig.update_layout(
        autosize=True,
        margin=dict(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        )
    )
    return fig
