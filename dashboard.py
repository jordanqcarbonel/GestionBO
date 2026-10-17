import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, date
from pathlib import Path
from config.settings import RUTA_CONSOLIDADO

# ==============================================================================
# CONFIGURACIÓN GENERAL DE LA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Dashboard BO | Monitoreo TMO",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# FUNCIÓN DE CÁLCULO DE TMO LABORABLE
# ==============================================================================
def calcular_tmo_laborable(inicio: date, fin: date) -> int:
    """
    Replica =DIAS.LAB.INTL(inicio, fin, 11) * 450
    Excluye domingos y feriados definidos en LISTA_FERIADOS.
    """
    if inicio > fin:
        return 0
    fin_calculo = fin + timedelta(days=1)
    feriados_str = [normalizar_fecha(f).strftime('%Y-%m-%d') for f in LISTA_FERIADOS]
    dias = np.busday_count(inicio, fin_calculo, weekmask='1111110', holidays=feriados_str)
    return int(dias * 450)

# ==============================================================================
# ESTILOS CSS PERSONALIZADOS (IDENTIDAD CORPORATIVA)
# ==============================================================================
# Paleta de Marca: Azul Principal #005cff | Azul Secundario #118DFF
st.markdown("""
<style>
    /* Estilos globales y tipografía */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Ocultar barra superior genérica de Streamlit para acabado corporativo */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Pestañas estilizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.95rem;
        color: #64748b;
        border-radius: 8px 8px 0 0;
        padding: 10px 18px;
        transition: all 0.2s ease-in-out;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #005cff;
        background-color: #f0f5ff;
    }
    .stTabs [aria-selected="true"] {
        color: #005cff !important;
        border-bottom: 3px solid #005cff !important;
        background-color: #f8faff !important;
    }

    /* Podio Vertical Lateral (Columna Derecha) */
    .podium-vcard {
        background: #ffffff;
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 3px 14px rgba(0, 92, 255, 0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .podium-vcard:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0, 92, 255, 0.10);
    }
    .podium-vcard-first {
        border: 2px solid #005cff;
        background: linear-gradient(180deg, #f0f6ff 0%, #ffffff 100%);
        box-shadow: 0 6px 20px rgba(0, 92, 255, 0.12);
        padding: 16px 16px;
    }
    .podium-vcard-second {
        border-left: 5px solid #94a3b8;
    }
    .podium-vcard-third {
        border-left: 5px solid #d97706;
    }
    .podium-rank-tag {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .rank-tag-1 { background: #005cff; color: #ffffff; }
    .rank-tag-2 { background: #e2e8f0; color: #334155; }
    .rank-tag-3 { background: #fef3c7; color: #92400e; }
    .podium-name {
        font-size: 0.98rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.25;
    }
    .podium-pct {
        font-weight: 800;
        color: #005cff;
    }
    .podium-tmo {
        font-weight: 700;
        color: #334155;
    }
    .podium-meta-info {
        font-size: 0.74rem;
        color: #64748b;
        font-weight: 600;
        background: #f8faff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 3px 8px;
        display: inline-block;
    }
    .podium-meta-info-first {
        font-size: 0.74rem;
        color: #005cff;
        font-weight: 700;
        background: #e6f0ff;
        border: 1px solid #bed6ff;
        border-radius: 6px;
        padding: 3px 8px;
        display: inline-block;
    }

    /* Sidebar corporativo */
    [data-testid="stSidebar"] {
        background-color: #f8faff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Contenedor de estado vacío */
    .empty-state-box {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-left: 5px solid #005cff;
        border-radius: 12px;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0, 92, 255, 0.04);
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# FUNCIONES DE FORMATO Y UTILIDADES
# ==============================================================================
def format_pct(val) -> str:
    """
    Formatea porcentaje con símbolo % y máximo un decimal (ej. 95.5% o 102%).
    Evita decimales innecesarios cuando es entero exacto.
    """
    if pd.isna(val) or np.isnan(val):
        return "0%"
    pct = val * 100.0
    rounded = round(pct, 1)
    if rounded.is_integer():
        return f"{int(rounded)}%"
    return f"{rounded:.1f}%"


def format_tmo_int(val) -> str:
    """Formatea minutos de TMO como entero estricto sin decimales."""
    if pd.isna(val) or np.isnan(val):
        return "0"
    return f"{int(round(val))}"


# ==============================================================================
# CONFIGURACIÓN DE FERIADOS Y DÍAS NO LABORADOS POR ASESOR (BO)
# ==============================================================================
# 1. Lista de Feriados Oficiales (puedes agregar o modificar fechas en formato date o 'YYYY-MM-DD').
#    Se excluyen automáticamente de los días hábiles para todo el equipo.
LISTA_FERIADOS = [
    date(2026, 1, 1),   # Año Nuevo
    date(2026, 4, 2),   # Jueves Santo
    date(2026, 4, 3),   # Viernes Santo
    date(2026, 5, 1),   # Día del Trabajo
    date(2026, 6, 29),  # San Pedro y San Pablo
    date(2026, 7, 28),  # Fiestas Patrias
    date(2026, 7, 29),  # Fiestas Patrias
    date(2026, 8, 6),   # Batalla de Junín
    date(2026, 8, 30),  # Santa Rosa de Lima
    date(2026, 10, 8),  # Combate de Angamos
    date(2026, 11, 1),  # Todos los Santos
    date(2026, 12, 8),  # Inmaculada Concepción
    date(2026, 12, 9),  # Batalla de Ayacucho
    date(2026, 12, 25), # Navidad
]

# 2. Días no laborados individuales por cada analista Back Office (BO).
#    (Vacaciones, descansos médicos, licencias, permisos personales, etc.).
#    Cada día que caiga dentro del período seleccionado en día hábil (Lun-Sáb no feriado)
#    se descuenta de la meta de ese BO específico (-450 min/día).
#    Formato: Diccionario donde la clave es el nombre del BO y el valor es una lista de fechas.
DIAS_NO_LABORADOS_BO = {
    "EVELYN CELESTE MENDEZ QUISPILAYA": [date(2026, 10, 2)],
    "BRAYAN ANTONY RIVERA CONDOR": [date(2026, 10, 3), "2026-10-10", "2026-10-19"],
    # Ejemplos de configuración (añade o edita aquí):
    # "SOFIA ANGELICA TINEO OBREGON": [date(2026, 10, 5), "2026-10-06"],
    # "EVELYN CELESTE MENDEZ QUISPILAYA": [date(2026, 10, 2)],
}


def normalizar_fecha(f) -> date:
    """Convierte cadenas o timestamps a objetos date puros."""
    if isinstance(f, date) and not isinstance(f, pd.Timestamp):
        return f
    return pd.to_datetime(f).date()


def obtener_set_feriados() -> set[date]:
    """Retorna un conjunto de fechas de feriados normalizadas."""
    return {normalizar_fecha(f) for f in LISTA_FERIADOS}


def calcular_dias_laborables_base(inicio: date, fin: date) -> int:
    """
    Calcula los días laborables base (Lunes a Sábado, excluyendo domingos y feriados generales).
    """
    if inicio > fin:
        return 0
    fin_calculo = fin + timedelta(days=1)
    feriados_str = [normalizar_fecha(f).strftime('%Y-%m-%d') for f in LISTA_FERIADOS]
    dias = np.busday_count(inicio, fin_calculo, weekmask='1111110', holidays=feriados_str)
    return int(dias)


def obtener_fechas_no_laboradas_asesor(asesor: str) -> list[date]:
    """
    Obtiene las fechas no laboradas registradas para un asesor (soporta diccionario o lista).
    """
    fechas = []
    asesor_norm = str(asesor).strip().upper()
    if isinstance(DIAS_NO_LABORADOS_BO, dict):
        for nombre, lista in DIAS_NO_LABORADOS_BO.items():
            if str(nombre).strip().upper() == asesor_norm:
                fechas.extend([normalizar_fecha(f) for f in lista])
    elif isinstance(DIAS_NO_LABORADOS_BO, list):
        for item in DIAS_NO_LABORADOS_BO:
            if isinstance(item, dict):
                nom = item.get("asesor") or item.get("bo") or item.get("nombre")
                f = item.get("fecha") or item.get("dia")
                if nom and str(nom).strip().upper() == asesor_norm and f:
                    fechas.append(normalizar_fecha(f))
    return fechas


def calcular_meta_asesor(asesor: str, inicio: date, fin: date, opcion_periodo: str) -> dict:
    """
    Calcula los días laborables base del período, descuenta los días no laborados
    del asesor que caigan en días hábiles (Lun-Sáb no feriado), y obtiene su TMO objetivo.
    """
    if inicio > fin:
        return {"dias_base": 0, "dias_descontados": 0, "dias_efectivos": 0, "tmo_objetivo": 0}

    feriados_set = obtener_set_feriados()

    if opcion_periodo in ["Hoy", "Ayer"]:
        es_domingo = (inicio.weekday() == 6)
        es_feriado = (inicio in feriados_set)
        dias_base = 0 if (es_domingo or es_feriado) else 1
    else:
        dias_base = calcular_dias_laborables_base(inicio, fin)

    fechas_no_lab = obtener_fechas_no_laboradas_asesor(asesor)
    dias_descontados = 0
    fechas_descontadas = []

    for f in fechas_no_lab:
        if inicio <= f <= fin:
            # Solo descontar si era un día laborable (no domingo y no feriado)
            if f.weekday() != 6 and f not in feriados_set:
                dias_descontados += 1
                fechas_descontadas.append(f)

    dias_efectivos = max(0, dias_base - dias_descontados)
    tmo_objetivo = int(dias_efectivos * 450)

    return {
        "dias_base": dias_base,
        "dias_descontados": dias_descontados,
        "dias_efectivos": dias_efectivos,
        "tmo_objetivo": tmo_objetivo,
        "fechas_descontadas": fechas_descontadas
    }


# ==============================================================================
# CARGA DE DATOS
# ==============================================================================
@st.cache_data(ttl=0)
def cargar_datos():
    try:
        df = pd.read_csv(RUTA_CONSOLIDADO)
        df['Fecha_Gestión'] = pd.to_datetime(df['Fecha_Gestión'], errors='coerce')
        return df.dropna(subset=['Fecha_Gestión'])
    except Exception:
        return pd.DataFrame()


df_raw = cargar_datos()

if df_raw.empty:
    st.markdown("""
        <div class="empty-state-box">
            <h3 style="color: #005cff; margin-top: 0;">📡 No se encontraron datos disponibles</h3>
            <p style="color: #475569;">
                No fue posible cargar el archivo consolidado. Por favor ejecuta el pipeline de extracción
                o verifica que la ruta del consolidado contenga información válida.
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()


# ==============================================================================
# BARRA LATERAL: FILTROS DINÁMICOS Y CONTROL DE TIEMPO
# ==============================================================================
with st.sidebar:
    # Encabezado corporativo
    st.markdown("""
        <div style="text-align: center; padding: 12px 0 16px 0;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background: linear-gradient(135deg, #005cff, #118DFF); border-radius: 14px; box-shadow: 0 4px 12px rgba(0, 92, 255, 0.3); margin-bottom: 10px;">
                <span style="font-size: 28px;">📡</span>
            </div>
            <h3 style="color: #005cff; margin: 0; font-weight: 800; font-size: 1.25rem; letter-spacing: -0.02em;">
                BACK OFFICE ENTEL CONNECT
            </h3>
            <p style="color: #64748b; font-size: 0.8rem; margin-top: 3px; font-weight: 500;">
                Sistema de Monitoreo
            </p>
        </div>
        <hr style="margin: 8px 0 18px 0; border: none; border-top: 1px solid #e2e8f0;" />
    """, unsafe_allow_html=True)

    st.markdown("#### ⏱️ Período de Análisis")

    # Botones de selección rápida (Por defecto 'Hoy')
    opcion_periodo = st.radio(
        "Seleccione Período:",
        options=["Hoy", "Ayer", "Rango Personalizado"],
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )

    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    min_date_disponible = df_raw['Fecha_Gestión'].min().date()
    max_date_disponible = df_raw['Fecha_Gestión'].max().date()

    if opcion_periodo == "Hoy":
        fecha_inicio = hoy
        fecha_fin = hoy
        tmo_objetivo = 450
    elif opcion_periodo == "Ayer":
        fecha_inicio = ayer
        fecha_fin = ayer
        tmo_objetivo = 450
    else:
        # Inicio del mes actual por defecto
        inicio_mes_actual = hoy.replace(day=1)
        default_inicio = max(min_date_disponible, min(inicio_mes_actual, max_date_disponible))

        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_inicio = st.date_input(
                "📅 Fecha Inicio",
                value=default_inicio,
                min_value=min_date_disponible,
                max_value=max_date_disponible,
                format="DD/MM/YYYY"
            )
        with col_f2:
            # Calcular fin por defecto: ayer (si está dentro del rango) o inicio si ayer es anterior al rango disponible
            default_fin = min(max_date_disponible, ayer)
            if default_fin < default_inicio:
                default_fin = default_inicio
            fecha_fin = st.date_input(
                "📅 Fecha Fin",
                value=default_fin,
                min_value=min_date_disponible,
                max_value=max_date_disponible,
                format="DD/MM/YYYY"
            )

        if fecha_inicio > fecha_fin:
            st.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
            st.stop()

        tmo_objetivo = calcular_tmo_laborable(fecha_inicio, fecha_fin)

    # Tarjeta de Meta Dinámica en Sidebar
    st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 16px; margin: 18px 0 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 700; letter-spacing: 0.04em;">
                🎯 TMO Meta por BO
            </div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #005cff; margin-top: 2px;">
                {int(tmo_objetivo)} min
            </div>
            <div style="font-size: 0.76rem; color: #64748b; margin-top: 4px;">
                Período: <b>{fecha_inicio.strftime('%d/%m/%Y')}</b> al <b>{fecha_fin.strftime('%d/%m/%Y')}</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="font-size: 0.74rem; color: #94a3b8; text-align: center; margin-top: 15px;">
            Días laborables: Lun - Sáb (450 min/día)
        </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# FILTRADO Y PROCESAMIENTO DE DATOS
# ==============================================================================
mask_fechas = (df_raw['Fecha_Gestión'].dt.date >= fecha_inicio) & (df_raw['Fecha_Gestión'].dt.date <= fecha_fin)
df_filtrado = df_raw.loc[mask_fechas].copy()

# Encabezado principal del Dashboard (Sin espacios que rompan Markdown)
texto_periodo = fecha_inicio.strftime('%d/%m/%Y') if fecha_inicio == fecha_fin else f"{fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"

st.markdown(f"""<div style="margin-bottom: 16px;">
<h1 style="color: #0f172a; margin: 0; font-size: 2rem; font-weight: 800; letter-spacing: -0.03em;">
🚀 Centro de Monitoreo Back Office
</h1>
<p style="color: #64748b; font-size: 0.92rem; margin-top: 3px; margin-bottom: 0;">
Seguimiento de productividad y cumplimiento de TMO | Período: <span style="color: #005cff; font-weight: 600;">{texto_periodo}</span>
</p>
</div>""", unsafe_allow_html=True)

# Validación de datos para el período seleccionado
if df_filtrado.empty:
    st.markdown(f"""<div class="empty-state-box">
<h3 style="color: #005cff; margin-top: 0;">📅 Sin registros para el período seleccionado</h3>
<p style="color: #334155; font-size: 0.95rem;">
No se encontraron gestiones registradas para la fecha <b>{texto_periodo}</b>.
</p>
<p style="color: #64748b; font-size: 0.88rem; margin-bottom: 0;">
💡 <b>Sugerencia:</b> Si estás consultando "Hoy", es posible que la carga del día aún no haya sido consolidada.
Puedes seleccionar <b>"Ayer"</b> o <b>"Rango Personalizado"</b> en la barra lateral para revisar datos históricos.
<br><em>Última fecha con gestiones registradas: <b>{max_date_disponible.strftime('%d/%m/%Y')}</b></em>.
</p>
</div>""", unsafe_allow_html=True)
    st.stop()

# Agrupar TMO por Asesor
df_resumen = df_filtrado.groupby('Reprogramador', as_index=False)['TMO_Asignado'].sum()
df_resumen.columns = ['BACK OFFICE', 'TOTAL_TMO']

# Asegurar enteros estrictos en TMO
df_resumen['TOTAL_TMO'] = df_resumen['TOTAL_TMO'].round().astype(int)

# Cálculo de cumplimiento individualizado por asesor (aplicando días no laborados)
metas_individuales = []
for idx, row in df_resumen.iterrows():
    asesor_nombre = row['BACK OFFICE']
    # Calcula la meta específica del asesor usando su lista de días no laborados
    res_meta = calcular_meta_asesor(asesor_nombre, fecha_inicio, fecha_fin, opcion_periodo)
    metas_individuales.append(res_meta['tmo_objetivo'])

df_resumen['TMO_OBJETIVO_INDIVIDUAL'] = metas_individuales

# Evitar división por cero si la meta individual es 0
df_resumen['CUMPLIMIENTO'] = df_resumen.apply(
    lambda r: r['TOTAL_TMO'] / r['TMO_OBJETIVO_INDIVIDUAL'] if r['TMO_OBJETIVO_INDIVIDUAL'] > 0 else 0.0,
    axis=1
)

# Ordenar de mayor a menor cumplimiento
df_resumen = df_resumen.sort_values(by='CUMPLIMIENTO', ascending=False).reset_index(drop=True)
df_resumen['RANKING'] = range(1, len(df_resumen) + 1)
total_asesores = int(len(df_resumen))

# ==============================================================================
# DISTRIBUCIÓN DE PANTALLA: PESTAÑAS (IZQUIERDA) Y PODIO VERTICAL (DERECHA)
# ==============================================================================
col_main, col_podio = st.columns([2.3, 1], gap="large")

# ------------------------------------------------------------------------------
# COLUMNA IZQUIERDA: PESTAÑAS PRINCIPALES
# ------------------------------------------------------------------------------
with col_main:
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Ranking General",
        "👤 Mi Avance Individual",
        "📋 Tabla Resumida",
        "☁️ Cruce Gestión Cloud"
    ])

    # ==========================================================================
    # PESTAÑA 1: RANKING GENERAL
    # ==========================================================================
    with tab1:
        st.markdown("### 📊 Ranking General de Cumplimiento de TMO")
        st.caption("Comparativa del cumplimiento de todo el equipo de Back Office respecto a la meta establecida.")

        # Gráfico de Barras Horizontales con gradiente corporativo azul (#118DFF a #005cff)
        df_ranking_chart = df_resumen.sort_values(by='CUMPLIMIENTO', ascending=True).copy()
        df_ranking_chart['CUMPLIMIENTO_TXT'] = df_ranking_chart['CUMPLIMIENTO'].apply(format_pct)
        df_ranking_chart['TOTAL_TMO_INT'] = df_ranking_chart['TOTAL_TMO'].astype(int)

        fig_ranking = px.bar(
            df_ranking_chart,
            x='CUMPLIMIENTO',
            y='BACK OFFICE',
            orientation='h',
            text='CUMPLIMIENTO_TXT',
            color='CUMPLIMIENTO',
            color_continuous_scale=[
                [0.0, '#99c2ff'],
                [0.5, '#118DFF'],
                [1.0, '#005cff']
            ],
            title="<b>Ranking General de Cumplimiento de TMO</b>"
        )

        # Línea vertical punteada en 100% (1.0)
        fig_ranking.add_vline(
            x=1.0,
            line_dash="dash",
            line_color="#005cff",
            line_width=2,
            annotation_text="🎯 Meta 100%",
            annotation_position="top right",
            annotation_font=dict(color="#005cff", size=12, family="Inter, sans-serif")
        )

        fig_ranking.update_traces(
            textposition='outside',
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Cumplimiento: %{text}<br>TMO Asignado: %{customdata} min<extra></extra>",
            customdata=df_ranking_chart['TOTAL_TMO_INT']
        )

        fig_ranking.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=40, t=50, b=20),
            height=max(400, len(df_ranking_chart) * 44),
            font=dict(family="Inter, sans-serif", color="#1e293b"),
            title_font=dict(size=16, color="#0f172a"),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=True,
                tickformat='.0%',
                title=dict(text="Porcentaje de Cumplimiento", font=dict(color="#64748b", size=12))
            ),
            yaxis=dict(
                showgrid=False,
                title=None,
                tickfont=dict(color="#1e293b", size=12)
            )
        )

        st.plotly_chart(fig_ranking, use_container_width=True)

    # ==========================================================================
    # PESTAÑA 2: MI AVANCE INDIVIDUAL (AUTOMONITOREO)
    # ==========================================================================
    with tab2:
        st.markdown("### 👤 Automonitoreo de Rendimiento Individual")
        st.caption("Selecciona tu nombre para revisar en detalle tu velocímetro de TMO, gestiones y recomendaciones dinámicas.")

        lista_asesores = df_resumen['BACK OFFICE'].sort_values().tolist()
        if not lista_asesores:
            st.info("No hay analistas registrados en este período.")
        else:
            col_sel1, col_sel2 = st.columns([2, 1])
            with col_sel1:
                asesor_seleccionado = st.selectbox(
                    "Seleccionar detalle de Back Office:",
                    options=lista_asesores,
                    index=0
                )

            # Extracción de métricas individuales con fallback seguro
            asesor_match = df_resumen[df_resumen['BACK OFFICE'] == asesor_seleccionado]
            if asesor_match.empty:
                datos_asesor = df_resumen.iloc[0]
                asesor_seleccionado = datos_asesor['BACK OFFICE']
            else:
                datos_asesor = asesor_match.iloc[0]

            tmo_actual = int(datos_asesor['TOTAL_TMO'])
            cumplimiento_actual = float(datos_asesor['CUMPLIMIENTO'])
            tmo_faltante = max(0, int(tmo_objetivo - tmo_actual))
            pct_actual_num = cumplimiento_actual * 100.0

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # Mensaje motivacional dinámico en cuadro estilizado según rango de cumplimiento
            if cumplimiento_actual < 0.80:
                st.warning(
                    f"⚡ **¡Acelera el ritmo para alcanzar el objetivo!**  \n"
                    f"Actualmente te encuentras al **{format_pct(cumplimiento_actual)}** de tu meta. "
                    f"Te faltan **{tmo_faltante} minutos** de TMO para alcanzar el 100% ({int(tmo_objetivo)} min). "
                    f"¡Prioriza gestiones pendientes de alto TMO para cerrar la brecha hoy!"
                )
            elif cumplimiento_actual < 1.00:
                st.info(
                    f"🎯 **¡Estás en la recta final hacia la meta!**  \n"
                    f"Llevas un sólido avance del **{format_pct(cumplimiento_actual)}**. "
                    f"Solo te faltan **{tmo_faltante} minutos** de TMO para asegurar tu 100% ({int(tmo_objetivo)} min). "
                    f"¡Un último esfuerzo y aseguras tu resultado!"
                )
            else:
                excedente = tmo_actual - int(tmo_objetivo)
                st.success(
                    f"🎉 **¡Felicitaciones! Objetivo asegurado y superado.**  \n"
                    f"Has alcanzado un destacado **{format_pct(cumplimiento_actual)}** de cumplimiento con **{tmo_actual} minutos** registrados "
                    f"(+**{excedente} min** sobre la meta). ¡Excelente trabajo y aporte a los estándares del equipo!"
                )

            col_gauge, col_pie = st.columns([1, 1], gap="medium")

            with col_gauge:
                # Velocímetro (go.Indicator) con barra en #005cff
                max_gauge_axis = max(150, int(pct_actual_num) + 15)

                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=round(pct_actual_num, 1),
                    number={
                        'suffix': "%",
                        'valueformat': ".1f",
                        'font': {'color': '#005cff', 'family': 'Inter, sans-serif', 'size': 44}
                    },
                    title={
                        'text': f"<b>Velocímetro de Cumplimiento</b><br><span style='font-size:12px;color:#64748b;'>{asesor_seleccionado}</span>",
                        'font': {'size': 16, 'color': '#0f172a', 'family': 'Inter, sans-serif'}
                    },
                    gauge={
                        'axis': {'range': [0, max_gauge_axis], 'tickwidth': 1, 'tickcolor': '#94a3b8'},
                        'bar': {'color': "#005cff", 'thickness': 0.28},
                        'bgcolor': "#ffffff",
                        'borderwidth': 1,
                        'bordercolor': "#e2e8f0",
                        'steps': [
                            {'range': [0, 80], 'color': "#fee2e2"},       # Rojo corporativo suave (0 - 80%)
                            {'range': [80, 100], 'color': "#fef3c7"},      # Amarillo corporativo suave (80 - 99%)
                            {'range': [100, max_gauge_axis], 'color': "#dcfce7"} # Verde corporativo (100%+)
                        ],
                        'threshold': {
                            'line': {'color': "#118DFF", 'width': 3},
                            'thickness': 0.75,
                            'value': 100
                        }
                    }
                ))

                fig_gauge.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=60, b=20),
                    height=340
                )

                st.plotly_chart(fig_gauge, use_container_width=True)

                # Micro-tarjetas informativas del analista
                sub_c1, sub_c2 = st.columns(2)
                with sub_c1:
                    st.metric(
                        label="TMO Generado",
                        value=f"{tmo_actual} min",
                        delta=f"{tmo_actual - int(tmo_objetivo)} min vs Meta"
                    )
                with sub_c2:
                    st.metric(
                        label="Posición en Ranking",
                        value=f"#{int(datos_asesor['RANKING'])} de {total_asesores}",
                        delta=f"{format_pct(cumplimiento_actual)} cumplimiento"
                    )

            with col_pie:
                # Gráfico de Anillos (px.pie con hole=0.5)
                df_asesor_detalle = df_filtrado[df_filtrado['Reprogramador'] == asesor_seleccionado]
                conteo_gestiones = df_asesor_detalle['Tipo_Gestión'].value_counts().reset_index()
                conteo_gestiones.columns = ['Tipo de Gestión', 'Cantidad']

                if not conteo_gestiones.empty:
                    fig_donut = px.pie(
                        conteo_gestiones,
                        values='Cantidad',
                        names='Tipo de Gestión',
                        hole=0.5,
                        title="<b>Distribución de Gestiones Realizadas</b>",
                        color_discrete_sequence=[
                            '#005cff',  # Azul Principal
                            '#118DFF',  # Azul Secundario
                            '#38b6ff',  # Celeste brillante
                            '#003ecb',  # Azul oscuro
                            '#60a5fa',  # Azul suave
                            '#00247d',  # Azul marino
                            '#93c5fd'   # Azul pastel
                        ]
                    )

                    fig_donut.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        marker=dict(line=dict(color='#ffffff', width=2)),
                        hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>Participación: %{percent}<extra></extra>"
                    )

                    fig_donut.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Inter, sans-serif", color="#1e293b"),
                        title_font=dict(size=16, color="#0f172a"),
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                        margin=dict(l=20, r=20, t=60, b=20),
                        height=340
                    )

                    st.plotly_chart(fig_donut, use_container_width=True)
                else:
                    st.info("No se registraron tipificaciones de gestión para este asesor en el período.")

    # ==========================================================================
    # PESTAÑA 3: TABLA RESUMIDA LIMPIA
    # ==========================================================================
    with tab3:
        st.markdown("### 📋 Resumen Directivo y Consolidado de Cumplimiento")
        st.caption("Visión tabulada con seguimiento porcentual mediante barra de progreso hasta el 150%.")

        # Preparación de DataFrame para visualización
        df_tabla = df_resumen.copy()

        # Estado semafórico informativo antes de convertir
        df_tabla['ESTADO'] = df_tabla['CUMPLIMIENTO'].apply(
            lambda c: '🎯 Meta Cumplida' if c >= 1.0 else ('⚡ Recta Final' if c >= 0.8 else '⚠️ Por Acelerar')
        )

        # Escalar a base 100% para evitar confusiones (ej. 1.0 -> 100.0%)
        df_tabla['CUMPLIMIENTO'] = (df_tabla['CUMPLIMIENTO'] * 100.0).round(1)

        st.dataframe(
            df_tabla[['RANKING', 'BACK OFFICE', 'TOTAL_TMO', 'CUMPLIMIENTO', 'ESTADO']],
            column_config={
                "RANKING": st.column_config.NumberColumn(
                    "Puesto",
                    format="#%d",
                    width="small",
                    help="Posición en el ranking de cumplimiento del equipo"
                ),
                "BACK OFFICE": st.column_config.TextColumn(
                    "Analista Back Office",
                    width="large"
                ),
                "TOTAL_TMO": st.column_config.NumberColumn(
                    "TMO Generado (minutos)",
                    format="%d",
                    help="Tiempo Medio de Operación total asignado (minutos enteros)."
                ),
                "CUMPLIMIENTO": st.column_config.ProgressColumn(
                    "Nivel de Cumplimiento",
                    format="%.1f%%",
                    min_value=0.0,
                    max_value=150.0,
                    help="Barra visual de progreso hacia el objetivo (base 100%, escala hasta 150%)."
                ),
                "ESTADO": st.column_config.TextColumn(
                    "Estado",
                    width="medium"
                )
            },
            hide_index=True,
            use_container_width=True
        )

        # Botón para descargar reporte en CSV si se requiere auditoría
        csv_data = df_tabla.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Descargar Reporte en CSV",
            data=csv_data,
            file_name=f"reporte_cumplimiento_bo_{fecha_inicio.strftime('%d%m%Y')}.csv",
            mime="text/csv"
        )

    # ==========================================================================
    # PESTAÑA 4: CRUCE GESTIÓN CLOUD (GENESYS) - ENFOQUE EJECUTIVO EN DESVÍOS
    # ==========================================================================
    with tab4:
        st.markdown(
            """
            <div style="margin-bottom: 12px;">
                <h3 style="margin: 0; color: #005cff; font-weight: 700;">☁️ GESTIÓN REPRO - CAIDAS: Cruce Genesys Cloud</h3>
                <p style="margin: 2px 0 0 0; color: #64748b; font-size: 0.85rem;">
                    Auditoría entre gestión tipificada en el drive vs llamadas reales en Genesys.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if 'Validación_Genesys' in df_filtrado.columns:
            hojas_validas = ['APP', 'FONO', 'DIG', 'REPRO TLV', 'CAIDAS'] 
            gestiones_telefonicas = ['CONTACTO VALIDO', 'CONTACTO NO VALIDO']
            
            # Filtro estricto del universo auditable
            df_cloud = df_filtrado[
                (df_filtrado['Validación_Genesys'].isin(['Sí', 'No'])) & 
                (df_filtrado['Hoja_Origen'].isin(hojas_validas)) &
                (df_filtrado['Tipo_Gestión'].isin(gestiones_telefonicas))
            ].copy()
            
            if not df_cloud.empty:
                # --------------------------------------------------------------
                # 1. CÁLCULO DE MÉTRICAS GLOBALES
                # --------------------------------------------------------------
                total_gestiones = len(df_cloud)
                total_con_cloud = (df_cloud['Validación_Genesys'] == 'Sí').sum()
                total_sin_cloud = (df_cloud['Validación_Genesys'] == 'No').sum()
                tasa_global_efectividad = (total_con_cloud / total_gestiones) * 100 if total_gestiones > 0 else 0.0
                tasa_global_error = (total_sin_cloud / total_gestiones) * 100 if total_gestiones > 0 else 0.0

                # --------------------------------------------------------------
                # 2. TARJETAS KPI RESUMEN (RESPONSIVE PARA PANELES CON PODIO)
                # --------------------------------------------------------------
                col_k1, col_k2, col_k3, col_k4 = st.columns(4)
                
                with col_k1:
                    st.metric(
                        label="Total Gestiones",
                        value=f"{total_gestiones:,}".replace(",", ".")
                    )
                with col_k2:
                    st.metric(
                        label="Llamadas Validadas",
                        value=f"{total_con_cloud:,}".replace(",", "."),
                        delta=f"{tasa_global_efectividad:.0f}%"
                    )
                with col_k3:
                    st.metric(
                        label="Sin Registro Cloud",
                        value=f"{total_sin_cloud:,}".replace(",", "."),
                        delta=f"{tasa_global_error:.1f}% Error",
                        delta_color="inverse"
                    )
                with col_k4:
                    status_text = "🟢 ÓPTIMO" if tasa_global_efectividad >= 95 else ("🟡 ALERTA" if tasa_global_efectividad >= 93 else "🔴 CRÍTICO")
                    st.metric(
                        label="Estado",
                        value=status_text
                    )

                st.markdown("<hr style='margin: 8px 0 14px 0; border: none; border-top: 1px solid #e2e8f0;'/>", unsafe_allow_html=True)

                # --------------------------------------------------------------
                # 3. CONSOLIDACIÓN DE DATOS POR BACK OFFICE (BO)
                # --------------------------------------------------------------
                resumen_bo = []
                col_agente = 'Reprogramador' if 'Reprogramador' in df_cloud.columns else df_cloud.columns[0]
                lista_bo = sorted(df_cloud[col_agente].dropna().unique())

                for agente in lista_bo:
                    df_a = df_cloud[df_cloud[col_agente] == agente]
                    n_tot = len(df_a)
                    if n_tot == 0:
                        continue
                    
                    # Contacto Válido
                    df_val = df_a[df_a['Tipo_Gestión'] == 'CONTACTO VALIDO']
                    n_val = len(df_val)
                    asert_val = ((df_val['Validación_Genesys'] == 'Sí').sum() / n_val * 100) if n_val > 0 else 100.0

                    # Contacto No Válido
                    df_noval = df_a[df_a['Tipo_Gestión'] == 'CONTACTO NO VALIDO']
                    n_noval = len(df_noval)
                    asert_noval = ((df_noval['Validación_Genesys'] == 'Sí').sum() / n_noval * 100) if n_noval > 0 else 100.0

                    # Métricas globales del BO
                    con_cloud_a = (df_a['Validación_Genesys'] == 'Sí').sum()
                    sin_cloud_a = n_tot - con_cloud_a
                    asert_global = (con_cloud_a / n_tot) * 100
                    error_global = (sin_cloud_a / n_tot) * 100

                    resumen_bo.append({
                        "Back Office": agente,
                        "Total Base": n_tot,
                        "Sin Cloud": sin_cloud_a,
                        "C. Válido (%)": asert_val,
                        "C. No Válido (%)": asert_noval,
                        "Cumplimiento Global (%)": asert_global,
                        "% Desvío": error_global
                    })

                df_resumen_cloud = pd.DataFrame(resumen_bo)

                if not df_resumen_cloud.empty:
                    # Ordenar priorizando a quienes presentan mayor volumen y tasa de error
                    df_resumen_cloud = df_resumen_cloud.sort_values(by=["Sin Cloud", "% Desvío"], ascending=[False, False]).reset_index(drop=True)

                    st.markdown("#### 📋 Resumen por Tipo de Contacto")
                    
                    # El foco visual va hacia % Desvío con ProgressColumn
                    st.dataframe(
                        df_resumen_cloud,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Back Office": st.column_config.TextColumn(
                                "Back Office",
                                help="Nombre de Back Office evaluado",
                                width="medium"
                            ),
                            "Total Gestiones": st.column_config.NumberColumn(
                                "Total Gestiones",
                                format="%d"
                            ),
                            "Sin Cloud": st.column_config.NumberColumn(
                                "❌ Sin Cloud",
                                help="Cantidad de llamadas tipificadas que no figuran en Genesys Cloud",
                                format="%d"
                            ),
                            "C. Válido (%)": st.column_config.NumberColumn(
                                "C. Válido (%)",
                                help="% de llamadas 'Contacto Válido' validadas en Genesys Cloud",
                                format="%.0f%%"
                            ),
                            "C. No Válido (%)": st.column_config.NumberColumn(
                                "C. No Válido (%)",
                                help="% de llamadas 'Contacto No Válido' validadas en Genesys Cloud",
                                format="%.0f%%"
                            ),
                            "Cumplimiento Global (%)": st.column_config.NumberColumn(
                                "Cumplimiento (%)",
                                help="Tasa global de gestión efectiva",
                                format="%.1f%%"
                            ),
                            "% Desvío": st.column_config.ProgressColumn(
                                "Error (%)",
                                help="Tasa de incumplimiento telefónico / error tipificación",
                                format="%.2f%%",
                                min_value=0.0,
                                max_value=max(float(df_resumen_cloud["% Desvío"].max() or 5.0), 5.0)  # Escala inteligente al desvío real
                            )
                        }
                    )
                else:
                    st.info("No se pudieron consolidar métricas por Back Office.")
            else:
                st.info("No hay datos de Contacto Válido/No Válido para cruzar en el rango de fechas seleccionado.")
        else:
            st.warning("⚠️ La columna 'Validación_Genesys' no existe. Asegúrate de haber ejecutado el pipeline de extracción.")

# ------------------------------------------------------------------------------
# COLUMNA DERECHA: PODIO DE HONOR VERTICAL (ALINEADO Y SIN SCROLL)
# ------------------------------------------------------------------------------
with col_podio:
    st.markdown("""<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
<h3 style="color: #0f172a; margin: 0; font-size: 1.25rem; font-weight: 800;">🏆 Podio de Honor</h3>
<span style="background: #e6f0ff; color: #005cff; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">TOP 3</span>
</div>
<p style="color: #64748b; font-size: 0.78rem; margin-top: 0; margin-bottom: 12px;">
TOP en cumplimiento Back Office
</p>""", unsafe_allow_html=True)

    if len(df_resumen) >= 3:
        primero = df_resumen.iloc[0]
        segundo = df_resumen.iloc[1]
        tercero = df_resumen.iloc[2]

        dif1 = int(primero['TOTAL_TMO']) - int(tmo_objetivo)
        dif2 = int(segundo['TOTAL_TMO']) - int(tmo_objetivo)
        dif3 = int(tercero['TOTAL_TMO']) - int(tmo_objetivo)

        dif_txt1 = f"+{dif1} min" if dif1 >= 0 else f"{dif1} min"
        dif_txt2 = f"+{dif2} min" if dif2 >= 0 else f"{dif2} min"
        dif_txt3 = f"+{dif3} min" if dif3 >= 0 else f"{dif3} min"

        # 1° Lugar (Arriba)
        st.markdown(f"""<div class="podium-vcard podium-vcard-first">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
    <span style="font-size: 1.6rem;">👑</span>
    <span class="podium-rank-tag rank-tag-1">🥇 1° Lugar • Campeón</span>
</div>
<div class="podium-name" style="color: #005cff; font-size: 1rem; font-weight: 800; margin-bottom: 6px;">{primero['BACK OFFICE']}</div>
<div style="display: flex; align-items: baseline; justify-content: space-between; margin: 4px 0;">
    <span class="podium-pct" style="font-size: 2.1rem; line-height: 1;">{format_pct(primero['CUMPLIMIENTO'])}</span>
    <span class="podium-tmo" style="color: #005cff; font-size: 1.05rem; font-weight: 800;">⏱️ {format_tmo_int(primero['TOTAL_TMO'])} min</span>
</div>
<div style="margin-top: 4px;">
    <span class="podium-meta-info-first">Meta: {int(tmo_objetivo)} min ({dif_txt1})</span>
</div>
</div>""", unsafe_allow_html=True)

        # 2do Lugar (Centro)
        st.markdown(f"""<div class="podium-vcard podium-vcard-second">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
    <span style="font-size: 1.3rem;">🥈</span>
    <span class="podium-rank-tag rank-tag-2">2° Lugar</span>
</div>
<div class="podium-name" style="font-size: 0.92rem; margin-bottom: 6px;">{segundo['BACK OFFICE']}</div>
<div style="display: flex; align-items: baseline; justify-content: space-between; margin: 4px 0;">
    <span class="podium-pct" style="font-size: 1.7rem; line-height: 1;">{format_pct(segundo['CUMPLIMIENTO'])}</span>
    <span class="podium-tmo" style="font-size: 0.95rem;">⏱️ {format_tmo_int(segundo['TOTAL_TMO'])} min</span>
</div>
<div style="margin-top: 4px;">
    <span class="podium-meta-info">Meta: {int(tmo_objetivo)} min ({dif_txt2})</span>
</div>
</div>""", unsafe_allow_html=True)

        # 3er Lugar (Abajo)
        st.markdown(f"""<div class="podium-vcard podium-vcard-third">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
    <span style="font-size: 1.3rem;">🥉</span>
    <span class="podium-rank-tag rank-tag-3">3° Lugar</span>
</div>
<div class="podium-name" style="font-size: 0.92rem; margin-bottom: 6px;">{tercero['BACK OFFICE']}</div>
<div style="display: flex; align-items: baseline; justify-content: space-between; margin: 4px 0;">
    <span class="podium-pct" style="font-size: 1.7rem; line-height: 1;">{format_pct(tercero['CUMPLIMIENTO'])}</span>
    <span class="podium-tmo" style="font-size: 0.95rem;">⏱️ {format_tmo_int(tercero['TOTAL_TMO'])} min</span>
</div>
<div style="margin-top: 4px;">
    <span class="podium-meta-info">Meta: {int(tmo_objetivo)} min ({dif_txt3})</span>
</div>
</div>""", unsafe_allow_html=True)

    elif len(df_resumen) > 0:
        for idx in range(len(df_resumen)):
            row = df_resumen.iloc[idx]
            dif = int(row['TOTAL_TMO']) - int(tmo_objetivo)
            dif_txt = f"+{dif} min" if dif >= 0 else f"{dif} min"
            st.markdown(f"""<div class="podium-vcard podium-vcard-first">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
    <span style="font-size: 1.4rem;">{'🥇' if idx == 0 else '🥈'}</span>
    <span class="podium-rank-tag rank-tag-1">Puesto #{idx + 1}</span>
</div>
<div class="podium-name" style="color: #005cff; font-size: 0.95rem; margin-bottom: 6px;">{row['BACK OFFICE']}</div>
<div style="display: flex; align-items: baseline; justify-content: space-between; margin: 4px 0;">
    <span class="podium-pct" style="font-size: 1.75rem; line-height: 1;">{format_pct(row['CUMPLIMIENTO'])}</span>
    <span class="podium-tmo" style="font-size: 0.95rem;">⏱️ {format_tmo_int(row['TOTAL_TMO'])} min</span>
</div>
<div style="margin-top: 4px;">
    <span class="podium-meta-info-first">Meta: {int(tmo_objetivo)} min ({dif_txt})</span>
</div>
</div>""", unsafe_allow_html=True)