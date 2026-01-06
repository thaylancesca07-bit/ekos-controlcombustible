import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO E IDENTIDADE 🇵🇾 ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

# SEU LINK DE IMPLANTAÇÃO (JÁ INSERIDO)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyMiQPn1c5dG_bB0GVS5LSeKqMal2R3YsBtpfTGM1kM_JFMalrzahyEKgHcUG5cnyW9/exec"

# --- ATENÇÃO: COLOQUE O ID DA SUA PLANILHA AQUI PARA A LEITURA FUNCIONAR ---
# O ID é aquele código longo que fica no link da sua planilha no navegador
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E/export?format=csv"

ACCESS_CODE = "1645"
BARRILES = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

# Cadastro da Flota com Unidades Dinâmicas
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

# --- 2. GERADOR DE PDF ---
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
    cols = ['Codigo', 'Nombre', 'Ult. Carga', 'Litros', 'Estado']
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
st.markdown("<p style='font-size: 18px; color: gray; margin-top: -20px;'>desenvolvido por Excelencia Consultora en Paraguay 🇵🇾</p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["👋 Registro Personal", "🔐 Auditoría & Stock", "📊 Informe Ejecutivo"])

# --- TAB 1: REGISTRO ---
with tab1:
    st.subheader("¡Buen día! Registremos la actividad de hoy 😊")
    operacion = st.radio("¿Qué estamos haciendo? 🛠️", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
    
    if "Máquina" in operacion:
        sel = st.selectbox("Selecciona la Máquina:", options=[f"{k} - {v['nombre']}" for k, v in FLOTA.items()])
        cod_f = sel.split(" - ")[0]
        nom_f = FLOTA[cod_f]['nombre']
        unidad_txt = FLOTA[cod_f]['unidad']
        origen = st.selectbox("¿De dónde sale el combustible? ⛽", BARRILES + ["Surtidor Petrobras", "Surtidor Shell"])
    else:
        cod_f = st.selectbox("¿Qué barril vamos a llenar? 📦", options=BARRILES)
        nom_f = cod_f
        unidad_txt = "Litros"
        origen = st.selectbox("¿Desde qué surtidor viene? ⛽", ["Surtidor Petrobras", "Surtidor Shell"])

    with st.form("form_final_ekos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            chofer = st.text_input("Nombre del Chofer / Operador 🧑‍🌾")
            resp_cargo = st.text_input("Responsable del Cargo / Encargado 👤")
            fecha = st.date_input("Fecha 📅", date.today())
        with col2:
            actividad = st.text_input("Actividad a desarrollar 🔨")
            litros = st.number_input("Cantidad de Litros 💧", min_value=0.0, step=0.1)
            if "Máquina" in operacion:
                lectura = st.number_input(f"Lectura actual en {unidad_txt} 🔢", min_value=0.0)
            else:
                lectura = 0.0
        
        btn = st.form_submit_button("✅ GUARDAR REGISTRO")

    if btn:
        if not chofer or not resp_cargo or not actividad:
            st.warning("Por favor completa todos los campos. 😉")
        else:
            payload = {
                "fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f,
                "nombre_maquina": nom_f, "origen": origen, "chofer": chofer,
                "responsable_cargo": resp_cargo, "actividad": actividad,
                "lectura_actual": lectura, "litros": litros, "media": 0.0, "estado_consumo": "N/A"
            }
            try:
                r = requests.post(SCRIPT_URL, json=payload)
                if r.status_code == 200:
                    st.balloons()
                    st.success(f"¡Excelente! Registro de {nom_f} enviado a la nube. 🚀")
                else:
                    st.error("Error al enviar datos. Verifique la conexión.")
            except:
                st.error("Falla crítica de conexión con el Script de Google.")

# --- TAB 2: AUDITORÍA Y STOCK ---
with tab2:
    pwd1 = st.text_input("PIN de Seguridad", type="password", key="p1")
    if pwd1 == ACCESS_CODE:
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                st.subheader("📦 Stock Actual de Barriles")
                cols_b = st.columns(4)
                for i, b in enumerate(BARRILES):
                    entradas = df[(df['tipo_operacion'].str.contains("Barril")) & (df['codigo_maquina'] == b)]['litros'].sum()
                    salidas = df[(df['origen'] == b)]['litros'].sum()
                    stock_real = entradas - salidas
                    cols_b[i].metric(b, f"{stock_real:.1f} L", f"Entradas: {entradas}")

                st.markdown("---")
                st.subheader("📋 Historial de Movimientos")
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False, sep=';', encoding='latin-1').encode('latin-1')
                st.download_button("📥 Descargar Excel", csv, "auditoria_ekos.csv")
            else:
                st.info("Aún no hay datos registrados.")
        except:
            st.error("Error al leer la planilha. Asegúrate de que 'Cualquier persona con el link pueda leer'.")
    elif pwd1: st.error("Acceso denegado 🔒")

# --- TAB 3: INFORME EJECUTIVO ---
with tab3:
    pwd2 = st.text_input("PIN de Gerencia", type="password", key="p2")
    if pwd2 == ACCESS_CODE:
        try:
            df_full = pd.read_csv(SHEET_URL)
            if not df_full.empty:
                df_maquinas = df_full[df_full['tipo_operacion'].str.contains("Máquina")]
                st.subheader("📊 Resumen de Consumo por Equipo")
                resumo = df_maquinas.groupby('nombre_maquina')['litros'].sum()
                st.bar_chart(resumo)
                
                pdf_b = generar_pdf(df_maquinas)
                st.download_button("📄 Descargar Reporte PDF", pdf_b, "Informe_Ekos.pdf")
        except:
            st.error("Error al generar informes.")


