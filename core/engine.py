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
