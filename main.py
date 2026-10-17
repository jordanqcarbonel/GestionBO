from config.settings import RUTA_REPRO, RUTA_QUANTIA, RUTA_CONSOLIDADO, RUTA_GENESYS, RUTA_REPORTE_BO
from src.extraccion import extraer_datos
from src.transformacion import transformar_datos

def ejecutar_pipeline():
    print("Iniciando orquestador BO...\n")
    
    if RUTA_REPRO.exists() and RUTA_QUANTIA.exists():
        print("✅ Archivos base encontrados con éxito.\n")
        
        # --- FASE 1: EXTRACCIÓN ---
        dict_repro, dict_quantia, df_genesys, df_reporte_bo = extraer_datos(RUTA_REPRO, RUTA_QUANTIA, RUTA_GENESYS, RUTA_REPORTE_BO)
        
        # --- FASE 2: TRANSFORMACIÓN ---
        df_consolidado = transformar_datos(dict_repro, dict_quantia, df_genesys, df_reporte_bo)

        # --- FASE 3: EXPORTACIÓN PARA DASHBOARD ---
        df_consolidado.to_csv(RUTA_CONSOLIDADO, index=False, encoding='utf-8')

        # Imprimir las hojas encontradas para validar
        print(f"✅ Archivo listo para Streamlit guardado en: {RUTA_CONSOLIDADO}")
        print("\n✅ Extracción completada.")
        print(f"-> Hojas en REPRO ({len(dict_repro)}): {list(dict_repro.keys())}")
        print(f"-> Hojas en QUANTIA ({len(dict_quantia)}): {list(dict_quantia.keys())}")
        
    else:
        print("❌ Error: No se encontró uno o ambos archivos.")

if __name__ == "__main__":
    ejecutar_pipeline()