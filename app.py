import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURACIÓN E IDENTIDAD 🇵🇾 ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyMiQPn1c5dG_bB0GVS5LSeKqMal2R3YsBtpfTGM1kM_JFMalrzahyEKgHcUG5cnyW9/exec"
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

ACCESS_CODE_AUDITORIA = "1645"
TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]

# MAPEO DE ENCARGADOS -> CONTRASEÑA Y SU BARRIL ASIGNADO
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
    "O-01": {"nombre": "Otros", "unidad": "Horas"}
}

# --- 2. GENERADOR DE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'INFORME EJECUTIVO - CONTROL EKOS 🇵🇾', 0, 1, 'C')
        self.ln(5)

def generar_pdf(df):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 8)
    cols = ['Codigo', 'Nombre', 'Fecha', 'Litros', 'Combustible']
    w = [25, 60, 30, 30, 40]
    for i, col in enumerate(cols): pdf.cell(w[i], 10, col, 1)
    pdf.ln()
    pdf.set_font('Arial', '', 8)
    for _, row in df.iterrows():
        pdf.cell(w[0], 10, str(row['codigo_maquina']), 1)
        pdf.cell(w[1], 10, str(row['nombre_maquina']), 1)
        pdf.cell(w[2], 10, str(row['fecha']), 1)
        pdf.cell(w[3], 10, f"{float(row['litros']):.1f}", 1)
        pdf.cell(w[4], 10, str(row.get('tipo_combustible', 'N/A')), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 3. INTERFAZ ---
st.title("⛽ Ekos Forestal / Control de combustible")
st.markdown("<p style='font-size: 18px; color: gray; margin-top: -20px;'>Desenvolvido por Excelencia Consultora en Paraguay 🇵🇾</p>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👋 Registro", "🔐 Auditoría & Stock", "📊 Gráficos", "🔍 Confirmación Petrobras"])

# --- TAB 1: REGISTRO ---
with tab1:
    st.subheader("🔑 Acceso de Encargado")
    c_auth1, c_auth2 = st.columns(2)
    with c_auth1: encargado_sel = st.selectbox("Encargado:", options=list(ENCARGADOS_DATA.keys()))
    with c_auth2: pwd_input = st.text_input("Contraseña:", type="password")

    if pwd_input == ENCARGADOS_DATA[encargado_sel]["pwd"]:
        st.markdown("---")
        operacion = st.radio("¿Qué estamos haciendo? 🛠️", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
        
        mi_barril = ENCARGADOS_DATA[encargado_sel]["barril"]
        op_origen = BARRILES_LISTA + ["Surtidor Petrobras", "Surtidor Shell"] if encargado_sel == "Admin Ekos" else [mi_barril, "Surtidor Petrobras", "Surtidor Shell"]
        
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            if "Máquina" in operacion:
                sel_m = st.selectbox("Máquina:", options=[f"{k} - {v['nombre']}" for k, v in FLOTA.items()])
                cod_f, nom_f, unidad = sel_m.split(" - ")[0], FLOTA[sel_m.split(" - ")[0]]['nombre'], FLOTA[sel_m.split(" - ")[0]]['unidad']
                origen = st.selectbox("¿De dónde sale el combustible?", op_origen)
            else:
                cod_f = st.selectbox("Barril a llenar:", options=BARRILES_LISTA if encargado_sel == "Admin Ekos" else [mi_barril])
                nom_f, unidad, origen = cod_f, "Litros", st.selectbox("Surtidor de Origen:", ["Surtidor Petrobras", "Surtidor Shell"])
        
        with c_f2:
            tipo_comb = st.selectbox("Tipo de Combustible ⛽:", TIPOS_COMBUSTIBLE)

        with st.form("form_final_v16", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                chofer, fecha, actividad = st.text_input("Nombre del Chofer / Operador 🧑‍🌾"), st.date_input("Fecha 📅", date.today()), st.text_input("Actividad 🔨")
            with col2:
                litros, lectura = st.number_input("Litros 💧", min_value=0.0, step=0.1), st.number_input(f"Lectura ({unidad}) 🔢", min_value=0.0) if "Máquina" in operacion else 0.0
            
            if st.form_submit_button("✅ GUARDAR REGISTRO"):
                if not chofer or not actividad:
                    st.warning("⚠️ Completa los datos.")
                else:
                    payload = {"fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f, "nombre_maquina": nom_f, "origen": origen, "chofer": chofer, "responsable_cargo": encargado_sel, "actividad": actividad, "lectura_actual": lectura, "litros": litros, "tipo_combustible": tipo_comb}
                    try:
                        r = requests.post(SCRIPT_URL, json=payload)
                        if r.status_code == 200: st.balloons(); st.success("¡Guardado!")
                    except: st.error("Error de conexión.")
    elif pwd_input: st.error("❌ Contraseña incorrecta.")

# --- TAB 2: AUDITORÍA ---
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
                    ent, sal = df[df['codigo_maquina'] == b]['litros'].sum(), df[df['origen'] == b]['litros'].sum()
                    cb[i].metric(b, f"{ent - sal:.1f} L")
                
                st.dataframe(df_mes, use_container_width=True)
                csv = df_mes.to_csv(index=False, sep=';').encode('latin-1')
                st.download_button("📥 Descargar Excel", csv, f"auditoria_{m_sel}.csv")
        except: st.error("Error al leer datos.")

# --- TAB 3: GRÁFICOS ---
with tab3:
    if st.text_input("PIN Gerencia", type="password", key="p_ger") == ACCESS_CODE_AUDITORIA:
        try:
            df_full = pd.read_csv(SHEET_URL)
            if not df_full.empty:
                df_maq = df_full[df_full['tipo_operacion'].str.contains("Máquina")]
                st.subheader("📊 Consumo Total por Equipo")
                st.bar_chart(df_maq.groupby('nombre_maquina')['litros'].sum())
                pdf_b = generar_pdf(df_maq)
                st.download_button("📄 Descargar PDF", pdf_b, "Informe_Ekos.pdf")
        except: st.error("Error en informes.")

# --- TAB 4: CONFIRMACIÓN PETROBRAS ---
with tab4:
    st.subheader("🔍 Conciliación Petrobras")
    archivo_p = st.file_uploader("Subir Excel/CSV de Petrobras", type=["csv", "xlsx"])
    if archivo_p:
        try:
            df_p = pd.read_csv(archivo_p) if archivo_p.name.endswith('.csv') else pd.read_excel(archivo_p)
            c_f = st.selectbox("Columna Fecha:", df_p.columns)
            c_l = st.selectbox("Columna Litros:", df_p.columns)
            if st.button("🚀 Comparar"):
                df_internal = pd.read_csv(SHEET_URL)
                total_int = df_internal[df_internal['origen'].str.contains("Petrobras", na=False)]['litros'].sum()
                total_ext = df_p[c_l].sum()
                st.metric("Petrobras", f"{total_ext:.2f} L")
                st.metric("Ekos", f"{total_int:.2f} L", delta=f"{total_int - total_ext:.2f} L")
        except Exception as e: st.error(f"Error: {e}")
