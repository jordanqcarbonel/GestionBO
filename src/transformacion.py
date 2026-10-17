import pandas as pd

# Matriz de TMO
TMO_MATRIX = {
    'CONTACTO VALIDO': 8,
    'CONTACTO NO VALIDO': 4,
    'ENTREGADO': 1,
    'REINGRESO': 2,
    'NO CORRESPONDE': 2,
    'CAIDAS EXPRESS': 10,
    'CAIDAS PROGRAMADO': 10,
    'CAIDAS PICKUP': 10,
    'DERIVACIÓN PICK UP': 10,
    'PLAZO OFRECIDO': 10,
    'ALERTAS': 10,
    'BASE QUANTIA': 3,
    'SUBSANACIONES': 1,
    'REASIGNACIONES': 2,
    'TRIAGE': 10,
    'EXPORTADO STOCK- OL': 10,
    'REINGRESO - VENTA MES ANTERIOR': 10,
    'SIMULACIÓN INGRESO': 10,
    'REPRO': 3,
    'ALERTA ACTIVACIÓN - REA': 3,
    'STATUS DE ORDEN': 5,
    'CONSULTA A TIENDA': 5,
    'HUELLA': 5,
    'CANCELACION': 5
}

# Matriz de nombres BO
MAPEO_GENESYS = {
    'Covenas Durand Janet[Scc]': 'MARYURI JANET COVEÑAS DURAND',
    'Camus Mendoza Ivan[Scc]': 'IVAN CAMUS MENDOZA',
    'Aranda Tamayo Shenla Franshesca[Scc]': 'SHENLA FRANCHESCA ARANDA TAMAYO',
    'Mendez Quispilaya Evelyn Celeste[Scc]': 'EVELYN CELESTE MENDEZ QUISPILAYA',
    'Yessenia Yasmin Yasmin. Quito Arteta': 'YESSENIA QUITO ARTETA',
    'Marcos Alberto Mori Alvarado': 'MARCOS ALBERTO EMANUEL MORI ALVARADO',
    'Hinojosa Leon Cinthya Paola[Sccp]': 'CINTHYA PAOLA HINOJOSA LEON',
    'Tineo Obregon Sofia Angelica[Scc]': 'SOFIA ANGELICA TINEO OBREGON',
    'Brayan Antony Rivera Condor': 'BRAYAN ANTONY RIVERA CONDOR'
}

def estandarizar_y_unir(df, mapeo_columnas, nombre_hoja, categoria_origen):
    """
    Toma un DataFrame, extrae bloques de columnas específicos, los renombra al estándar
    y los apila verticalmente ignorando los nulos.
    """
    bloques = []
    
    for bloque in mapeo_columnas:
        # Extraer solo las columnas que existen en el DataFrame
        cols_existentes = {k: v for k, v in bloque.items() if k in df.columns}
        
        if not cols_existentes:
            continue
            
        df_bloque = df[list(cols_existentes.keys())].copy()
        df_bloque.rename(columns=cols_existentes, inplace=True)
        
        # Añadir metadatos de origen
        df_bloque['Hoja_Origen'] = nombre_hoja
        df_bloque['Categoria_Calculo'] = categoria_origen
        
        # Si no hay 'Tipo_Gestión' en este bloque (ej. Quantia), lo rellenamos con la categoría
        if 'Tipo_Gestión' not in df_bloque.columns:
            df_bloque['Tipo_Gestión'] = categoria_origen
            
        bloques.append(df_bloque)
        
    if bloques:
        df_unido = pd.concat(bloques, ignore_index=True)
        # 🔒 FILTRADO ESTRICTO DE NULOS:
        # Una gestión es válida solo si tiene Reprogramador, Fecha de Gestión Y Tipo de Gestión.
        # Si cualquiera de estos tres campos es nulo/vacío, se descarta.
        columnas_a_validar = [c for c in ['Fecha_Gestión', 'Reprogramador', 'Tipo_Gestión'] if c in df_unido.columns]
        df_unido = df_unido.dropna(subset=columnas_a_validar)
        return df_unido
    else:
        return pd.DataFrame()

def transformar_datos(dict_repro, dict_quantia, df_genesys):
    print("⚙️ Iniciando transformación y cálculo de TMO...")

    # --- 0. PREPARAR BASE CLOUD ---
    if not df_genesys.empty and 'DNIS' in df_genesys.columns and 'Usuarios' in df_genesys.columns:
        # Extraer los últimos 9 dígitos
        df_genesys['Telefono_Cloud'] = df_genesys['DNIS'].astype(str).str.strip().str[-9:]
        # Estandarizar nombre del BO
        df_genesys['Reprogramador_Cloud'] = df_genesys['Usuarios'].map(MAPEO_GENESYS)
        # Eliminar duplicados porque solo nos interesa saber si el BO llamó al número al menos 1 vez
        df_genesys_unicos = df_genesys[['Telefono_Cloud', 'Reprogramador_Cloud']].dropna().drop_duplicates()
        df_genesys_unicos['Llamada_Cloud'] = 'Sí'
    else:
        df_genesys_unicos = pd.DataFrame(columns=['Telefono_Cloud', 'Reprogramador_Cloud', 'Llamada_Cloud'])

    datos_procesados = []

    # 1. PROCESAR HOJAS: APP, DIG, REPRO TLV
    hojas_grupo_1 = ['APP', 'DIG', 'REPRO TLV']
    for hoja in hojas_grupo_1:
        if hoja in dict_repro:
            df = dict_repro[hoja]
            
            # Bloque de Gestiones Regulares (1, 2 y 3)
            mapeo_gestiones = [
                {'FECHA DE GESTIÓN 1': 'Fecha_Gestión', 'REPROGRAMADOR ASIGNADO 1': 'Reprogramador', 'TIPO CONTACTO 1': 'Tipo_Gestión', 'N° LLAMADA': 'Telefono'},
                {'FECHA DE GESTIÓN 2': 'Fecha_Gestión', 'REPROGRAMADOR ASIGNADO 2': 'Reprogramador', 'TIPO CONTACTO 2': 'Tipo_Gestión', 'N° LLAMADA': 'Telefono'},
                {'FECHA DE GESTIÓN 3': 'Fecha_Gestión', 'REPROGRAMADOR ASIGNADO 3': 'Reprogramador', 'TIPO CONTACTO 3': 'Tipo_Gestión', 'N° LLAMADA': 'Telefono'}
            ]
            df_gestiones = estandarizar_y_unir(df, mapeo_gestiones, hoja, 'GESTIÓN REPRO')
            
            # Bloque de Análisis 1
            mapeo_analisis_1 = [
                {'FECHA ANÁLISIS 1': 'Fecha_Gestión', 'REPRO ANÁLISIS 1': 'Reprogramador', 'TIPO DE ANALISIS 1': 'Tipo_Gestión'}
            ]
            df_analisis_1 = estandarizar_y_unir(df, mapeo_analisis_1, hoja, 'GESTIÓN ANÁLISIS')
            
            # Bloque de Análisis Caídas
            mapeo_caidas = [
                {'FECHA ANALISIS CAIDAS': 'Fecha_Gestión', 'REPRO ANÁLISIS CAIDAS': 'Reprogramador', 'ANALISIS VENTAS CAIDAS': 'Tipo_Gestión'}
            ]
            df_caidas = estandarizar_y_unir(df, mapeo_caidas, hoja, 'GESTIÓN ANÁLISIS')
            
            datos_procesados.extend([df_gestiones, df_analisis_1, df_caidas])

    # 2. PROCESAR HOJA: CAIDAS
    if 'CAIDAS' in dict_repro:
        df = dict_repro['CAIDAS']
        # Como solo hay un reprogramador, lo asignamos a los 3 mapeos
        mapeo_caidas_unica = [
            {'FECHA GESTIÓN 1': 'Fecha_Gestión', 'REPROGRAMADOR': 'Reprogramador', 'TIPO CONTACTO 1': 'Tipo_Gestión', 'NÚMERO DE LLAMADA': 'Telefono'},
            {'FECHA GESTIÓN 2': 'Fecha_Gestión', 'REPROGRAMADOR': 'Reprogramador', 'TIPO CONTACTO 2': 'Tipo_Gestión', 'NÚMERO DE LLAMADA': 'Telefono'},
            {'FECHA GESTIÓN 3': 'Fecha_Gestión', 'REPROGRAMADOR': 'Reprogramador', 'TIPO CONTACTO 3': 'Tipo_Gestión', 'NÚMERO DE LLAMADA': 'Telefono'}
        ]
        df_caidas_unica = estandarizar_y_unir(df, mapeo_caidas_unica, 'CAIDAS', 'GESTIÓN REPRO')
        datos_procesados.append(df_caidas_unica)

    # 2.1 PROCESAR HOJA: ALERTAS
    if 'ALERTAS' in dict_repro:
        df_alertas = estandarizar_y_unir(
            dict_repro['ALERTAS'],
            [{'FECHA DE GESTIÓN': 'Fecha_Gestión', 'NOMBRE BO': 'Reprogramador', 'TIPO DE ALERTA': 'Tipo_Gestión'}],
            'ALERTAS', 'ALERTAS'
        )
        datos_procesados.append(df_alertas)

    # 2.2 PROCESAR HOJA: REASIGNACIONES
    if 'REASIGNACIONES' in dict_repro:
        df_reasig = estandarizar_y_unir(
            dict_repro['REASIGNACIONES'],
            [{'FECHA GESTION 1': 'Fecha_Gestión', 'REPRO REA 1': 'Reprogramador'}],
            'REASIGNACIONES', 'REASIGNACIONES'
        )
        datos_procesados.append(df_reasig)

    # 3. PROCESAR QUANTIA - SUBSANACIONES
    # Hojas específicas con lógica de "OBSERVACIONES"
    hojas_subsanaciones = ['SUB-REINCIDENTES', 'SUBSANACIONES']
    for hoja in hojas_subsanaciones:
        if hoja in dict_quantia:
            df_sub = dict_quantia[hoja].copy()
            # Filtrar filas donde 'OBSERVACIONES' no esté vacía ni nula
            if 'OBSERVACIONES' in df_sub.columns:
                df_sub = df_sub.dropna(subset=['OBSERVACIONES'])
                df_sub = df_sub[df_sub['OBSERVACIONES'].astype(str).str.strip() != '']
            
            df_procesado = estandarizar_y_unir(
                df_sub,
                [{'FECHA': 'Fecha_Gestión', 'REPRO': 'Reprogramador'}],
                hoja, 'SUBSANACIONES' # Fuerza que el Tipo_Gestión sea SUBSANACIONES
            )
            datos_procesados.append(df_procesado)

    # Resto de hojas de Quantia
    for hoja, df in dict_quantia.items():
        if hoja not in hojas_subsanaciones:
            mapeo_quantia = [
                {'FECHA GESTION BO 1': 'Fecha_Gestión', 'BO ASIGNADO 1': 'Reprogramador'},
                {'FECHA GESTION BO 2': 'Fecha_Gestión', 'BO ASIGNADO 2': 'Reprogramador'},
                {'FECHA GESTION BO 3': 'Fecha_Gestión', 'BO ASIGNADO 3': 'Reprogramador'},
                {'FECHA GESTION BO 4': 'Fecha_Gestión', 'BO ASIGNADO 4': 'Reprogramador'}
            ]
            df_quantia = estandarizar_y_unir(df, mapeo_quantia, hoja, hoja.upper())
            datos_procesados.append(df_quantia)

    # 4. CONSOLIDAR TODO
    df_final = pd.concat(datos_procesados, ignore_index=True)
    
    # Limpieza final: asegurar que Tipo_Gestión esté en mayúsculas y sin espacios extra para el cruce
    df_final['Tipo_Gestión'] = df_final['Tipo_Gestión'].astype(str).str.strip().str.upper()

    # --- CRUCE CON GENESYS ---
    if 'Telefono' in df_final.columns:
        # Limpiar el teléfono de Excel (quitar '.0' si se leyó como decimal y extraer últimos 9)
        df_final['Telefono'] = df_final['Telefono'].astype(str).str.replace(r'\D', '', regex=True).str[-9:]
        
        # Unir por Teléfono Y Reprogramador
        df_final = df_final.merge(
            df_genesys_unicos,
            how='left',
            left_on=['Telefono', 'Reprogramador'],
            right_on=['Telefono_Cloud', 'Reprogramador_Cloud']
        )
        
        # Validar cruce
        condicion_vacio = df_final['Telefono'] == ''
        df_final['Validación_Genesys'] = df_final['Llamada_Cloud'].fillna('No')
        df_final.loc[condicion_vacio, 'Validación_Genesys'] = 'No aplica' # Para gestiones sin teléfono tipificado
        
        # Limpiar columnas auxiliares
        df_final.drop(columns=['Telefono_Cloud', 'Reprogramador_Cloud', 'Llamada_Cloud', 'Telefono'], inplace=True, errors='ignore')
    else:
        df_final['Validación_Genesys'] = 'No aplica'
    
    # 5. CRUZAR TMO
    # Si el Tipo_Gestión no está en la matriz, asigna 0 por defecto.
    df_final['TMO_Asignado'] = df_final['Tipo_Gestión'].map(TMO_MATRIX).fillna(0)

    print(f"✅ Transformación completa. Se consolidaron {len(df_final)} gestiones válidas.")
    return df_final