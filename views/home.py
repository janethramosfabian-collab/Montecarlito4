import streamlit as st

def render_home():
    """
    Renderiza la vista principal / dashboard de la plataforma de datos y simulaciones.
    """
    st.title(":material/dashboard: Panel General de la Plataforma")
    st.write("Bienvenida a tu plataforma profesional de gestión de datos y análisis de riesgos mediante Simulación de Montecarlo.")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader(":material/analytics: Simulador de Montecarlo")
            st.write("Configura variables, distribuciones probabilísticas, fórmulas avanzadas y análisis de sensibilidad (Tornado).")
            if st.button("Ir al Simulador", type="primary"):
                st.session_state.current_view = "Simulador de Montecarlo"
                st.rerun()
                
    with col2:
        with st.container(border=True):
            st.subheader(":material/database: Gestión de Datos")
            st.write("Carga, depura y estructura datasets tabulares para alimentar tus modelos de negocio.")
            st.info("Módulo en expansión para la gestión avanzada de datos.", icon=":material/info:")
