import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURACIÓN E IDENTIDAD 🇵🇾 ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

# ENLACES DE CONEXIÓN
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyMiQPn1c5dG_bB0GVS5LSeKqMal2R3YsBtpfTGM1kM_JFMalrzahyEKgHcUG5cnyW9/exec"
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

ACCESS_CODE = "1645"

# TIPOS DE COMBUSTIBLE DEFINIDOS
TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]

# MAPEO DE COMBUSTIBLES PETROBRAS
MAPA_COMBUSTIBLE = {
    "4002147 - Diesel EURO 5 S-50": "Diesel S500",
    "4002151 - NAFTA GRID 95": "Nafta",
    "4001812 - Diesel podium S-10 gr.": "Diesel Podium"
}

# MAPEO DE ENCARGADOS DEFINIDOS
ENCARGADOS_DATA = {
    "Juan Britez": {"pwd": "jb2026", "barril": "Barril Juan"},
    "Diego Bordon": {"pwd": "db2026", "barril": "Barril Diego"},
    "Jonatan Vargas": {"pwd": "jv2026", "barril": "Barril Jonatan"},
    "Cesar Cabañas": {"pwd": "cc2026", "barril": "Barril Cesar"},
    "Admin Ekos": {"pwd": "1645", "barril": "Todos"}
}

BARRILES_LISTA = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

# FLOTA CON O-01 ADICIONADO
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
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Excelencia Consultora - Nueva Esperanza - Canindeyu', 0, 1, 'C')
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
        pdf.cell(w[4], 10, str(row.get('estado_consumo', 'N/A')), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 3. INTERFAZ (Títulos y Subtítulos Originales) ---
st.title("⛽ Ekos Forestal / Control de combustible")
st.markdown("<p style='font-size: 18px; color: gray; margin-top: -20px;'>Desenvolvido por Excelencia Consultora en Paraguay 🇵🇾</p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["👋 Registro Personal", "🔐 Auditoría & Stock", "📊 Informe Grafico", "🔍 Confirmación de Datos"])

# --- TAB 1: REGISTRO PERSONAL ---
with tab1:
    st.subheader("🔑 Acceso de Encargado")
    c_auth1, c_auth2 = st.columns(2)
    with c_auth1: encargado_sel = st.selectbox("Encargado:", options=list(ENCARGADOS_DATA.keys()))
    with c_auth2: pwd_input = st.text_input("Contraseña:", type="password")

    if pwd_input == ENCARGADOS_DATA[encargado_sel]["pwd"]:
        st.markdown("---")
        operacion = st.radio("¿Qué estamos haciendo? 🛠️", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
        
        mi_barril = ENCARGADOS_DATA[encargado_sel]["barril"]
        opciones_origen = BARRILES_LISTA + ["Surtidor Petrobras", "Surtidor Shell"] if encargado_sel == "Auditoria" else [mi_barril, "Surtidor Petrobras", "Surtidor Shell"]

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if "Máquina" in operacion:
                sel_m = st.selectbox("Selecciona la Máquina:", options=[f"{k} - {v['nombre']}" for k, v in FLOTA.items()])
                cod_f, nom_f, unidad = sel_m.split(" - ")[0], FLOTA[sel_m.split(" - ")[0]]['nombre'], FLOTA[sel_m.split(" - ")[0]]['unidad']
                origen = st.selectbox("¿De dónde sale el combustible? ⛽", opciones_origen)
            else:
                cod_f = st.selectbox("¿Qué barril vamos a llenar? 📦", options=BARRILES_LISTA if encargado_sel == "Auditoria" else [mi_barril])
                nom_f, unidad, origen = cod_f, "Litros", st.selectbox("¿Desde qué surtidor viene? ⛽", ["Surtidor Petrobras", "Surtidor Shell"])
        
        with col_f2:
            tipo_comb = st.selectbox("Tipo de Combustible ⛽:", TIPOS_COMBUSTIBLE)

        with st.form("form_final_ekos", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                chofer, fecha, actividad = st.text_input("Nombre del Chofer / Operador 🧑‍🌾"), st.date_input("Fecha 📅", date.today()), st.text_input("Actividad a desarrollar 🔨")
            with col2:
                litros, lectura = st.number_input("Cantidad de Litros 💧", min_value=0.0, step=0.1), st.number_input(f"Lectura actual en {unidad} 🔢", min_value=0.0) if "Máquina" in operacion else 0.0
            
            if st.form_submit_button("✅ GUARDAR REGISTRO"):
                payload = {"fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f, "nombre_maquina": nom_f, "origen": origen, "chofer": chofer, "responsable_cargo": encargado_sel, "actividad": actividad, "lectura_actual": lectura, "litros": litros, "tipo_combustible": tipo_comb}
                try:
                    r = requests.post(SCRIPT_URL, json=payload)
                    if r.status_code == 200: st.balloons(); st.success(f"¡Excelente {encargado_sel}! Registro guardado exitosamente. 🚀")
                except: st.error("Falla de conexión.")
    elif pwd_input: st.error("❌ Contraseña incorrecta.")

# --- TAB 2: AUDITORÍA & STOCK ---
with tab2:
    if st.text_input("PIN Auditoría", type="password", key="p_aud") == ACCESS_CODE:
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
                st.subheader("📦 Stock Actual de Barriles")
                cb = st.columns(4)
                for i, b in enumerate(BARRILES_LISTA):
                    ent, sal = df[df['codigo_maquina'] == b]['litros'].sum(), df[df['origen'] == b]['litros'].sum()
                    cb[i].metric(b, f"{ent - sal:.1f} L")
                st.markdown("---")
                st.subheader("📋 Historial por Mes")
                cf1, cf2 = st.columns(2)
                with cf1:
                    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                    m_sel = st.selectbox("Mes:", options=range(1, 13), format_func=lambda x: meses[x-1], index=date.today().month - 1)
                with cf2: a_sel = st.selectbox("Año:", options=[2025, 2026], index=1)
                
                df_mes = df[(df['fecha'].dt.month == m_sel) & (df['fecha'].dt.year == a_sel)]
                st.dataframe(df_mes, use_container_width=True)
        except: st.error("Error al leer la base de datos.")

# --- TAB 3: INFORME GRAFICO ---
with tab3:
    if st.text_input("PIN Gerencia", type="password", key="p_ger") == ACCESS_CODE:
        try:
            df_full = pd.read_csv(SHEET_URL)
            if not df_full.empty:
                st.subheader("📊 Consumo Total por Maquina")
                st.bar_chart(df_full[df_full['tipo_operacion'].str.contains("Máquina")].groupby('nombre_maquina')['litros'].sum())
                pdf_b = generar_pdf(df_full[df_full['tipo_operacion'].str.contains("Máquina")])
                st.download_button("📄 Descargar Reporte PDF", pdf_b, "Informe_Ekos.pdf")
        except: st.error("Error en informes.")

# --- TAB 4: CONFIRMACIÓN DE DATOS (Mapeo F, P, K, O) ---
with tab4:
    if st.text_input("PIN Conciliación", type="password", key="p_con") == ACCESS_CODE:
        st.subheader("🔍 Lado a Lado: Ekos vs Petrobras")
        archivo_p = st.file_uploader("Alzar planilla de Petrobras", type=["xlsx"])
        if archivo_p:
            try:
                # F=5, P=15, K=10, O=14 (Basado en 0-index)
                df_p = pd.read_excel(archivo_p, usecols=[5, 10, 14, 15], names=["Fecha", "Responsable", "Comb_Original", "Litros"])
                df_p['Comb_Ekos'] = df_p['Comb_Original'].map(MAPA_COMBUSTIBLE).fillna("Otros")
                st.write("📋 Vista previa de datos Petrobras:")
                st.dataframe(df_p.head())
                
                if st.button("🚀 SUBIR Y COMPARAR EN LA NUBE"):
                    for _, r in df_p.iterrows():
                        p = {"fecha": str(r['Fecha']), "tipo_operacion": "FACTURA PETROBRAS", "codigo_maquina": "PETRO-F", "nombre_maquina": "Factura Petrobras", "origen": "Surtidor", "chofer": "N/A", "responsable_cargo": str(r['Responsable']), "actividad": "Conciliación", "lectura_actual": 0, "litros": float(r['Litros']), "tipo_combustible": r['Comb_Ekos'], "fuente_dato": "PETROBRAS_OFFICIAL"}
                        requests.post(SCRIPT_URL, json=p)
                    st.success("✅ Datos sincronizados y almacenados en la nube.")
            except Exception as e: st.error(f"Error en el mapeo de columnas F, P, K, O: {e}")
