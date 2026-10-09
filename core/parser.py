import re
import numpy as np

def generarVariables(formula):
    """
    Extrae variables tipo {{variable}} de la fórmula ingresada y traduce
    la sintaxis de tipo Excel a expresiones compatibles con Python y NumPy.
    """
    # Extrae las variables entre llaves {{variable}}
    listaVariables = re.findall(r"({{[A-Za-z0-9_]+}})", formula)
    formulaSimulacion = formula
    listaNombreVariables = []
    
    for var in listaVariables:
        nombrevar = var.replace("{{", "").replace("}}", "")
        if nombrevar not in listaNombreVariables:
            listaNombreVariables.append(nombrevar)
        formulaSimulacion = formulaSimulacion.replace(var, f"variables['{nombrevar}']")
    
    # 1. Traduce la función IF de Excel a np.where de NumPy
    formulaSimulacion = re.sub(r'\bIF\s*\(', 'np.where(', formulaSimulacion, flags=re.IGNORECASE)
    
    # 2. Cambia punto y coma ';' por comas ','
    formulaSimulacion = formulaSimulacion.replace(';', ',')
    
    # 3. Convierte el operador '=' de Excel a '==' de Python
    formulaSimulacion = re.sub(r'(?<![><!=])=(?![=])', '==', formulaSimulacion)
    
    return formulaSimulacion, listaNombreVariables
