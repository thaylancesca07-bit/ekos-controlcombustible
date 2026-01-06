import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURACIÓN E IDENTIDAD 🇵🇾 ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

# ENLACES DE CONEXIÓN
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyMiQPn1c5dG_bB0GVS5LSeKqMal2R3YsBtpfTGM1kM_JFMalrzahyEKgHcUG5cnyW9/exec"

# ID DE TU PLANILLA (Mantenemos el que pasaste)
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- CONFIGURACIÓN DE SEGURIDAD ---
ACCESS_CODE_AUDITORIA = "1645"

# MAPEO DE ENCARGADOS -> CONTRASEÑA Y SU BARRIL ASIGNADO
# Aquí definimos quién cuida cada barril
ENCARGADOS_DATA = {
    "Juan Britez": {"pwd": "jb2026", "barril": "Barril Juan"},
    "Diego Bordon": {"pwd": "db2026", "barril": "Barril Diego"},
    "Jonatan Vargas": {"pwd": "jv2026", "barril": "Barril Jonatan"},
    "Cesar Cabañas": {"pwd": "cc2026", "barril": "Barril Cesar"},
    "Admin Ekos": {"pwd": "1645", "barril": "Todos"}
}

BARRILES_LISTA = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

FLOTA = {
    "HV-01": {"nombre": "Caterpilar 320D", "unidad": "Horas"},
    "JD-01": {"nombre": "John Deere", "unidad": "Horas"},
    "M-11": {"nombre": "N. Frontier", "unidad": "KM"},
    "M-17": {"nombre": "GM S-10", "unidad": "KM"},
    "V-12": {"nombre": "Valtra 180", "unidad": "Horas"},
    "JD-03": {"nombre": "John Deere 6110", "unidad": "Horas"},
    "MC-06": {"nombre": "MB Canter", "unidad": "KM"},
    "M-02": {"nombre": "Chevrolet - S10", "unidad": "KM"},
    "JD-02": {"nombre": "John Deere 6170", "unidad": "Horas"},
    "MF-02": {"nombre": "Massey", "unidad": "Horas"},
    "V-07": {"nombre": "Valmet 1580", "unidad": "Horas"},
    "TM-01": {"nombre": "Pala Michigan", "unidad": "Horas"},
    "JD-04": {"nombre": "John Deere 5090", "unidad": "Horas"},
    "V-02": {"nombre": "Valmet 785", "unidad": "Horas"},
    "V-11": {"nombre": "Valmet 8080", "unidad": "Horas"},
    "M13": {"nombre": "Nisan Frontier (M13)", "unidad": "Horas"},
    "TF01": {"nombre": "Ford", "unidad": "Horas"},
    "MICHIGAN": {"nombre": "Pala Michigan", "unidad": "Horas"},
    "S-08": {"nombre": "Scania Rojo", "unidad": "KM"},
    "S-05": {"nombre": "Scania Azul", "unidad": "KM"},
    "M-03": {"nombre": "GM S-10 (M-03)", "unidad": "KM"},
    "S-03": {"nombre": "Scania 113H", "unidad": "KM"},
    "S-06": {"nombre": "Scania P112H", "unidad": "Horas"},
    "S-07": {"nombre": "Scania R380", "unidad": "Horas"},
    "O-01": {"nombre": "Otros¨, "unidad": "Horas¨}, 
}

# --- 2. GENERADOR DE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'INFORME EJECUTIVO - CONTROL EKOS 🇵🇾', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Excelencia Consultora - Nueva Esperanza', 0, 1, 'C')
        self.ln(5)

def generar_pdf(df):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 8)
    cols = ['Codigo', 'Nombre', 'Fecha', 'Litros', 'Estado']
    w = [25, 60, 30, 30, 40]
    for i, col in enumerate(cols): pdf.cell(w[i], 10, col, 1)
    pdf.ln()
    pdf.set_font('Arial', '', 8)
    for _, row in df.iterrows():
        pdf.cell(w[0], 10, str(row['codigo_maquina']), 1)
        pdf.cell(w[1], 10, str(row['nombre_maquina']), 1)
        pdf.cell(w[2], 10, str(row['fecha']), 1)
        pdf.cell(w[3], 10, f"{float(row['litros']):.1f}", 1)
        pdf.cell(w[4], 10, str(row['estado_consumo']), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 3. INTERFAZ ---
st.title("⛽ Ekos Forestal / Control de combustible")
st.markdown("<p style='font-size: 18px; color: gray; margin-top: -20px;'>Desenvolvido por Excelencia Consultora en Paraguay 🇵🇾</p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["👋 Registro Personal", "🔐 Auditoría & Stock", "📊 Informe Grafico"])

# --- TAB 1: REGISTRO RESTRINGIDO ---
with tab1:
    st.subheader("🔑 Acceso de Encargado")
    c_auth1, c_auth2 = st.columns(2)
    with c_auth1:
        encargado_sel = st.selectbox("Encargado:", options=list(ENCARGADOS_DATA.keys()))
    with c_auth2:
        pwd_input = st.text_input("Contraseña:", type="password")

    st.markdown("---")
    
    # Solo mostrar el formulario si la contraseña es correcta (para filtrar opciones)
    if pwd_input == ENCARGADOS_DATA[encargado_sel]["pwd"]:
        operacion = st.radio("¿Qué estamos haciendo? 🛠️", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
        
        # FILTRO DE ORIGEN SEGÚN EL ENCARGADO
        if encargado_sel == "Admin Ekos":
            opciones_origen = BARRILES_LISTA + ["Surtidor Petrobras", "Surtidor Shell"]
            opciones_barril_destino = BARRILES_LISTA
        else:
            mi_barril = ENCARGADOS_DATA[encargado_sel]["barril"]
            opciones_origen = [mi_barril, "Surtidor Petrobras", "Surtidor Shell"]
            opciones_barril_destino = [mi_barril]

        if "Máquina" in operacion:
            sel_m = st.selectbox("Máquina:", options=[f"{k} - {v['nombre']}" for k, v in FLOTA.items()])
            cod_f = sel_m.split(" - ")[0]
            nom_f = FLOTA[cod_f]['nombre']
            unidad = FLOTA[cod_f]['unidad']
            origen = st.selectbox("¿De dónde sale el combustible? ⛽", opciones_origen)
        else:
            cod_f = st.selectbox("¿Qué barril vamos a llenar? 📦", options=opciones_barril_destino)
            nom_f = cod_f
            unidad = "Litros"
            origen = st.selectbox("¿Desde qué surtidor viene? ⛽", ["Surtidor Petrobras", "Surtidor Shell"])

        with st.form("form_ekos_v15", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                chofer = st.text_input("Nombre del Chofer / Operador 🧑‍🌾")
                fecha = st.date_input("Fecha 📅", date.today())
                actividad = st.text_input("Actividad 🔨")
            with col2:
                litros = st.number_input("Cantidad de Litros 💧", min_value=0.0, step=0.1)
                lectura = st.number_input(f"Lectura actual en {unidad} 🔢", min_value=0.0) if "Máquina" in operacion else 0.0
            
            btn = st.form_submit_button("✅ GUARDAR REGISTRO")

        if btn:
            if not chofer or not actividad:
                st.warning("⚠️ Completa chofer y actividad.")
            else:
                payload = {
                    "fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f,
                    "nombre_maquina": nom_f, "origen": origen, "chofer": chofer,
                    "responsable_cargo": encargado_sel, "actividad": actividad,
                    "lectura_actual": lectura, "litros": litros, "media": 0.0, "estado_consumo": "N/A"
                }
                try:
                    r = requests.post(SCRIPT_URL, json=payload)
                    if r.status_code == 200:
                        st.balloons()
                        st.success(f"¡Excelente {encargado_sel}! Datos guardados. 🚀")
                    else: st.error("Error al enviar.")
                except: st.error("Falla de conexión.")
    elif pwd_input:
        st.error("❌ Contraseña incorrecta para este encargado.")

# --- TAB 2: AUDITORÍA CON FILTRO ---
with tab2:
    if st.text_input("PIN Maestro Auditoría", type="password", key="p_aud") == ACCESS_CODE_AUDITORIA:
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
                
                st.subheader("📅 Historial por Mes")
                cf1, cf2 = st.columns(2)
                with cf1:
                    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                    m_sel = st.selectbox("Mes:", options=range(1, 13), format_func=lambda x: meses[x-1], index=date.today().month - 1)
                with cf2:
                    a_sel = st.selectbox("Año:", options=[2025, 2026], index=1)

                df_mes = df[(df['fecha'].dt.month == m_sel) & (df['fecha'].dt.year == a_sel)]

                st.subheader("📦 Stock Actual Real")
                cb = st.columns(4)
                for i, b in enumerate(BARRILES_LISTA):
                    ent = df[(df['codigo_maquina'] == b)]['litros'].sum()
                    sal = df[(df['origen'] == b)]['litros'].sum()
                    cb[i].metric(b, f"{ent - sal:.1f} L")

                st.markdown("---")
                st.dataframe(df_mes, use_container_width=True)
                csv = df_mes.to_csv(index=False, sep=';').encode('latin-1')
                st.download_button(f"📥 Descargar Excel {meses[m_sel-1]}", csv, f"auditoria_{m_sel}.csv")
        except: st.error("Error al leer la planilla.")

# --- TAB 3: INFORME ---
with tab3:
    if st.text_input("PIN Gerencia", type="password", key="p_ger") == ACCESS_CODE_AUDITORIA:
        try:
            df_full = pd.read_csv(SHEET_URL)
            if not df_full.empty:
                df_maq = df_full[df_full['tipo_operacion'].str.contains("Máquina")]
                st.subheader("📊 Consumo Total por Equipo")
                resumo = df_maq.groupby('nombre_maquina')['litros'].sum()
                st.bar_chart(resumo)
                pdf_b = generar_pdf(df_maq)
                st.download_button("📄 Descargar Reporte PDF", pdf_b, "Informe_Ekos.pdf")
        except: st.error("Error en informes.")


