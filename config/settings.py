from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Rutas locales de los archivos Excel sincronizados con OneDrive
RUTA_REPRO = Path(r"C:\Users\vorte\scc.com.pe\Karen Flores - BO\GESTION REPRO - ENTEL PERU.xlsx")
RUTA_QUANTIA = Path(r"C:\Users\vorte\scc.com.pe\Karen Flores - BO\QUANTIA - SUBSANACIONES.xlsx")

# Directorio de salida para el CSV procesado que leerá Streamlit
CARPETA_SALIDA = BASE_DIR / "output"
CARPETA_SALIDA.mkdir(exist_ok=True) # Crea la carpeta automáticamente si no existe

RUTA_CONSOLIDADO = CARPETA_SALIDA / "consolidado_bo.csv"