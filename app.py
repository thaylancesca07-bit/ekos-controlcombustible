import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import io
import tempfile
from datetime import date, datetime, timedelta
from fpdf import FPDF
from docx import Document
from docx.shared import Inches

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

# ESTILOS CSS CORREGIDOS (Todo Claro con Texto Oscuro)
st.markdown("""
    <style>
    /* Fondo General de la App */
    .stApp {
        background-color: #f7f7e8; /* Beige muy suave */
        color: #0b0f19; /* Azul muy oscuro casi negro */
    }
    
    /* Textos Generales */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, div, span {
        color: #0b0f19 !important;
    }

    /* --- INPUTS (Cajas de texto y números) --- */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        color: #0b0f19 !important;
        background-color: #ffffff !important; /* Blanco para escribir */
        border: 1px solid #b0a890 !important; /* Borde marrón suave */
        border-radius: 5px;
    }
    
    /* --- SELECTBOX (Listas desplegables: Año, Máquina, etc.) --- */
    /* El contenedor principal del selector */
    div[data-baseweb="select"] > div {
        background-color: #e6e2d3 !important; /* Marrón claro */
        color: #0b0f19 !important;
        border: 1px solid #0b0f19 !important; /* Borde definido */
    }
    /* El texto dentro del selector */
    .stSelectbox div[data-baseweb="select"] span {
        color: #0b0f19 !important;
    }
    /* El ícono de la flechita */
    .stSelectbox svg {
        fill: #0b0f19 !important;
    }
    /* El menú desplegable (las opciones) */
    ul[data-baseweb="menu"] {
        background-color: #f7f7e8 !important;
        border: 1px solid #0b0f19 !important;
    }
    li[data-baseweb="option"] {
        color: #0b0f19 !important;
    }

    /* --- BOTONES (Guardar, Descargar, etc.) --- */
    .stButton > button, .stDownloadButton > button {
        background-color: #e6e2d3 !important; /* Marrón claro */
        color: #0b0f19 !important; /* Texto Oscuro */
        border: 1px solid #0b0f19 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1) !important;
    }
    
    /* Efecto al pasar el mouse (Hover) */
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: #d1ccb8 !important; /* Un poco más oscuro */
        color: #0b0f19 !important;
        border-color: #0b0f19 !important;
    }

    /* Asegurar que el texto dentro del botón sea oscuro */
    .stButton > button p, .stDownloadButton > button p {
        color: #0b0f19 !important;
    }

    /* --- CALENDARIO (Date Picker) --- */
    div[data-baseweb="calendar"] {
        background-color: #ffffff !important;
        color: #0b0f19 !important;
    }
    div[data-baseweb="calendar"] button {
        color: #0b0f19 !important; /* Flechas oscuras */
    }
    div[role="grid"] div {
        color: #0b0f19 !important; /* Números oscuros */
    }
    div[aria-selected="true"] {
        background-color: #e6e2d3 !important; /* Selección marrón claro */
        color: #0b0f19 !important;
        font-weight: bold;
    }

    /* --- TABLAS (Dataframes) --- */
    div[data-testid="stDataFrame"] {
        background-color: #fffcf0 !important;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #b0a890;
    }
    </style>
""", unsafe_allow_html=True)

# URL del Script de Google
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwnPU3LdaHqrNO4bTsiBMKmm06ZSm3dUbxb5OBBnHBQOHRSuxcGv_MK4jWNHsrAn3M/exec"
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

ACCESS_CODE_MAESTRO = "1645"
TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]
MARGEN_TOLERANCIA = 0.20 

MAPA_COMBUSTIBLE = {
    "4002147 - Diesel EURO 5 S-50": "Diesel S500",
    "4002151 - NAFTA GRID 95": "Nafta",
    "4001812 - Diesel podium S-10 gr.": "Diesel Podium"
}

ENCARGADOS_DATA = {
    "Juan Britez": {"pwd": "jb2026", "barril": "Barril Juan"},
    "Diego Bordon": {"pwd": "db2026", "barril": "Barril Diego"},
    "Jonatan Vargas": {"pwd": "jv2026", "barril": "Barril Jonatan"},
    "Cesar Cabañas": {"pwd": "cc2026", "barril": "Barril Cesar"},
    "Auditoria": {"pwd": "1645", "barril": "Acceso Total"}
}
BARRILES_LISTA = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

FLOTA = {
    "HV-01": {"nombre": "Caterpilar 320D", "unidad": "Horas", "ideal": 18.0}, 
    "JD-01": {"nombre": "John Deere", "unidad": "Horas", "ideal": 15.0},
    "M-11": {"nombre": "N. Frontier", "unidad": "KM", "ideal": 9.0},
    "M-17": {"nombre": "GM S-10", "unidad": "KM", "ideal": 10.0},
    "V-12": {"nombre": "Valtra 180", "unidad": "Horas", "ideal": 12.0},
    "JD-03": {"nombre": "John Deere 6110", "unidad": "Horas", "ideal": 10.0},
    "MC-06": {"nombre": "MB Canter", "unidad": "KM", "ideal": 6.0},
    "M-02": {"nombre": "Chevrolet - S10", "unidad": "KM", "ideal": 8.0},
    "JD-02": {"nombre": "John Deere 6170", "unidad": "Horas", "ideal": 16.0},
    "MF-02": {"nombre": "Massey", "unidad": "Horas", "ideal": 9.0},
    "V-07": {"nombre": "Valmet 1580", "unidad": "Horas", "ideal": 11.0},
    "TM-01": {"nombre": "Pala Michigan", "unidad": "Horas", "ideal": 14.0},
    "JD-04": {"nombre": "John Deere 5090", "unidad": "Horas", "ideal": 8.0},
    "V-02": {"nombre": "Valmet 785", "unidad": "Horas", "ideal": 7.0},
    "V-11": {"nombre": "Valmet 8080", "unidad": "Horas", "ideal": 9.5},
    "M13": {"nombre": "Nisan Frontier (M13)", "unidad": "Horas", "ideal": 5.0},
    "TF01": {"nombre": "Ford", "unidad": "Horas", "ideal": 0.0},
    "MICHIGAN": {"nombre": "Pala Michigan", "unidad": "Horas", "ideal": 14.0},
    "S-08": {"nombre": "Scania Rojo", "unidad": "KM", "ideal": 2.2},
    "S-05": {"nombre": "Scania Azul", "unidad": "KM", "ideal": 2.4},
    "M-03": {"nombre": "GM S-10 (M-03)", "unidad": "KM", "ideal": 8.5},
    "S-03": {"nombre": "Scania 113H", "unidad": "KM", "ideal": 2.3},
    "S-06": {"nombre": "Scania P112H", "unidad": "Horas", "ideal": 0.0},
    "S-07": {"nombre": "Scania R380", "unidad": "Horas", "ideal": 0.0},
    "O-01": {"nombre": "Otros", "unidad": "Horas", "ideal": 0.0}
}

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        titulo = 'INFORME EJECUTIVO - CONTROL EKOS'.encode('latin-1', 'replace').decode('latin-1')
        subtitulo = 'Excelencia Consultora - Nueva Esperanza'.encode('latin-1', 'replace').decode('latin-1')
        self.cell(0, 10, titulo, 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, subtitulo, 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos Ekos')
        worksheet = writer.sheets['Datos Ekos']
        worksheet.set_column('A:N', 20)
    return output.getvalue()

def generar_word(df_data, titulo_reporte, grafico_fig=None):
    doc = Document()
    doc.add_heading(titulo_reporte, 0)
    doc.add_paragraph('Generado por Sistema Ekos Control')
    if grafico_fig:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            grafico_fig.savefig(tmpfile.name, format='png')
            doc.add_picture(tmpfile.name, width=Inches(6))
            doc.add_paragraph('Grafico de Analisis')
    if not df_data.empty:
        t = doc.add_table(rows=1, cols=len(df_data.columns))
        t.style = 'Table Grid'
        hdr_cells = t.rows[0].cells
        for i, col_name in enumerate(df_data.columns): hdr_cells[i].text = str(col_name)
        for _, row in df_data.iterrows():
            row_cells = t.add_row().cells
            for i, item in enumerate(row):
                texto_celda = str(item)
                if isinstance(item, float): texto_celda = f"{item:.2f}"
                row_cells[i].text = texto_celda
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

def generar_pdf_con_graficos(df_data, titulo_reporte, incluir_grafico=False, tipo_grafico="barras"):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, clean_text(titulo_reporte), 0, 1, 'L')
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 8)
    if 'Mes' in df_data.columns: 
        cols = ['Mes', 'Litros', 'Prom. Real', 'Prom. Ideal', 'Estado']
        w = [30, 30, 30, 30, 40]
    else: 
        cols = ['Codigo', 'Nombre', 'Fecha', 'Litros', 'Comb.']
        w = [25, 55, 25, 25, 30]
    for i, col in enumerate(cols): pdf.cell(w[i], 10, clean_text(col), 1, 0, 'C')
    pdf.ln()
    pdf.set_font('Arial', '', 8)
    for _, row in df_data.iterrows():
        if 'Mes' in df_data.columns:
            pdf.cell(w[0], 10, clean_text(row['Mes']), 1)
            pdf.cell(w[1], 10, str(row['Litros']), 1)
            pdf.cell(w[2], 10, str(row['Promedio Real']), 1)
            pdf.cell(w[3], 10, str(row['Promedio Ideal']), 1)
            pdf.cell(w[4], 10, clean_text(row['Estado']), 1)
        else:
            pdf.cell(w[0], 10, clean_text(row.get('codigo_maquina','')), 1)
            pdf.cell(w[1], 10, clean_text(row.get('nombre_maquina',''))[:25], 1)
            pdf.cell(w[2], 10, clean_text(row.get('fecha','')), 1)
            try: lts = f"{float(row['litros']):.1f}"
            except: lts = "0.0"
            pdf.cell(w[3], 10, lts, 1)
            pdf.cell(w[4], 10, clean_text(row.get('tipo_combustible','N/A'))[:15], 1)
        pdf.ln()
    if incluir_grafico:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Analisis Grafico", 0, 1, 'L')
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        if tipo_grafico == "anual":
            ax.plot(df_data['Mes'], df_data['Promedio Real'], marker='o', label='Real', color='#2E86C1', linewidth=2)
            ax.plot(df_data['Mes'], df_data['Promedio Ideal'], linestyle='--', label='Ideal', color='#28B463', linewidth=2)
            ax.set_title("Evolucion Anual de Rendimiento")
            ax.set_ylabel("Promedio")
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            ax.bar(df_data['nombre_maquina'], df_data['litros'], color='#E67E22')
            ax.set_title("Consumo Total por Maquina")
            plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            fig.savefig(tmpfile.name, format='png')
            pdf.image(tmpfile.name, x=10, y=40, w=190)
        plt.close(fig) 
    return pdf.output(dest='S').encode('latin-1', 'replace')

def estilo_tabla(df):
    # Tabla Beige Claro con bordes Visibles
    return df.style.set_properties(**{
        'background-color': '#fffcf0', 
        'color': 'black',
        'border': '1px solid #b0a890'
    }).set_table_styles([{
        'selector': 'th',
        'props': [('background-color', '#e6e2d3'), ('color', 'black'), ('font-weight', 'bold'), ('border', '1px solid #b0a890')]
    }])

# --- 3. INTERFAZ ---
st.title("⛽ Ekos Forestal / Control de combustible")
st.markdown("""
<p style='font-size: 18px; color: #0b0f19; margin-top: -20px;'>
    Desenvolvido por Excelencia Consultora en Paraguay 🇵🇾 
    <span style='font-size: 14px; font-style: italic; color: #0b0f19; margin-left: 10px;'>
        creado por Thaylan Cesca
    </span>
</p>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["👋 Registro Personal", "🔐 Auditoría & Stock", "📊 Informe Grafico", "🔍 Confirmación de Datos", "🚜 Máquina por Máquina"])

with tab1:
    st.subheader("🔑 Acceso de Encargado")
    c_auth1, c_auth2 = st.columns(2)
    with c_auth1: encargado_sel = st.selectbox("Encargado:", options=list(ENCARGADOS_DATA.keys()))
    with c_auth2: pwd_input = st.text_input("Contraseña:", type="password")

    if pwd_input == ENCARGADOS_DATA[encargado_sel]["pwd"]:
        operacion = st.radio("Operación:", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
        if encargado_sel == "Auditoria":
            op_barril, op_origen = BARRILES_LISTA, BARRILES_LISTA + ["Surtidor Petrobras", "Surtidor Shell"]
        else:
            mi_barril = ENCARGADOS_DATA[encargado_sel]["barril"]
            op_barril, op_origen = [mi_barril], [mi_barril, "Surtidor Petrobras", "Surtidor Shell"]

        c_f1, c_f2 = st.columns(2)
        with c_f1:
            if "Máquina" in operacion:
                sel_m = st.selectbox("Máquina:", options=[f"{k} - {v['nombre']}" for k, v in FLOTA.items()])
                cod_f, nom_f, unidad = sel_m.split(" - ")[0], FLOTA[sel_m.split(" - ")[0]]['nombre'], FLOTA[sel_m.split(" - ")[0]]['unidad']
                origen = st.selectbox("Origen:", op_origen)
            else:
                cod_f = st.selectbox("Barril:", options=op_barril)
                nom_f, unidad, origen = cod_f, "Litros", st.selectbox("Surtidor:", ["Surtidor Petrobras", "Surtidor Shell"])
        
        with c_f2: tipo_comb = st.selectbox("Combustible:", TIPOS_COMBUSTIBLE)

        with st.form("form_final_ekos", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                chofer, fecha, act = st.text_input("Chofer"), st.date_input("Fecha", date.today()), st.text_input("Actividad")
            with col2:
                lts = st.number_input("Litros", min_value=0.0, step=0.1)
                lect = st.number_input(f"Lectura ({unidad})", min_value=0.0) if "Máquina" in operacion else 0.0
            
            if st.form_submit_button("✅ GUARDAR REGISTRO"):
                if not chofer or not act:
                    st.warning("⚠️ Completa los campos.")
                else:
                    error_lectura = False
                    media_calc = 0.0
                    if "Máquina" in operacion and lect > 0:
                        try:
                            df_hist = pd.read_csv(SHEET_URL)
                            df_hist.columns = df_hist.columns.str.strip().str.lower()
                            cols_num = ['lectura_actual', 'litros', 'media']
                            for c in cols_num:
                                if c in df_hist.columns: df_hist[c] = pd.to_numeric(df_hist[c], errors='coerce').fillna(0)
                            hist_maq = df_hist[df_hist['codigo_maquina'] == cod_f]
                            if not hist_maq.empty:
                                ult_lectura = hist_maq['lectura_actual'].max()
                                if lect < ult_lectura:
                                    st.error(f"⛔ ERROR: La lectura ({lect}) es MENOR a la anterior ({ult_lectura}).")
                                    error_lectura = True
                                else:
                                    recorrido = lect - ult_lectura
                                    if lts > 0: media_calc = recorrido / lts
                        except: pass 
                    if not error_lectura:
                        payload = {"fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f, "nombre_maquina": nom_f, "origen": origen, "chofer": chofer, "responsable_cargo": encargado_sel, "actividad": act, "lectura_actual": lect, "litros": lts, "tipo_combustible": tipo_comb, "media": media_calc}
                        try:
                            r = requests.post(SCRIPT_URL, json=payload)
                            if r.status_code == 200: st.balloons(); st.success(f"¡Guardado! Promedio calculado: {media_calc:.2f}")
                            else: st.error("Error en permisos.")
                        except: st.error("Error de conexión.")
    elif pwd_input: st.error("❌ Contraseña incorrecta.")

with tab2:
    if st.text_input("PIN Maestro Auditoría", type="password", key="p_aud") == ACCESS_CODE_MAESTRO:
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                if len(df.columns) > 0 and "html" in str(df.columns[0]).lower(): st.error("🚨 ERROR DE PERMISOS.")
                else:
                    df.columns = df.columns.str.strip().str.lower()
                    cols_num = ['litros', 'media', 'lectura_actual']
                    for c in cols_num:
                        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                    if 'fecha' in df.columns:
                        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
                        
                        st.subheader("📦 Verificación de Stock (Total Histórico)")
                        tipo_audit = st.radio("¿Qué combustible desea verificar?", TIPOS_COMBUSTIBLE, horizontal=True)
                        cb = st.columns(4)
                        for i, b in enumerate(BARRILES_LISTA):
                            ent = df[(df['codigo_maquina'] == b) & (df['tipo_combustible'] == tipo_audit)]['litros'].sum()
                            sal = df[(df['origen'] == b) & (df['tipo_combustible'] == tipo_audit)]['litros'].sum()
                            cb[i].metric(b, f"{ent - sal:.1f} L", f"Entradas: {ent:.0f}")

                        st.markdown("---")
                        st.subheader("📋 Historial de Movimientos")
                        c_date1, c_date2 = st.columns(2)
                        with c_date1: f_ini = st.date_input("Fecha Inicio:", date.today() - timedelta(days=30))
                        with c_date2: f_fin = st.date_input("Fecha Fin:", date.today())
                        
                        mask = (df['fecha'].dt.date >= f_ini) & (df['fecha'].dt.date <= f_fin)
                        df_filtrado = df.loc[mask]
                        cols_finales = [c for c in ['fecha', 'nombre_maquina', 'origen', 'litros', 'tipo_combustible', 'responsable_cargo', 'media', 'lectura_actual'] if c in df.columns]
                        
                        st.dataframe(estilo_tabla(df_filtrado[cols_finales].sort_values(by='fecha', ascending=False)), use_container_width=True)
                        
                        st.markdown("### 📥 Descargas")
                        excel_data = generar_excel(df_filtrado[cols_finales])
                        st.download_button("Descargar Tabla en Excel (.xlsx)", data=excel_data, file_name="Historial_Ekos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    else: st.warning("⚠️ Faltan encabezados.")
            else: st.info("Planilla vacía.")
        except Exception as e: st.error(f"Error técnico: {e}")

with tab3:
    if st.text_input("PIN Gerencia", type="password", key="p_ger") == ACCESS_CODE_MAESTRO:
        try:
            df_graph = pd.read_csv(SHEET_URL)
            df_graph.columns = df_graph.columns.str.strip().str.lower()
            cols_num = ['litros', 'media', 'lectura_actual']
            for c in cols_num:
                if c in df_graph.columns: df_graph[c] = pd.to_numeric(df_graph[c], errors='coerce').fillna(0)
            
            if not df_graph.empty and 'fecha' in df_graph.columns:
                df_graph['fecha'] = pd.to_datetime(df_graph['fecha'], errors='coerce')
                st.subheader("📊 Análisis de Rendimiento (Con Margen de Tolerancia)")
                c_g1, c_g2 = st.columns(2)
                with c_g1: g_ini = st.date_input("Desde:", date.today() - timedelta(days=30), key="g_ini_r")
                with c_g2: g_fin = st.date_input("Hasta:", date.today(), key="g_fin_r")
                mask_g = (df_graph['fecha'].dt.date >= g_ini) & (df_graph['fecha'].dt.date <= g_fin)
                df_g = df_graph.loc[mask_g]
                df_maq = df_g[df_g['tipo_operacion'].str.contains("Máquina", na=False)]
                
                if not df_maq.empty:
                    resumen_data = []
                    maquinas_activas = df_maq['codigo_maquina'].unique()
                    for cod in maquinas_activas:
                        if cod in FLOTA:
                            datos_maq = df_maq[df_maq['codigo_maquina'] == cod]
                            total_litros = datos_maq['litros'].sum()
                            datos_maq['recorrido_est'] = datos_maq['media'] * datos_maq['litros']
                            total_recorrido_media = datos_maq['recorrido_est'].sum()
                            lectura_max = datos_maq['lectura_actual'].max()
                            lectura_min = datos_maq['lectura_actual'].min()
                            total_recorrido_lecturas = lectura_max - lectura_min
                            
                            if total_recorrido_media > 1: total_recorrido = total_recorrido_media
                            elif total_recorrido_lecturas > 0: total_recorrido = total_recorrido_lecturas
                            else: total_recorrido = 0
                            
                            unidad = FLOTA[cod]['unidad']
                            ideal = FLOTA[cod].get('ideal', 0.0)
                            promedio_real = 0.0
                            metric_label = "Unid/L"
                            
                            if total_litros > 0:
                                if unidad == 'KM': promedio_real = total_recorrido / total_litros; metric_label = "KM/L"
                                else: 
                                    if total_recorrido > 0: promedio_real = total_litros / total_recorrido; metric_label = "L/Hora"
                            
                            estado = "N/A"
                            if ideal > 0:
                                margen = ideal * MARGEN_TOLERANCIA
                                min_ok, max_ok = ideal - margen, ideal + margen
                                estado = "✅ Normal" if min_ok <= promedio_real <= max_ok else "⚠️ Fuera de Rango"

                            resumen_data.append({
                                "Máquina": FLOTA[cod]['nombre'],
                                "Unidad": unidad,
                                "Litros Usados": round(total_litros, 2),
                                f"Promedio Real ({metric_label})": round(promedio_real, 2),
                                f"Promedio Ideal": ideal,
                                "Estado": estado
                            })
                    
                    df_res = pd.DataFrame(resumen_data)
                    st.dataframe(estilo_tabla(df_res), use_container_width=True)
                    st.caption(f"Nota: Margen de tolerancia +/- {int(MARGEN_TOLERANCIA*100)}%")
                    
                    st.markdown("---")
                    st.subheader("Gráficos de Consumo")
                    
                    fig_cons, ax_cons = plt.subplots(figsize=(10, 4))
                    fig_cons.patch.set_facecolor('#fffcf0')
                    ax_cons.set_facecolor('#fffcf0')
                    data_cons = df_maq.groupby('nombre_maquina')['litros'].sum()
                    bars = ax_cons.bar(data_cons.index, data_cons.values, color='#E67E22')
                    ax_cons.set_title("Litros Totales por Máquina", color='#0b0f19')
                    ax_cons.tick_params(axis='x', rotation=45, colors='#0b0f19')
                    ax_cons.tick_params(axis='y', colors='#0b0f19')
                    for bar in bars:
                        height = bar.get_height()
                        ax_cons.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
                    st.pyplot(fig_cons)
                    
                    c_down1, c_down2 = st.columns(2)
                    with c_down1:
                        pdf_b = generar_pdf_con_graficos(df_maq, "Informe General de Consumo", incluir_grafico=True, tipo_grafico="barras")
                        st.download_button("📄 Descargar Reporte PDF", pdf_b, "Informe_Grafico.pdf")
                    with c_down2:
                        word_b = generar_word(df_res, "Reporte Rendimiento Ekos")
                        st.download_button("📝 Descargar Reporte Word (.docx)", word_b, "Informe_Rendimiento.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

                else: st.info("No hay movimientos.")
            else: st.warning("Sin datos.")
        except Exception as e: st.error(f"Error: {e}")

with tab4:
    if st.text_input("PIN Conciliación", type="password", key="p_con") == ACCESS_CODE_MAESTRO:
        st.subheader("🔍 Lado a Lado: Ekos vs Petrobras")
        archivo_p = st.file_uploader("Subir Archivo Petrobras (Excel o CSV)", type=["xlsx", "csv"])
        if archivo_p:
            try:
                if archivo_p.name.endswith('.csv'):
                    df_p = pd.read_csv(archivo_p, header=0, usecols=[5, 12, 14, 15], names=["Fecha", "Responsable", "Comb_Original", "Litros"])
                else:
                    df_p = pd.read_excel(archivo_p, usecols=[5, 12, 14, 15], names=["Fecha", "Responsable", "Comb_Original", "Litros"])

                df_p['Comb_Ekos'] = df_p['Comb_Original'].map(MAPA_COMBUSTIBLE).fillna("Otros")
                st.dataframe(estilo_tabla(df_p.head()), use_container_width=True)
                if st.button("🚀 SINCRONIZAR"):
                    for _, r in df_p.iterrows():
                        p = {"fecha": str(r['Fecha']), "tipo_operacion": "FACTURA PETROBRAS", "codigo_maquina": "PETRO-F", "nombre_maquina": "Factura", "origen": "Surtidor", "chofer": "N/A", "responsable_cargo": str(r['Responsable']), "actividad": "Conciliación", "lectura_actual": 0, "litros": float(r['Litros']), "tipo_combustible": r['Comb_Ekos'], "fuente_dato": "PETROBRAS_OFFICIAL"}
                        requests.post(SCRIPT_URL, json=p)
                    st.success("✅ Sincronizado.")
            except Exception as e: st.error(f"Error: {e}")

with tab5:
    if st.text_input("PIN Analítico", type="password", key="p_maq") == ACCESS_CODE_MAESTRO:
        st.subheader("🚜 Análisis Anual: Máquina por Máquina")
        try:
            df_m = pd.read_csv(SHEET_URL)
            df_m.columns = df_m.columns.str.strip().str.lower()
            for c in ['litros', 'media', 'lectura_actual']:
                if c in df_m.columns: df_m[c] = pd.to_numeric(df_m[c], errors='coerce').fillna(0)
            if 'fecha' in df_m.columns:
                df_m['fecha'] = pd.to_datetime(df_m['fecha'], errors='coerce')

                col_sel1, col_sel2 = st.columns(2)
                with col_sel1:
                    lista_maquinas = [f"{k} - {v['nombre']}" for k,v in FLOTA.items()]
                    maq_elegida_str = st.selectbox("Seleccione Máquina:", lista_maquinas)
                    cod_maq = maq_elegida_str.split(" - ")[0]
                with col_sel2:
                    anio_elegido = st.selectbox("Seleccione Año:", [2024, 2025, 2026], index=1)
                
                df_maq_anual = df_m[(df_m['codigo_maquina'] == cod_maq) & (df_m['fecha'].dt.year == anio_elegido)]
                
                if not df_maq_anual.empty:
                    datos_mensuales = []
                    meses_nombre = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                    ideal = FLOTA[cod_maq].get('ideal', 0.0)
                    unidad = FLOTA[cod_maq]['unidad']
                    
                    for mes_idx in range(1, 13):
                        df_mes = df_maq_anual[df_maq_anual['fecha'].dt.month == mes_idx]
                        litros_mes = df_mes['litros'].sum()
                        
                        prom_real_mes = 0.0
                        if litros_mes > 0:
                            df_mes['recorrido_est'] = df_mes['media'] * df_mes['litros']
                            rec_media = df_mes['recorrido_est'].sum()
                            rec_lectura = df_mes['lectura_actual'].max() - df_mes['lectura_actual'].min()
                            total_rec = max(rec_media, rec_lectura) if rec_media > 1 or rec_lectura > 0 else 0
                            
                            if unidad == 'KM': prom_real_mes = total_rec / litros_mes
                            else: 
                                if total_rec > 0: prom_real_mes = litros_mes / total_rec

                        estado = "-"
                        if litros_mes > 0 and ideal > 0:
                             min_ok, max_ok = ideal * (1-MARGEN_TOLERANCIA), ideal * (1+MARGEN_TOLERANCIA)
                             estado = "✅" if min_ok <= prom_real_mes <= max_ok else "⚠️"

                        datos_mensuales.append({
                            "Mes": meses_nombre[mes_idx-1],
                            "Litros": round(litros_mes, 2),
                            "Promedio Real": round(prom_real_mes, 2),
                            "Promedio Ideal": ideal,
                            "Estado": estado
                        })
                    
                    df_resumen_mensual = pd.DataFrame(datos_mensuales)
                    
                    st.subheader(f"📊 Panel de Control: {FLOTA[cod_maq]['nombre']}")
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        st.markdown("**Rendimiento Mensual**")
                        fig_line, ax_line = plt.subplots(figsize=(6, 4))
                        fig_line.patch.set_facecolor('#fffcf0')
                        ax_line.set_facecolor('#fffcf0')
                        ax_line.plot(df_resumen_mensual['Mes'], df_resumen_mensual['Promedio Real'], marker='o', label='Real', color='#2E86C1', linewidth=2)
                        ax_line.plot(df_resumen_mensual['Mes'], df_resumen_mensual['Promedio Ideal'], linestyle='--', label='Ideal', color='#28B463', linewidth=2)
                        ax_line.set_ylabel("Rendimiento")
                        ax_line.legend()
                        ax_line.grid(True, alpha=0.3)
                        plt.setp(ax_line.get_xticklabels(), rotation=45, ha="right")
                        for i, txt in enumerate(df_resumen_mensual['Promedio Real']):
                            if txt > 0: ax_line.annotate(f"{txt}", (i, txt), xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8)
                        st.pyplot(fig_line)

                    with col_chart2:
                        st.markdown("**Consumo (Litros)**")
                        fig_bar, ax_bar = plt.subplots(figsize=(6, 4))
                        fig_bar.patch.set_facecolor('#fffcf0')
                        ax_bar.set_facecolor('#fffcf0')
                        bars = ax_bar.bar(df_resumen_mensual['Mes'], df_resumen_mensual['Litros'], color='#E67E22', alpha=0.8)
                        ax_bar.set_ylabel("Litros")
                        ax_bar.grid(axis='y', alpha=0.3)
                        plt.setp(ax_bar.get_xticklabels(), rotation=45, ha="right")
                        for bar in bars:
                            height = bar.get_height()
                            if height > 0: ax_bar.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
                        st.pyplot(fig_bar)

                    st.markdown("#### Detalle Numérico")
                    st.dataframe(estilo_tabla(df_resumen_mensual), use_container_width=True)

                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        pdf_anual = generar_pdf_con_graficos(df_resumen_mensual, f"Reporte Anual {anio_elegido}: {FLOTA[cod_maq]['nombre']}", incluir_grafico=True, tipo_grafico="anual")
                        st.download_button("📄 Descargar PDF Anual", pdf_anual, f"Reporte_{cod_maq}_{anio_elegido}.pdf")
                    with col_d2:
                        word_anual = generar_word(df_resumen_mensual, f"Reporte Anual {anio_elegido}: {FLOTA[cod_maq]['nombre']}", grafico_fig=fig_line)
                        st.download_button("📝 Descargar Word Anual", word_anual, f"Reporte_{cod_maq}_{anio_elegido}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    
                else:
                    st.info(f"No hay datos registrados para la máquina {cod_maq} en el año {anio_elegido}.")

        except Exception as e: st.error(f"Error al procesar: {e}")
