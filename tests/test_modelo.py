import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
from core import Supuestos, simular, totales_deterministas, tabla_determinista
from core.ejemplo import escenarios_ejemplo
from core.estadistica import prob_mejor, sensibilidad

E = escenarios_ejemplo()

def test_determinista_coincide_con_excel():
    esperado = {"Escenario 1": 24097407.04, "Escenario 2": 24260810.52, "Escenario 3": 26243750.38}
    for k, v in esperado.items():
        assert totales_deterministas(E[k])["Utilidad (US$)"] == pytest.approx(v, abs=0.01)

def test_totales_ponderados_por_tms_propio():
    # En el Excel F18/F32 usaban las TMS del escenario 1 (error); aquí se pondera con las propias.
    assert totales_deterministas(E["Escenario 2"])["Ley (g/t)"] == pytest.approx(7.2)
    assert totales_deterministas(E["Escenario 3"])["Ley (g/t)"] == pytest.approx(7.6)
    assert totales_deterministas(E["Escenario 1"])["Certeza geológica (%)"] == pytest.approx(71.667, abs=1e-3)
    assert totales_deterministas(E["Escenario 3"])["Certeza geológica (%)"] == pytest.approx(68.5)

def test_onzas_por_zona():
    t = tabla_determinista(E["Escenario 1"])
    assert t["Onzas (oz)"].round(0).tolist() == [2138, 1447, 2170]

def test_media_simulada_no_sesgada():
    s = Supuestos(n_iter=40000, semilla=7)
    r = simular(E, s)
    for k, df in r.items():
        det = totales_deterministas(E[k])["Utilidad (US$)"]
        se = df["Utilidad (US$)"].std() / np.sqrt(len(df))
        assert abs(df["Utilidad (US$)"].mean() - det) < 4 * se, k

def test_reproducible_con_semilla():
    a = simular(E, Supuestos(n_iter=500, semilla=3))["Escenario 1"]["Utilidad (US$)"]
    b = simular(E, Supuestos(n_iter=500, semilla=3))["Escenario 1"]["Utilidad (US$)"]
    c = simular(E, Supuestos(n_iter=500, semilla=4))["Escenario 1"]["Utilidad (US$)"]
    assert (a == b).all() and not (a == c).all()

def test_sin_incertidumbre_da_el_determinista():
    s = Supuestos(n_iter=200, precio_min_pct=0, precio_max_pct=0, precio_moda_pct=0, certeza_delta_pp=0, k_dispersion=0)
    r = simular(E, s)
    for k, df in r.items():
        assert df["Utilidad (US$)"].std() < 1e-6
        assert df["Utilidad (US$)"].iloc[0] == pytest.approx(totales_deterministas(E[k])["Utilidad (US$)"])

def test_geologia_compartida_entre_escenarios():
    r = simular(E, Supuestos(n_iter=300, compartir_geologia=True))
    a, b = r["Escenario 1"]["Factor ley Zona 1"], r["Escenario 2"]["Factor ley Zona 1"]
    assert np.allclose(a, b)
    r2 = simular(E, Supuestos(n_iter=300, compartir_geologia=False))
    assert not np.allclose(r2["Escenario 1"]["Factor ley Zona 1"], r2["Escenario 2"]["Factor ley Zona 1"])

def test_mas_certeza_menos_dispersion_de_ley():
    r = simular(E, Supuestos(n_iter=20000))["Escenario 1"]
    assert r["Factor ley Zona 1"].std() > r["Factor ley Zona 3"].std() * 2   # 50 % vs 90 %

def test_distribuciones_y_rho():
    for d in ["Triangular", "Uniforme", "Normal", "Lognormal"]:
        r = simular(E, Supuestos(n_iter=2000, precio_dist=d))["Escenario 1"]
        assert r["Factor precio"].mean() == pytest.approx(1.0, abs=0.02), d
    for d in ["Triangular", "Uniforme", "Normal"]:
        r = simular(E, Supuestos(n_iter=2000, certeza_dist=d))["Escenario 1"]
        assert r["Certeza Zona 2"].between(0, 100).all()
    r = simular(E, Supuestos(n_iter=20000, rho_zonas=0.8, certeza_delta_pp=0))["Escenario 1"]
    assert np.corrcoef(r["Factor ley Zona 1"], r["Factor ley Zona 3"])[0, 1] > 0.6

def test_prob_mejor_suma_uno_y_tornado():
    r = simular(E, Supuestos(n_iter=3000))
    assert sum(prob_mejor(r).values()) == pytest.approx(1.0)
    t = sensibilidad(r["Escenario 1"])
    assert "Factor precio" in set(t["Variable"])


def test_efecto_certeza_proporcional():
    s = Supuestos(n_iter=40000, semilla=11, efecto_certeza="proporcional")
    r = simular(E, s)
    for k, df in r.items():
        det = totales_deterministas(E[k])["Utilidad (US$)"]
        se = df["Utilidad (US$)"].std() / np.sqrt(len(df))
        assert abs(df["Utilidad (US$)"].mean() - det) < 4 * se, k
    t = sensibilidad(r["Escenario 1"])
    corr = dict(zip(t["Variable"], t["Correlación"]))
    assert corr["Certeza Zona 1"] > 0.2          # ahora la certeza SÍ mueve el resultado
    assert corr["Certeza Zona 1"] > corr["Certeza Zona 3"]


def test_tornado_sin_duplicados_en_modo_proporcional():
    r = simular(E, Supuestos(n_iter=2000, efecto_certeza="proporcional"))
    t = sensibilidad(r["Escenario 1"])
    assert not any(v.startswith("Factor ley") for v in t["Variable"])


def test_exportar_excel_y_comparar_externo(tmp_path):
    import io, openpyxl
    from core.exportar import excel_bytes
    from core.estadistica import resumen, comparar_con_externo
    s = Supuestos(n_iter=1000)
    r = simular(E, s)
    det = {k: totales_deterministas(v)["Utilidad (US$)"] for k, v in E.items()}
    res = resumen(r, det, "pct", 90)
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes(E, s, res, r)))
    assert {"Supuestos", "Determinístico", "Resumen estocástico", "Sim Escenario 1"} <= set(wb.sheetnames)
    ws = wb["Determinístico"]
    valores = [c.value for c in ws["K"]]            # columna Utilidad (US$)
    assert any(isinstance(v, float) and abs(v - 24097407.04) < 0.01 for v in valores)
    propio = r["Escenario 1"]["Utilidad (US$)"].to_numpy()
    otro = simular(E, Supuestos(n_iter=20000, semilla=99))["Escenario 1"]["Utilidad (US$)"].to_numpy()
    cmp = comparar_con_externo(propio, otro, 22e6)
    z = cmp.loc[cmp["Estadístico"] == "Media", "Diferencia en errores estándar"].iloc[0]
    assert abs(z) < 4
