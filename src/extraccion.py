import pandas as pd
import warnings

def extraer_datos(ruta_repro, ruta_quantia):
    """
    Lee los archivos Excel completos en memoria.
    Retorna dos diccionarios donde la llave es el nombre de la hoja
    y el valor es el DataFrame correspondiente.
    """
    # Silenciar las advertencias de openpyxl sobre validación de datos
    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
    print("⏳ Extrayendo datos de GESTION REPRO...")
    # sheet_name=None lee todas las hojas de golpe
    dict_repro = pd.read_excel(ruta_repro, sheet_name=None)
    
    print("⏳ Extrayendo datos de QUANTIA...")
    dict_quantia = pd.read_excel(ruta_quantia, sheet_name=None)
    
    return dict_repro, dict_quantia