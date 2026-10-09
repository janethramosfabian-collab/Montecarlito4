import streamlit as st
from utils.formatters import local_css
from views.home import render_home
from views.simulator_view import render_simulator

# 1. Configuración global de la página de Streamlit
st.set_page_config(
    page_title="Plataforma de Simulación y Datos", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Carga de estilos globales personalizados
local_css("assets/estilos.css")

def main():
    """
    Función principal que actúa como router de la plataforma web.
    """
    # Barra lateral de navegación
    st.sidebar.title("🧭 Navegación")
    
    # Inicializar estado de navegación si no existe
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "Simulador de Montecarlo"
        
    opciones_navegacion = ["Simulador de Montecarlo", "Gestión de Datos"]
    
    # Selector en barra lateral vinculado al estado de la sesión
    current_index = opciones_navegacion.index(st.session_state.current_view) if st.session_state.current_view in opciones_navegacion else 0
    
    selected_view = st.sidebar.radio("Seleccione el Módulo", opciones_navegacion, index=current_index)
    st.session_state.current_view = selected_view
    
    st.sidebar.divider()
    st.sidebar.markdown("### 💡 Acerca de")
    st.sidebar.info("Plataforma profesional de análisis de riesgos, modelado matemático y simulación estocástica.", icon=":material/info:")

    # Enrutamiento de vistas
    if selected_view == "Simulador de Montecarlo":
        render_simulator()
    elif selected_view == "Gestión de Datos":
        render_home()

if __name__ == "__main__":
    main()
