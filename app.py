import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURACIÓN E IDENTIDAD 🇵🇾 ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

# ENLACES DE CONEXIÓN (TU PUENTE GRATUITO)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyMiQPn1c5dG_bB0GVS5LSeKqMal2R3YsBtpfTGM1kM_JFMalrzahyEKgHcUG5cnyW9/exec"

# REEMPLAZA 'TU_ID_DE_PLANILLA' con el código largo que sale en el link de tu Google Sheet
# Ejemplo: https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit
SHEET_ID = "TU_ID_DE_PLANILLA" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

ACCESS_CODE = "1645"
BARRILES = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

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
    cols = ['Codigo', 'Nombre', 'Ult. Carga', 'Litros', 'Estado']
    w = [25, 60, 30, 30, 40]
    for i, col in enumerate(cols): pdf.cell(w[i], 10, col, 1)
    pdf.ln()
    pdf.set_font('Arial', '', 8)
    for _, row in df.iterrows():
        pdf.cell(w[0], 10, str(row['codigo_maquina']), 1)
        pdf.cell(w[1], 10, str(row['nombre_maquina']), 1)
        pdf.cell(w[2], 10, str(row['fecha']), 1)
        pdf.cell(w[3], 10, f"{row['litros']:.1f}", 1)
        pdf.cell(w[4], 10, str(row['estado_consumo']), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 3. INTERFAZ ---
st.title("🇵🇾 Ekos Forestal / Control de combustible")
st.markdown("<p style='font-size: 18px; color: gray; margin-top: -20px;'>desarrollado por Excelencia Consultora - Gratis para Ekos</p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["👋 Registro", "🔐 Auditoría & Stock", "📊 Reportes PDF"])

with tab1:
    st.subheader("¡Buen día! Registremos la actividad de hoy 😊")
    operacion = st.radio("¿Qué estamos haciendo? 🛠️", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
    
    if "Máquina" in operacion:
        sel = st.selectbox("Máquina:", options=[f"{k} - {v['nombre']}" for k,v in FLOTA.items()])
        cod_f = sel.split(" - ")[0]
        nom_f = FLOTA[cod_f]['nombre']
        unidad = FLOTA[cod_f]['unidad']
        origen = st.selectbox("Origen del combustible ⛽", BARRILES + ["Surtidor Petrobras", "Surtidor Shell"])
    else:
        cod_f = st.selectbox("Seleccione Barril:", options=BARRILES)
        nom_f = cod_f
        unidad = "Litros"
        origen = st.selectbox("Surtidor de Origen ⛽", ["Surtidor Petrobras", "Surtidor Shell"])

    with st.form("form_v12", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            chofer = st.text_input("Chofer 🧑‍🌾")
            resp = st.text_input("Responsable 👤")
            fecha = st.date_input("Fecha", date.today())
        with c2:
            act = st.text_input("Actividad 🔨")
            lts = st.number_input("Litros 💧", min_value=0.0)
            lectura = st.number_input(f"Lectura en {unidad}", min_value=0.0) if "Máquina" in operacion else 0.0
        
        btn = st.form_submit_button("✅ GUARDAR REGISTRO")

    if btn:
        if not chofer or not resp:
            st.warning("Completa los nombres.")
        else:
            payload = {
                "fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f,
                "nombre_maquina": nom_f, "origen": origen, "chofer": chofer,
                "responsable_cargo": resp, "actividad": act,
                "lectura_actual": lectura, "litros": lts, "media": 0.0, "estado_consumo": "N/A"
            }
            # Enviar datos al script de Google de forma gratuita
            try:
                r = requests.post(SCRIPT_URL, json=payload)
                if r.status_code == 200:
                    st.balloons()
                    st.success(f"¡Excelente! Registro de {nom_f} guardado en la nube. 🚀")
                else:
                    st.error("Error al guardar. Verifica la URL del Script.")
            except:
                st.error("Falla de conexión. Revisa el link del Script.")

with tab2:
    if st.text_input("PIN Auditoría", type="password", key="p_aud") == ACCESS_CODE:
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                st.subheader("📦 Stock Actual de Barriles")
                cols = st.columns(4)
                for i, b in enumerate(BARRILES):
                    entradas = df[(df['tipo_operacion'].str.contains("Barril")) & (df['codigo_maquina'] == b)]['litros'].sum()
                    salidas = df[(df['origen'] == b)]['litros'].sum()
                    cols[i].metric(b, f"{entradas - salidas:.1f} L")
                
                st.markdown("---")
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False, sep=';').encode('latin-1')
                st.download_button("📥 Descargar Excel", csv, "auditoria_ekos.csv")
            else:
                st.info("La planilla está vacía.")
        except:
            st.error("Error al leer datos. Asegúrate de que la planilla sea pública para lectura.")

with tab3:
    if st.text_input("PIN Reportes", type="password", key="p_rep") == ACCESS_CODE:
        try:
            df_rep = pd.read_csv(SHEET_URL)
            if not df_rep.empty:
                res = df_rep[df_rep['tipo_operacion'].str.contains("Máquina")].groupby('nombre_maquina')['litros'].sum().reset_index()
                st.bar_chart(res.set_index('nombre_maquina'))
                pdf_b = generar_pdf(df_rep[df_rep['tipo_operacion'].str.contains("Máquina")])
                st.download_button("📄 Descargar PDF Ejecutivo", pdf_b, "Informe_Ekos.pdf")
        except:
            st.error("Error al generar reporte.")

