import streamlit as st
from utils.formatters import local_css
from views.home import render_home
from views.simulator_view import render_simulator
from views.mining_simulator import render_mining_simulator # <-- NUEVO

# 1. Configuración global
st.set_page_config(page_title="Plataforma de Simulación", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
local_css("assets/estilos.css")

def main():
    st.sidebar.title("🧭 Navegación")
    
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "Simulador de Montecarlo"
        
    # Añadir el nuevo simulador a las opciones
    opciones_navegacion = ["Simulador de Montecarlo", "Simulador Minero LOM", "Gestión de Datos"]
    
    current_index = opciones_navegacion.index(st.session_state.current_view) if st.session_state.current_view in opciones_navegacion else 0
    selected_view = st.sidebar.radio("Seleccione el Módulo", opciones_navegacion, index=current_index)
    st.session_state.current_view = selected_view
    
    st.sidebar.divider()
    st.sidebar.markdown("### 💡 Acerca de")
    st.sidebar.info("Plataforma profesional de análisis de riesgos, modelado matemático y simulación estocástica.", icon=":material/info:")
    
    # Enrutamiento de vistas actualizado
    if selected_view == "Simulador de Montecarlo":
        render_simulator()
    elif selected_view == "Simulador Minero LOM":
        render_mining_simulator() # <-- NUEVO
    elif selected_view == "Gestión de Datos":
        render_home()

if __name__ == "__main__":
    main()
