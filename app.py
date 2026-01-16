import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import io
import tempfile
import time
import base64
from datetime import date, datetime, timedelta
from fpdf import FPDF
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

# URL DEL SCRIPT DE GOOGLE
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwnPU3LdaHqrNO4bTsiBMKmm06ZSm3dUbxb5OBBnHBQOHRSuxcGv_MK4jWNHsrAn3M/exec"
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

ACCESS_CODE_MAESTRO = "1645"
PASS_EXCELENCIA = "excelespasado"
TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]
MARGEN_TOLERANCIA = 0.20

ENCARGADOS_DATA = {
    "Juan Britez": {"pwd": "jbritez45", "barril": "Barril Juan"},
    "Diego Bordon": {"pwd": "Bng2121", "barril": "Barril Diego"},
    "Jonatan Vargas": {"pwd": "jv2026", "barril": "Barril Jonatan"},
    "Cesar Cabañas": {"pwd": "cab14", "barril": "Barril Cesar"},
    "Natalia Santana": {"pwd": "Santana2057", "barril": "Acceso Total"},
    "Auditoria": {"pwd": "1645", "barril": "Acceso Total"}
}

# --- LISTADO DE TARJETAS POR ENCARGADO ---
TARJETAS_DATA = {
    "Diego Bordon": [
        "MULTI Diego - 70026504990100126"
    ],
    "Cesar Cabañas": [
        "MULTI CESAR - 70026504990100140",
        "M-02 - 70026504990100179"
    ],
    "Juan Britez": [
        "MULTI JUAN - 70026504990100112",
        "M-13 - 70026504990100024"
    ],
    "Jonatan Vargas": [
        "M-03 - 70026504990100189",
        "S-03 - 70026504990100056",
        "S-05 - 70026504990100063",
        "S-06 - 70026504990100078",
        "S-07 - 70026504990100164",
        "S-08 - 70026504990100088",
        "MULTI JONATAN - 70026504990100134"
    ]
}

BARRILES_LISTA = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

# --- FLOTA ACTUALIZADA ---
FLOTA = {
    "HV-01": {"nombre": "Caterpilar 320D", "unidad": "Horas", "ideal": 18.0}, 
    "JD-01": {"nombre": "John Deere", "unidad": "Horas", "ideal": 15.0},
    "JD-02": {"nombre": "John Deere 6170", "unidad": "Horas", "ideal": 16.0},
    "JD-03": {"nombre": "John Deere 6110", "unidad": "Horas", "ideal": 10.0},
    "JD-04": {"nombre": "John Deere 5090", "unidad": "Horas", "ideal": 8.0},
    "M-01": {"nombre": "Nissan Frontier (Natalia)", "unidad": "KM", "ideal": 9.0},
    "M-02": {"nombre": "Chevrolet - S10", "unidad": "KM", "ideal": 8.0},
    "M-03": {"nombre": "GM S-10 (M-03)", "unidad": "KM", "ideal": 8.5},
    "M-11": {"nombre": "N. Frontier", "unidad": "KM", "ideal": 9.0},
    "M-17": {"nombre": "GM S-10", "unidad": "KM", "ideal": 10.0},
    "M13": {"nombre": "Nisan Frontier (M13)", "unidad": "Horas", "ideal": 5.0},
    "MC-06": {"nombre": "MB Canter", "unidad": "KM", "ideal": 6.0},
    "MF-02": {"nombre": "Massey", "unidad": "Horas", "ideal": 9.0},
    "MICHIGAN": {"nombre": "Pala Michigan", "unidad": "Horas", "ideal": 14.0},
    "RA-01": {"nombre": "Ranger Alquilada 0-01", "unidad": "KM", "ideal": 9.0},
    "O-01": {"nombre": "Otros", "unidad": "Horas", "ideal": 0.0},
    "S-03": {"nombre": "Scania 113H", "unidad": "KM", "ideal": 2.3},
    "S-05": {"nombre": "Scania Azul", "unidad": "KM", "ideal": 2.4},
    "S-06": {"nombre": "Scania P112H", "unidad": "Horas", "ideal": 0.0},
    "S-07": {"nombre": "Scania R380", "unidad": "Horas", "ideal": 0.0},
    "S-08": {"nombre": "Scania Rojo", "unidad": "KM", "ideal": 2.2},
    "TF01": {"nombre": "Ford", "unidad": "Horas", "ideal": 0.0},
    "TM-01": {"nombre": "Pala Michigan", "unidad": "Horas", "ideal": 14.0},
    "V-02": {"nombre": "Valmet 785", "unidad": "Horas", "ideal": 7.0},
    "V-07": {"nombre": "Valmet 1580", "unidad": "Horas", "ideal": 11.0},
    "V-11": {"nombre": "Valmet 8080", "unidad": "Horas", "ideal": 9.5},
    "V-12": {"nombre": "Valtra 180", "unidad": "Horas", "ideal": 12.0}
}

# --- FUNCIONES DE SOPORTE ---
def clean_text(text): return str(text).encode('latin-1', 'replace').decode('latin-1')

def generar_excel(df, sheet_name='Datos'):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def generar_pdf_con_graficos(df, titulo, inc_graf=False, tipo="barras"):
    pdf = FPDF(); pdf.add_page(); pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, clean_text(titulo), 0, 1, 'L'); pdf.ln(5)
    pdf.set_font('Arial', '', 8)
    for i, col in enumerate(df.columns): pdf.cell(30, 10, clean_text(col), 1)
    pdf.ln()
    for _, row in df.iterrows():
        for col in df.columns: pdf.cell(30, 10, clean_text(str(row[col])), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'replace')

def generar_word(df, titulo):
    doc = Document(); doc.add_heading(titulo, 0)
    if not df.empty:
        t = doc.add_table(rows=1, cols=len(df.columns)); t.style = 'Table Grid'
        for i, col in enumerate(df.columns): t.rows[0].cells[i].text = str(col)
        for _, row in df.iterrows():
            row_cells = t.add_row().cells
            for i, item in enumerate(row): row_cells[i].text = str(item)
    b = io.BytesIO(); doc.save(b); return b.getvalue()

def estilo_tabla(df):
    return df.style.set_properties(**{'background-color': '#fffcf0', 'color': 'black', 'border': '1px solid #b0a890'})

# --- GENERADOR DE INFORME EXCELENCIA (WORD) ---
def generar_informe_corporativo(encargado, df_filtrado, fecha_ini, fecha_fin):
    doc = Document()
    style = doc.styles['Normal']; font = style.font; font.name = 'Calibri'; font.size = Pt(11)
    try: doc.add_picture('logo.png', width=Inches(1.5)) 
    except: pass

    heading = doc.add_heading(f'INFORME DE CONTROL DE COMBUSTIBLE', 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph(f"Responsable Auditado: {encargado}")
    doc.add_paragraph(f"Período de Análisis: {fecha_ini.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}")
    doc.add_paragraph(f"Fecha de Emisión: {date.today().strftime('%d/%m/%Y')}")
    doc.add_paragraph("-" * 70)

    doc.add_heading('1. Objetivo del Reporte', level=1)
    p = doc.add_paragraph("El presente documento tiene como finalidad certificar la correspondencia entre los registros de ingreso y salida de combustible, validando la integridad de los datos reportados por el proveedor frente a la gestión operativa interna. Asimismo, se busca identificar desviaciones en el rendimiento de la flota que puedan impactar en la eficiencia operativa de Ekos Forestal S.A.")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    doc.add_heading('2. Análisis de Rendimiento y Hallazgos', level=1)
    maquinas_alerta = []
    
    if 'tipo_operacion' in df_filtrado.columns:
        df_maq = df_filtrado[df_filtrado['tipo_operacion'].astype(str).str.contains("Máquina", na=False)]
        unique_maqs = df_maq['codigo_maquina'].unique()
        
        for cod in unique_maqs:
            dm = df_maq[df_maq['codigo_maquina'] == cod]
            l_total = dm['litros'].sum()
            rec = dm['lectura_actual'].max() - dm['lectura_actual'].min()
            
            if len(dm) > 1:
                dm_sorted = dm.sort_values('lectura_actual')
                l_ajustados = dm_sorted.iloc[1:]['litros'].sum()
            else: l_ajustados = l_total

            rend = 0
            if cod in FLOTA:
                ideal = FLOTA[cod]['ideal']
                unidad = FLOTA[cod]['unidad']
                
                if unidad == 'KM':
                    rend = rec / l_ajustados if l_ajustados > 0 else 0
                    if rend < ideal * (1 - MARGEN_TOLERANCIA): maquinas_alerta.append((cod, rend, ideal, unidad, "bajo"))
                else: 
                    rend = l_ajustados / rec if rec > 0 else 0
                    if rend > ideal * (1 + MARGEN_TOLERANCIA): maquinas_alerta.append((cod, rend, ideal, unidad, "alto"))

    if maquinas_alerta:
        doc.add_paragraph("Durante la revisión detallada de la flota asignada, se han detectado las siguientes oportunidades de mejora en el consumo de combustible:")
        for maq, real, ideal, un, tipo in maquinas_alerta:
            diff_pct = abs((real - ideal) / ideal) * 100
            if un == 'KM': txt = f"• La unidad {maq} presentó un rendimiento de {real:.2f} Km/L, situándose por debajo del estándar ideal de {ideal} Km/L. Esto representa una desviación del {diff_pct:.1f}%."
            else: txt = f"• El equipo {maq} registró un consumo horario de {real:.2f} L/H, excediendo el parámetro esperado de {ideal} L/H. Esta desviación del {diff_pct:.1f}%."
            p = doc.add_paragraph(txt); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    else:
        doc.add_paragraph("Tras el análisis de los registros del período, no se observaron desviaciones significativas en el rendimiento de las máquinas.")

    doc.add_heading('3. Detalle de Movimientos Consolidados', level=1)
    table = doc.add_table(rows=1, cols=3); table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Código Máquina'; hdr_cells[1].text = 'Litros Totales'; hdr_cells[2].text = 'Recorrido Total'
    
    if 'tipo_operacion' in df_filtrado.columns:
        resumen = df_maq.groupby('codigo_maquina').agg({'litros': 'sum'}).reset_index()
        for index, row in resumen.iterrows():
            row_cells = table.add_row().cells
            row_cells[0].text = str(row['codigo_maquina']); row_cells[1].text = f"{row['litros']:.1f}"
            dmm = df_maq[df_maq['codigo_maquina'] == row['codigo_maquina']]
            recc = dmm['lectura_actual'].max() - dmm['lectura_actual'].min()
            row_cells[2].text = f"{recc:.1f}"

    doc.add_heading('4. Conclusiones y Recomendaciones', level=1)
    doc.add_paragraph("Se recomienda mantener un monitoreo constante sobre las unidades listadas. Es vital asegurar que todos los registros de carga incluyan la diferenciación correcta entre Nafta y Diésel.")
    doc.add_paragraph("\n")
    footer = doc.add_paragraph("Informe generado automáticamente por el sistema Ekos Control."); footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    b = io.BytesIO(); doc.save(b); return b.getvalue()

@st.dialog("📝 Confirmar Información")
def confirmar_envio(pl):
    st.markdown("### Por favor, verifica que todo esté correcto:")
    col_x, col_y = st.columns(2)
    with col_x:
        st.write(f"**Fecha:** {pl['fecha']}")
        st.write(f"**Encargado:** {pl['responsable_cargo']}")
        if "Máquina" in pl['tipo_operacion']:
            st.write(f"**Máquina:** {pl['codigo_maquina']}")
            if pl['nombre_maquina'] != pl['codigo_maquina']: st.write(f"**Nombre:** {pl['nombre_maquina']}")
            st.write(f"**Lectura:** {pl['lectura_actual']}")
        else: st.write(f"**Barril:** {pl['codigo_maquina']}")
        
        # MOSTRAR TARJETA EN LA CONFIRMACIÓN
        st.write(f"**Tarjeta:** {pl.get('tarjeta', 'N/A')}")
        
    with col_y:
        st.write(f"**Litros:** {pl['litros']}")
        st.write(f"**Combustible:** {pl['tipo_combustible']}")
        st.write(f"**Chofer:** {pl['chofer']}")
    if pl['imagen_base64']: st.success("📸 Foto Adjuntada")
    st.markdown("---")
    col_a, col_b = st.columns(2)
    if col_a.button("✅ SÍ, GUARDAR", type="primary"):
        envio_exitoso = False
        try:
            requests.post(SCRIPT_URL, json=pl)
            envio_exitoso = True
        except: st.error("Error REAL de conexión. Verifica tu internet.")
        if envio_exitoso:
            st.session_state['exito_guardado'] = True
            st.rerun()
    if col_b.button("❌ CANCELAR"): st.rerun()

# --- INTERFAZ ---
st.title("⛽ Ekos Forestal / Control de combustible")
st.markdown("""<p style='font-size: 18px; color: gray; margin-top: -20px;'>Desenvolvido por Excelencia Consultora en Paraguay 🇵🇾 <span style='font-size: 14px; font-style: italic;'>creado por Thaylan Cesca</span></p><hr>""", unsafe_allow_html=True)

if 'exito_guardado' in st.session_state and st.session_state['exito_guardado']:
    st.toast('Datos Guardados Correctamente!', icon='✅')
    st.markdown("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)
    st.session_state['exito_guardado'] = False 

tab1, tab2, tab3, tab4 = st.tabs(["👋 Registro Personal", "🔐 Auditoría", "🔍 Verificación", "🚜 Analisis Anual por Máquina"])

# --- TAB 1: REGISTRO ---
with tab1: 
    st.subheader("🔑 Acceso de Encargado")
    c_auth1, c_auth2 = st.columns(2)
    with c_auth1: encargado_sel = st.selectbox("Encargado:", list(ENCARGADOS_DATA.keys()))
    with c_auth2: pwd_input = st.text_input("Contraseña:", type="password")
    
    if pwd_input == ENCARGADOS_DATA[encargado_sel]["pwd"]:
        SURTIDORES = ["Surtidor Petrobras", "Surtidor Shell", "Surtidor Crisma", "Surtidor Puma"]
        if ENCARGADOS_DATA[encargado_sel]["barril"] == "Acceso Total": 
            op_barril = BARRILES_LISTA; op_origen = BARRILES_LISTA + SURTIDORES
        else: 
            mi_barril = ENCARGADOS_DATA[encargado_sel]["barril"]
            op_barril = [mi_barril]; op_origen = [mi_barril] + SURTIDORES

        operacion = st.radio("Operación:", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            if "Máquina" in operacion:
                lista_maquinas = [f"{k} - {v['nombre']}" for k, v in FLOTA.items()]
                lista_maquinas.append("➕ OTRO (Manual)")
                sel_m = st.selectbox("Máquina:", lista_maquinas)
                if sel_m == "➕ OTRO (Manual)":
                    st.info("Ingresa los datos del nuevo vehículo:")
                    cod_f = st.text_input("Código (Ej: M-99)").strip().upper()
                    nom_f = st.text_input("Nombre (Ej: Toyota Hilux)")
                    unidad = st.selectbox("Unidad de Medida", ["KM", "Horas"])
                    origen = st.selectbox("Origen:", op_origen)
                else:
                    cod_f, nom_f, unidad = sel_m.split(" - ")[0], FLOTA[sel_m.split(" - ")[0]]['nombre'], FLOTA[sel_m.split(" - ")[0]]['unidad']
                    origen = st.selectbox("Origen:", op_origen)
            else: 
                cod_f = st.selectbox("Barril:", op_barril)
                nom_f, unidad, origen = cod_f, "Litros", st.selectbox("Surtidor:", SURTIDORES)

        with c_f2: tipo_comb = st.selectbox("Combustible:", TIPOS_COMBUSTIBLE)
        
        # --- SELECCIÓN DE TARJETA ---
        mis_tarjetas = TARJETAS_DATA.get(encargado_sel, []) + ["💳 Otra (Manual)"]
        sel_tarjeta = st.selectbox("Tarjeta Utilizada:", mis_tarjetas)
        
        tarjeta_final = ""
        if sel_tarjeta == "💳 Otra (Manual)":
            tarjeta_final = st.text_input("Ingrese N° o Nombre de Tarjeta Manual:")
        else:
            tarjeta_final = sel_tarjeta

        with st.form("f_reg", clear_on_submit=False):
            c1, c2 = st.columns(2)
            chofer = c1.text_input("Chofer")
            fecha = c1.date_input("Fecha", date.today(), format="DD/MM/YYYY")
            act = c1.text_input("Actividad")
            lts = c2.number_input("Litros", min_value=0.0, step=0.1, value=None)
            if "Máquina" in operacion: lect = c2.number_input(f"Lectura ({unidad})", min_value=0.0, value=None)
            else: lect = 0.0
            st.markdown("---")
            foto = st.file_uploader("📸 Foto Evidencia (Opcional)", type=["jpg", "png", "jpeg"])

            if st.form_submit_button("🔎 REVISAR DATOS ANTES DE GUARDAR"):
                error_manual = False
                if "Máquina" in operacion and sel_m == "➕ OTRO (Manual)":
                    if not cod_f or not nom_f: error_manual = True
                
                if not chofer or not act or lts is None or error_manual: st.warning("⚠️ Faltan datos obligatorios.")
                elif "Máquina" in operacion and lect is None: st.warning("⚠️ Falta la Lectura.")
                elif not tarjeta_final: st.warning("⚠️ Debe seleccionar o escribir una TARJETA.")
                else:
                    lts_val = lts if lts is not None else 0.0
                    lect_val = lect if lect is not None else 0.0
                    mc = 0.0
                    try: 
                        if "Máquina" in operacion and lect_val > 0 and lts_val > 0:
                            df_h = pd.read_csv(SHEET_URL)
                            df_h.columns = df_h.columns.str.strip().str.lower()
                            if 'lectura_actual' in df_h.columns and 'codigo_maquina' in df_h.columns:
                                df_h['lectura_actual'] = df_h['lectura_actual'].astype(str).str.replace(',', '.')
                                df_h['lectura_actual'] = pd.to_numeric(df_h['lectura_actual'], errors='coerce').fillna(0)
                                lect_anterior = df_h[df_h['codigo_maquina'] == cod_f]['lectura_actual'].max()
                                if lect_anterior > 0 and lect_val > lect_anterior:
                                    recorrido = lect_val - lect_anterior
                                    if unidad == 'KM': mc = recorrido / lts_val
                                    else: mc = lts_val / recorrido
                    except Exception as e: print(f"Error: {e}")

                    img_str, img_name, img_mime = "", "", ""
                    if foto is not None:
                        try:
                            img_bytes = foto.read()
                            img_str = base64.b64encode(img_bytes).decode('utf-8')
                            img_name = f"EVIDENCIA_{fecha}_{encargado_sel}.jpg"
                            img_mime = foto.type
                        except: pass
                    pl = {"fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f, "nombre_maquina": nom_f, 
                        "origen": origen, "chofer": chofer, "responsable_cargo": encargado_sel, "actividad": act, 
                        "lectura_actual": lect_val, "litros": lts_val, "tipo_combustible": tipo_comb, "media": mc,
                        "tarjeta": tarjeta_final,
                        "estado_conciliacion": "N/A", "fuente_dato": "APP_MANUAL", "imagen_base64": img_str, "nombre_archivo": img_name, "mime_type": img_mime}
                    confirmar_envio(pl)

# --- TAB 2: AUDITORÍA ---
with tab2:
    st.subheader("🔐 Acceso Restringido")
    c_login1, c_login2 = st.columns(2)
    with c_login1: usuario_auditoria = st.selectbox("Usuario:", ["Auditoria", "Natalia Santana"])
    with c_login2: pass_auditoria = st.text_input("Contraseña:", type="password", key="pass_auditoria_tab2")
    
    credenciales_validas = {"Auditoria": "1645", "Natalia Santana": "Santana2057"}
    
    if pass_auditoria == credenciales_validas.get(usuario_auditoria):
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                df.columns = df.columns.str.strip().str.lower()
                for c in ['litros', 'media', 'lectura_actual']:
                    if c in df.columns: 
                        df[c] = df[c].astype(str).str.replace(',', '.')
                        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
                df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', dayfirst=True)
                
                st.subheader("📦 Stock Actual")
                ta = st.radio("Combustible:", TIPOS_COMBUSTIBLE, horizontal=True)
                cols = st.columns(4)
                for i, b in enumerate(BARRILES_LISTA):
                    ent = df[(df['codigo_maquina'] == b) & (df['tipo_combustible'] == ta)]['litros'].sum()
                    sal = df[(df['origen'] == b) & (df['tipo_combustible'] == ta)]['litros'].sum()
                    cols[i].metric(label=f"🛢️ {b}", value=f"{ent - sal:.1f} L")
                
                st.markdown("---"); st.subheader("📅 Historial")
                c1, c2, c3 = st.columns(3)
                d1 = c1.date_input("Desde", date.today()-timedelta(30), format="DD/MM/YYYY")
                d2 = c2.date_input("Hasta", date.today(), format="DD/MM/YYYY")
                enc_filter = c3.selectbox("Filtrar Encargado", ["Todos"] + list(ENCARGADOS_DATA.keys()))
                
                mask = (df['fecha'].dt.date >= d1) & (df['fecha'].dt.date <= d2)
                if enc_filter != "Todos":
                    if 'responsable_cargo' in df.columns: mask = mask & (df['responsable_cargo'] == enc_filter)
                dff = df[mask]
                
                if not dff.empty:
                    st.subheader("📋 Detalle")
                    
                    # --- AQUI SE MUESTRA LA TARJETA ---
                    cols_ver = ['fecha','nombre_maquina','origen','litros','tipo_combustible','tarjeta','responsable_cargo']
                    cols_exist = [c for c in cols_ver if c in dff.columns]
                    st.dataframe(dff[cols_exist].sort_values(by='fecha', ascending=False).style.format({"litros": "{:.1f}"}), use_container_width=True)
                    
                    st.subheader("📊 Rendimiento General (Resumen)")
                    if 'tipo_operacion' in dff.columns:
                        df_maq = dff[dff['tipo_operacion'].astype(str).str.contains("Máquina", na=False)]
                        if not df_maq.empty:
                            res = []
                            codigos_ordenados = sorted(df_maq['codigo_maquina'].unique())
                            for cod in codigos_ordenados:
                                dm = df_maq[df_maq['codigo_maquina'] == cod]
                                l_total = dm['litros'].sum()
                                lect_max = dm['lectura_actual'].max()
                                lect_min = dm['lectura_actual'].min()
                                rec_real = lect_max - lect_min
                                
                                if len(dm) > 1:
                                    dm_sorted = dm.sort_values('lectura_actual')
                                    l_ajustados = dm_sorted.iloc[1:]['litros'].sum()
                                else: l_ajustados = l_total

                                val_kml, val_lkm, val_lh = 0.0, 0.0, 0.0
                                val_ideal = 0.0
                                if cod in FLOTA:
                                    val_ideal = FLOTA[cod]['ideal']
                                    if FLOTA[cod]['unidad'] == 'KM':
                                        if l_ajustados > 0: val_kml = rec_real / l_ajustados
                                        if rec_real > 0: val_lkm = l_ajustados / rec_real
                                    else:
                                        if rec_real > 0: val_lh = l_ajustados / rec_real 
                                else:
                                    if l_ajustados > 0: val_kml = rec_real / l_ajustados
                                    if rec_real > 0: val_lh = l_ajustados / rec_real
                                    
                                estado = "N/A"
                                if cod in FLOTA and l_total > 0 and (val_kml > 0 or val_lh > 0):
                                    ideal = FLOTA[cod]['ideal']
                                    if FLOTA[cod]['unidad'] == 'KM':
                                        if val_kml < ideal * (1 - MARGEN_TOLERANCIA): estado = "⚠️ Alto Consumo"
                                        elif val_kml > ideal * (1 + MARGEN_TOLERANCIA): estado = "✨ Muy Bueno"
                                        else: estado = "✅ Ideal"
                                    else: 
                                        if val_lh > ideal * (1 + MARGEN_TOLERANCIA): estado = "⚠️ Alto Consumo"
                                        elif val_lh < ideal * (1 - MARGEN_TOLERANCIA): estado = "✨ Muy Bueno"
                                        else: estado = "✅ Ideal"
                                res.append({"Código": cod, "Recorrido": round(rec_real, 1), "Litros": round(l_total, 1), "Km/L": round(val_kml, 2), "L/Km": round(val_lkm, 2), "L/H": round(val_lh, 2), "Ideal": val_ideal, "Estado": estado})
                            
                            df_res = pd.DataFrame(res)
                            st.dataframe(df_res.style.format({"Recorrido": "{:.1f}", "Litros": "{:.1f}", "Km/L": "{:.2f}", "L/Km": "{:.2f}", "L/H": "{:.2f}", "Ideal": "{:.1f}"}), use_container_width=True)
                            
                            st.markdown("### 📥 Descargas")
                            c1, c2, c3 = st.columns(3)
                            c1.download_button("Excel", generar_excel(dff[cols_exist]), "Historial.xlsx")
                            c2.download_button("PDF", generar_pdf_con_graficos(df_res, "Reporte"), "Reporte.pdf")
                            c3.download_button("Word", generar_word(df_res, "Reporte"), "Reporte.docx")
                    
                    st.markdown("---")
                    if usuario_auditoria == "Auditoria":
                        with st.expander("📂 Fuente de Informe Excelencia Consultora (ADMIN)"):
                            st.markdown("Generación de informes corporativos.")
                            pass_excelencia = st.text_input("Contraseña de Acceso:", type="password", key="pass_exc")
                            
                            if pass_excelencia == PASS_EXCELENCIA:
                                if enc_filter == "Todos": st.warning("⚠️ Por favor, selecciona un Encargado Específico.")
                                else:
                                    if st.button(f"📄 Generar Informe Corporativo para {enc_filter}"):
                                        docx_bytes = generar_informe_corporativo(enc_filter, dff, d1, d2)
                                        st.download_button(label="⬇️ Descargar Informe.docx", data=docx_bytes, file_name=f"Informe_Gestion_{enc_filter}_{date.today()}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                            elif pass_excelencia: st.error("Contraseña incorrecta.")
                    else: st.info("ℹ️ La sección de generación de Informes Corporativos está restringida únicamente al usuario 'Auditoria'.")
                else: st.info("Sin datos.")
        except Exception as e: st.error(e)
    elif pass_auditoria: st.error("❌ Contraseña incorrecta para el usuario seleccionado.")

# --- TAB 3: VERIFICACIÓN ---
with tab3: 
    if st.text_input("PIN Conciliación", type="password", key="p2") == ACCESS_CODE_MAESTRO:
        st.subheader("🔍 Conciliación Total")
        up = st.file_uploader("Archivo Petrobras", ["xlsx", "csv"])
        if up:
            st.info("Cargando base de datos del sistema...")
            dfe = pd.read_csv(SHEET_URL); dfe.columns = dfe.columns.str.strip().str.lower()
            if 'litros' in dfe.columns: 
                dfe['litros'] = dfe['litros'].astype(str).str.replace(',', '.')
                dfe['litros'] = pd.to_numeric(dfe['litros'], errors='coerce').fillna(0)
            dfe['fecha'] = pd.to_datetime(dfe['fecha'], errors='coerce', dayfirst=True)
            dfe['KEY'] = (dfe['fecha'].dt.strftime('%Y-%m-%d') + "_" + dfe['responsable_cargo'].astype(str).str.strip().str.upper() + "_" + dfe['litros'].astype(int).astype(str))

            dfp = pd.DataFrame()
            if up.name.endswith('.csv'): 
                try: 
                    up.seek(0); dfp = pd.read_csv(up, sep=';', header=0, engine='python')
                    if len(dfp.columns) < 2: up.seek(0); dfp = pd.read_csv(up, sep=',', header=0)
                except Exception as e: st.error(f"Error leyendo CSV: {e}")
            else: 
                try: dfp = pd.read_excel(up)
                except Exception as e: st.error(f"Error leyendo Excel: {e}")

            if not dfp.empty and len(dfp.columns) > 15:
                dfp = dfp.iloc[:, [5, 12, 14, 15]]; dfp.columns = ["Fecha", "Resp", "Comb", "Litros"]
                dfp['Fecha'] = pd.to_datetime(dfp['Fecha'], errors='coerce', dayfirst=True)
                dfp['Litros'] = dfp['Litros'].astype(str).str.replace(',', '.')
                dfp['Litros'] = pd.to_numeric(dfp['Litros'], errors='coerce').fillna(0)
                dfp['KEY'] = (dfp['Fecha'].dt.strftime('%Y-%m-%d') + "_" + dfp['Resp'].astype(str).str.strip().str.upper() + "_" + dfp['Litros'].astype(int).astype(str))

                m = pd.merge(dfp, dfe, on='KEY', how='outer', indicator=True)
                def clasificar(r):
                    if r['_merge'] == 'both': return "✅ Correcto"
                    elif r['_merge'] == 'left_only': return "⚠️ Faltante en Sistema"
                    else: return "❓ Sobrante en Sistema"
                m['Estado'] = m.apply(clasificar, axis=1)
                
                m['Fecha_F'] = m['Fecha'].combine_first(m['fecha'])
                m['Resp_F'] = m['Resp'].combine_first(m['responsable_cargo'])
                m['Comb_F'] = m['Comb'].combine_first(m['tipo_combustible'])
                m['Litros_F'] = m['Litros'].combine_first(m['litros'])
                fv = m[['Fecha_F', 'Resp_F', 'Comb_F', 'Litros_F', 'Estado']].sort_values(by='Fecha_F', ascending=False)
                
                def color(val):
                    if "Correcto" in val: return 'background-color: #d4edda; color: black'
                    elif "Faltante" in val: return 'background-color: #f8d7da; color: black'
                    else: return 'background-color: #fff3cd; color: black'
                st.dataframe(fv.style.format({"Litros_F": "{:.1f}"}).applymap(color, subset=['Estado']), use_container_width=True)
                
                st.markdown("---")
                if st.button("🚀 SINCRONIZAR REPORTE COMPLETO"):
                    bar = st.progress(0); n = len(fv); ok = 0
                    for i, r in fv.iterrows():
                        litros_envio = float(r['Litros_F']) if pd.notnull(r['Litros_F']) else 0.0
                        fecha_envio = str(r['Fecha_F']) if pd.notnull(r['Fecha_F']) else str(date.today())
                        resp_envio = str(r['Resp_F']) if pd.notnull(r['Resp_F']) else "Desconocido"
                        comb_envio = str(r['Comb_F']) if pd.notnull(r['Comb_F']) else "N/A"
                        p = {"target_sheet": "Facturas_Petrobras", "fecha": fecha_envio, "tipo_operacion": "CONCILIACION", "codigo_maquina": "PETRO-F", "nombre_maquina": "Reporte", "origen": "Petrobras", "chofer": "N/A", "responsable_cargo": resp_envio, "actividad": "Auditoria", "lectura_actual": 0, "litros": litros_envio, "tipo_combustible": comb_envio, "media": 0, "estado_conciliacion": r['Estado'], "fuente_dato": "PETROBRAS_IMPORT"}
                        try: requests.post(SCRIPT_URL, json=p); ok += 1
                        except: pass
                        time.sleep(0.05); bar.progress(min((i+1)/n, 1.0))
                    st.success(f"✅ Sincronizado: {ok} registros.")
            else: st.error("Error en formato de archivo.")

# --- TAB 4: ANÁLISIS ---
with tab4: 
    if st.text_input("PIN Analítico", type="password", key="p3") == ACCESS_CODE_MAESTRO:
        dfm = pd.read_csv(SHEET_URL); dfm.columns = dfm.columns.str.strip().str.lower()
        for c in ['litros','media','lectura_actual']: 
            if c in dfm.columns: 
                dfm[c] = dfm[c].astype(str).str.replace(',', '.')
                dfm[c] = pd.to_numeric(dfm[c], errors='coerce').fillna(0)
        dfm['fecha'] = pd.to_datetime(dfm['fecha'], errors='coerce', dayfirst=True)
        
        c1, c2 = st.columns(2)
        codigos_db = dfm['codigo_maquina'].unique().tolist()
        opciones_maquina = [f"{k} - {v['nombre']}" for k, v in FLOTA.items()]
        for c in codigos_db:
            if c not in FLOTA and isinstance(c, str): opciones_maquina.append(f"{c} - (Manual)")
        opciones_maquina.sort()
        
        maq = c1.selectbox("Máquina", opciones_maquina)
        y = c2.selectbox("Año", [2024, 2025, 2026], index=1)
        cod = maq.split(" - ")[0]
        
        dy = dfm[(dfm['codigo_maquina'] == cod) & (dfm['fecha'].dt.year == y)]
        if not dy.empty:
            res = []; mn = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
            for i in range(1, 13):
                dm = dy[dy['fecha'].dt.month == i]
                l_total = dm['litros'].sum()
                if l_total > 0:
                    rec = dm['lectura_actual'].max() - dm['lectura_actual'].min()
                    if len(dm) > 1:
                        dm_sorted = dm.sort_values('lectura_actual')
                        l_ajustados = dm_sorted.iloc[1:]['litros'].sum()
                    else: l_ajustados = l_total

                    pr = 0
                    if cod in FLOTA:
                        if FLOTA[cod]['unidad'] == 'KM': pr = rec/l_ajustados if l_ajustados > 0 else 0
                        else: pr = l_ajustados/rec if rec > 0 else 0
                    else:
                        if rec > l_ajustados: pr = rec/l_ajustados if l_ajustados > 0 else 0
                        else: pr = l_ajustados/rec if rec > 0 else 0
                else: pr = 0; l_total = 0
                
                estado = "N/A"
                if cod in FLOTA and l_total > 0 and pr > 0:
                    ideal = FLOTA[cod]['ideal']
                    if FLOTA[cod]['unidad'] == 'KM':
                        if pr < ideal * (1 - MARGEN_TOLERANCIA): estado = "⚠️ Alto Consumo"
                        elif pr > ideal * (1 + MARGEN_TOLERANCIA): estado = "✨ Muy Bueno"
                        else: estado = "✅ Ideal"
                    else:
                        if pr > ideal * (1 + MARGEN_TOLERANCIA): estado = "⚠️ Alto Consumo"
                        elif pr < ideal * (1 - MARGEN_TOLERANCIA): estado = "✨ Muy Bueno"
                        else: estado = "✅ Ideal"
                
                enc_list = dm['responsable_cargo'].dropna().unique().tolist()
                enc_str = ", ".join(enc_list) if enc_list else "-"
                res.append({"Mes": mn[i-1], "Encargados": enc_str, "Litros": round(l_total, 1), "Promedio": round(pr, 2), "Estado": estado})
            
            dr = pd.DataFrame(res)
            st.subheader(f"📊 {maq}")
            c1, c2 = st.columns(2)
            fig_line, ax_line = plt.subplots(figsize=(6, 4)); fig_line.patch.set_facecolor('white'); ax_line.set_facecolor('white')
            ax_line.plot(dr['Mes'], dr['Promedio'], marker='o', label='Real', color='blue')
            if cod in FLOTA: ax_line.axhline(y=FLOTA[cod]['ideal'], color='r', linestyle='--', label='Ideal')
            ax_line.set_title("Rendimiento"); ax_line.legend(); ax_line.grid(True, alpha=0.3)
            c1.pyplot(fig_line); plt.close(fig_line)
            
            fig_bar, ax_bar = plt.subplots(figsize=(6, 4)); fig_bar.patch.set_facecolor('white'); ax_bar.set_facecolor('white')
            ax_bar.bar(dr['Mes'], dr['Litros'], color='orange')
            ax_bar.set_title("Consumo (Litros)"); c2.pyplot(fig_bar); plt.close(fig_bar)
            
            st.dataframe(dr.style.format({"Litros": "{:.1f}", "Promedio": "{:.2f}"}), use_container_width=True)
            c1, c2 = st.columns(2)
            c1.download_button("PDF", generar_pdf_con_graficos(dr, f"Reporte {cod}"), f"{cod}.pdf")
            c2.download_button("Word", generar_word(dr, f"Reporte {cod}"), f"{cod}.docx")
        else: st.info(f"Sin datos registrados para el año {y}.")
