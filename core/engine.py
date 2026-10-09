import numpy as np
import pandas as pd

def ejecutar_simulacion(df_variables, formula_compilada, num_simulaciones, usar_escenarios=False, df_escenarios=None):
    """
    Motor independiente de cálculo de Montecarlo. 
    Recibe la configuración de variables y devuelve el DataFrame con las simulaciones.
    """
    variables = {}
    
    for _, fila in df_variables.iterrows():
        var_nombre = fila["Variable"]
        
        # Validación de escenarios conjuntos (correlacionados)
        if usar_escenarios and df_escenarios is not None and not df_escenarios.empty and var_nombre in df_escenarios.columns:
            if "Probabilidad" in df_escenarios.columns:
                probs = pd.to_numeric(df_escenarios["Probabilidad"], errors='coerce').fillna(0).values
                if probs.sum() > 0:
                    probs = probs / probs.sum()
                    escenarios_idx = np.random.choice(df_escenarios.index, size=num_simulaciones, p=probs)
                    valores = pd.to_numeric(df_escenarios.loc[escenarios_idx, var_nombre], errors='coerce').values
                else:
                    valores = np.zeros(num_simulaciones)
            else:
                valores = np.zeros(num_simulaciones)
        else:
            dist = fila["Distribucion"]
            p1 = fila["Param 1"]
            p2 = fila["Param 2"]
            p3 = fila["Param 3"]
            
            # Generación según el tipo de distribución de probabilidad
            if dist == "Normal":
                valores = np.random.normal(p1, p2, num_simulaciones)
            elif dist == "Uniforme":
                if fila["Tipo Datos"] == "Entero":
                    valores = np.random.randint(int(p1), int(p2) + 1, size=num_simulaciones)
                else:
                    valores = np.random.uniform(p1, p2, num_simulaciones)
            elif dist == "Binomial":
                valores = np.random.binomial(int(p1), p2, num_simulaciones)
            elif dist == "Triangular":
                valores = np.random.triangular(p1, p2, p3, num_simulaciones)
            elif dist == "Exponencial":
                valores = np.random.exponential(scale=p1, size=num_simulaciones)
            elif dist == "Poisson":
                valores = np.random.poisson(lam=p1, size=num_simulaciones)
            elif dist == "Log-Normal":
                valores = np.random.lognormal(mean=p1, sigma=p2, size=num_simulaciones)
            else:
                valores = np.zeros(num_simulaciones)
        
        # Ajuste de tipo de datos final para la variable
        if fila["Tipo Datos"] == "Entero":
            variables[var_nombre] = np.round(valores).astype(int)
        else:
            variables[var_nombre] = valores.astype(float)
            
    # Evaluación de la fórmula final de simulación
    variables[list(variables.keys())[0]] # Referencia para mantener contexto si se requiere
    evaluado = eval(formula_compilada, {"np": np, "variables": variables})
    variables['resultado_evaluado'] = evaluado
    
    return pd.DataFrame(variables)
    
    # Añadir al final de core/engine.py

def simular_escenario_minero(df_zonas, num_simulaciones=1000):
    """
    Simula el VNA (Utilidad) y Onzas de un escenario minero basado en zonas.
    La Certeza Geológica define la volatilidad (desviación estándar) de Ley y Recuperación.
    """
    total_onzas_sim = np.zeros(num_simulaciones)
    total_utilidad_sim = np.zeros(num_simulaciones)
    
    for _, zona in df_zonas.iterrows():
        tms = float(zona['TMS'])
        ley_media = float(zona['Ley (g-Au/t)'])
        # Convertir porcentajes a decimales
        rec_media = float(zona['Recuperación (%)']) / 100.0
        precio = float(zona['Precio ($)'])
        costo_tms = float(zona['Costo Explotación ($/t)'])
        certeza = float(zona['Certeza Geológica (%)']) / 100.0
        
        # A menor certeza, mayor desviación estándar (mayor riesgo de variación)
        std_ley = ley_media * (1.0 - certeza)
        std_rec = rec_media * (1.0 - certeza)
        
        # Generar simulaciones (Distribución Normal)
        ley_sim = np.random.normal(ley_media, std_ley, num_simulaciones)
        rec_sim = np.random.normal(rec_media, std_rec, num_simulaciones)
        
        # Limitar para evitar leyes negativas o recuperaciones irreales (>100%)
        ley_sim = np.clip(ley_sim, 0.001, None)
        rec_sim = np.clip(rec_sim, 0.001, 1.0)
        
        # Fórmulas del modelo financiero minero
        onzas_sim = (tms * ley_sim * rec_sim) / 31.1035
        valorizado_sim = onzas_sim * precio
        costo_sim = tms * costo_tms
        utilidad_sim = valorizado_sim - costo_sim
        
        total_onzas_sim += onzas_sim
        total_utilidad_sim += utilidad_sim
        
    return pd.DataFrame({
        'Onzas': total_onzas_sim,
        'VNA': total_utilidad_sim
    })
