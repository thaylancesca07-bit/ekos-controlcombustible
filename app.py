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

ACCESS_CODE_AUDITORIA = "1645"
TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]

# TRADUCCIÓN DE COMBUSTIBLES PETROBRAS
MAPA_COMBUSTIBLE = {
    "4002147 - Diesel EURO 5 S-50": "Diesel S500",
    "4002151 - NAFTA GRID 95": "Nafta",
    "4001812 - Diesel podium S-10 gr.": "Diesel Podium"
}

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
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Excelencia Consultora - Nueva Esperanza', 0, 1, 'C')
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
st.title("⛽ Ekos Forestal / Control Integrado 2026")
st.markdown("---")

tabs = st.tabs(["👋 Registro", "🔐 Auditoría", "📊 Gráficos", "🔍 Conciliación Petrobras"])

# --- TAB 1: REGISTRO ---
with tabs[0]:
    st.subheader("🔑 Validación")
    c_a1, c_a2 = st.columns(2)
    with c_a1: encargado = st.selectbox("Encargado:", options=list(ENCARGADOS_DATA.keys()))
    with c_a2: pwd = st.text_input("Contraseña:", type="password")

    if pwd == ENCARGADOS_DATA[encargado]["pwd"]:
        op = st.radio("Operación:", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
        barril_propio = ENCARGADOS_DATA[encargado]["barril"]
        
        orig_op = BARRILES_LISTA + ["Surtidor Petrobras", "Surtidor Shell"] if encargado == "Admin Ekos" else [barril_propio, "Surtidor Petrobras", "Surtidor Shell"]
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if "Máquina" in op:
                sel_m = st.selectbox("Máquina:", options=[f"{k} - {v['nombre']}" for k, v in FLOTA.items()])
                cod, nom, uni = sel_m.split(" - ")[0], FLOTA[sel_m.split(" - ")[0]]['nombre'], FLOTA[sel_m.split(" - ")[0]]['unidad']
                orig = st.selectbox("Origen:", orig_op)
            else:
                cod = st.selectbox("Barril:", options=BARRILES_LISTA if encargado == "Admin Ekos" else [barril_propio])
                nom, uni, orig = cod, "Litros", st.selectbox("Surtidor:", ["Surtidor Petrobras", "Surtidor Shell"])
        
        with col_f2: tipo_c = st.selectbox("Combustible:", TIPOS_COMBUSTIBLE)

        with st.form("registro_v20", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1: chof, fec, act = st.text_input("Chofer"), st.date_input("Fecha", date.today()), st.text_input("Actividad")
            with c2: lts, lec = st.number_input("Litros", min_value=0.0), st.number_input(f"Lectura ({uni})", min_value=0.0) if "Máquina" in op else 0.0
            if st.form_submit_button("✅ GUARDAR"):
                if chof and act:
                    pay = {"fecha": str(fec), "tipo_operacion": op, "codigo_maquina": cod, "nombre_maquina": nom, "origen": orig, "chofer": chof, "responsable_cargo": encargado, "actividad": act, "lectura_actual": lec, "litros": lts, "tipo_combustible": tipo_c}
                    try:
                        if requests.post(SCRIPT_URL, json=pay).status_code == 200: st.balloons(); st.success("¡Éxito!")
                    except: st.error("Error de conexión.")
    elif pwd: st.error("❌ Contraseña incorrecta.")

# --- TAB 2: AUDITORÍA ---
with tabs[1]:
    if st.text_input("PIN Auditoría", type="password", key="p_aud") == ACCESS_CODE_AUDITORIA:
        try:
            df = pd.read_csv(SHEET_URL).dropna(subset=['fecha'])
            df['fecha'] = pd.to_datetime(df['fecha'])
            st.subheader("📦 Stock Real")
            cb = st.columns(4)
            for i, b in enumerate(BARRILES_LISTA):
                cb[i].metric(b, f"{df[df['codigo_maquina']==b]['litros'].sum() - df[df['origen']==b]['litros'].sum():.1f} L")
            st.dataframe(df.sort_values(by='fecha', ascending=False))
        except: st.error("No se pudo leer la base de datos.")

# --- TAB 3: GRÁFICOS ---
with tabs[2]:
    if st.text_input("PIN Reportes", type="password", key="p_rep") == ACCESS_CODE_AUDITORIA:
        try:
            df_g = pd.read_csv(SHEET_URL)
            st.bar_chart(df_g[df_g['tipo_operacion'].str.contains("Máquina", na=False)].groupby('nombre_maquina')['litros'].sum())
        except: st.error("Error en gráficos.")

# --- TAB 4: CONCILIACIÓN PETROBRAS (F, P, K, O) ---
with tabs[3]:
    if st.text_input("PIN Conciliación", type="password", key="p_con") == ACCESS_CODE_AUDITORIA:
        st.subheader("🔍 Mapeo Petrobras (Columnas F, P, K, O)")
        file_p = st.file_uploader("Subir Excel de Petrobras", type=["xlsx"])
        if file_p:
            try:
                # F=5, K=10, O=14, P=15
                df_p = pd.read_excel(file_p, usecols=[5, 10, 14, 15], names=["Fecha", "Responsable", "Comb_Original", "Litros"])
                df_p['Comb_Ekos'] = df_p['Comb_Original'].map(MAPA_COMBUSTIBLE).fillna("Otros")
                st.dataframe(df_p)
                if st.button("🚀 SUBIR A LA NUBE"):
                    for _, r in df_p.iterrows():
                        p = {"fecha": str(r['Fecha']), "tipo_operacion": "FACTURA PETROBRAS", "codigo_maquina": "PETRO-F", "nombre_maquina": "Petrobras", "origen": "Surtidor", "chofer": "Factura", "responsable_cargo": str(r['Responsable']), "actividad": "Conciliación", "lectura_actual": 0, "litros": float(r['Litros']), "tipo_combustible": r['Comb_Ekos'], "fuente_dato": "PETROBRAS_OFFICIAL"}
                        requests.post(SCRIPT_URL, json=p)
                    st.success("✅ Datos sincronizados.")
            except Exception as e: st.error(f"Error: {e}")
