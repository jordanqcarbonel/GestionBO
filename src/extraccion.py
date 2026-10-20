import pandas as pd
import warnings
import glob
import os

def extraer_datos(ruta_repro, ruta_quantia, ruta_genesys, ruta_reporte_bo):
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

    print("⏳ Extrayendo datos de GENESYS...")
    # Leer todos los CSV de la carpeta y unirlos
    archivos_csv = glob.glob(os.path.join(ruta_genesys, "*.csv"))
    if archivos_csv:
        # Se asume que están separados por comas. Si es por punto y coma, añade sep=';' en read_csv
        lista_dfs = [pd.read_csv(archivo) for archivo in archivos_csv]
        df_genesys = pd.concat(lista_dfs, ignore_index=True)
    else:
        df_genesys = pd.DataFrame() # Si la carpeta está vacía

    print("⏳ Extrayendo datos de REPORTE BO...")
    try:
        df_reporte_bo = pd.read_csv(ruta_reporte_bo, low_memory=False)
    except Exception as e:
        print(f"⚠️ Error al leer ReporteBO ({ruta_reporte_bo}): {e}")
        df_reporte_bo = pd.DataFrame()
    
    return dict_repro, dict_quantia, df_genesys, df_reporte_bo