import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import os
os.chdir(ROOT)
from streamlit.testing.v1 import AppTest

def test_app_arranca_simula_y_no_falla():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    assert not at.exception, at.exception
    boton = [b for b in at.sidebar.button if "Simular" in b.label][0]
    boton.click().run()
    assert not at.exception, at.exception
    assert at.session_state["sim"]["resultados"].keys() == {"Escenario 1", "Escenario 2", "Escenario 3"}
    # slider de probabilidad y de umbral responden sin romper
    for sl in at.slider:
        if sl.key == "u_pct":
            sl.set_value(80).run()
    assert not at.exception, at.exception
    assert len(at.metric) > 10

def test_cambiar_distribuciones_y_escenarios():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    at.selectbox(key="p_dist").set_value("Lognormal").run()
    at.selectbox(key="c_dist").set_value("Normal").run()
    assert not at.exception, at.exception
    [b for b in at.button if "Añadir escenario (copia" in b.label][0].click().run()
    assert len(at.session_state["esc"]) == 4
    [b for b in at.sidebar.button if "Simular" in b.label][0].click().run()
    assert not at.exception, at.exception
    assert len(at.session_state["sim"]["resultados"]) == 4

def test_error_de_validacion_bloquea():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    at.selectbox(key="p_dist").set_value("Triangular").run()
    at.number_input(key="p_min").set_value(10.0).run()   # mín > más probable
    assert at.sidebar.button[0].disabled
