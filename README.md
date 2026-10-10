# Montecarlo para planeamiento minero (Streamlit)

## Ejecutar
```
pip install -r requirements.txt
streamlit run app.py
```
Pruebas: `pip install pytest && python -m pytest tests`

## Estructura
- `app.py` – arranque, pestañas y botón ▶ Simular
- `core/modelo.py` – fórmulas del Excel (por zona y totales ponderados) y simulación Montecarlo
- `core/estadistica.py` – percentiles, probabilidad de cumplir, prob. de ser el mejor, tornado, comparación con @RISK
- `core/exportar.py` – Excel con supuestos, determinístico, resumen y simulaciones
- `core/ejemplo.py` – los 3 escenarios de tu Excel
- `ui/` – pantallas (datos, resultados, exportar) y gráficos
- `tests/` – valida contra las utilidades de tu Excel y el comportamiento de la app

## Modelo
Por zona: `Onzas = TMS·Ley·Rec/31.1035`, `Valorizado = Precio·Onzas`, `Costo = Costo/t·TMS`, `Utilidad = Valorizado − Costo`.
En cada iteración varían el **precio** (factor común a todo el mercado) y la **certeza geológica** de cada zona.
Ver la pestaña «2 · Incertidumbre» para el detalle y las opciones.
