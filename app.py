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
SHEET_URL = f"https://docs.google.com/spreadsheets/d/1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E/export?format=csv"

ACCESS_CODE_MAESTRO = "1645"
TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]

# TRADUCCIÓN DE COMBUSTIBLES PETROBRAS
MAPA_COMBUSTIBLE = {
    "4002147 - Diesel EURO 5 S-50": "Diesel S500",
    "4002151 - NAFTA GRID 95": "Nafta",
    "4001812 - Diesel podium S-10 gr.": "Diesel Podium"
}

# MAPEO DE ENCARGADOS (Admin Ekos cambiado por Auditoria)
ENCARGADOS_DATA = {
    "Juan Britez": {"pwd": "jb2026", "barril": "Barril Juan"},
    "Diego Bordon": {"pwd": "db2026", "barril": "Barril Diego"},
    "Jonatan Vargas": {"pwd": "jv2026", "barril": "Barril Jonatan"},
    "Cesar Cabañas": {"pwd": "cc2026", "barril": "Barril Cesar"},
    "Auditoria": {"pwd": "1645", "barril": "Acceso Total"}
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
        self.cell(0, 10, 'Excelencia Consultora - Nueva Esperanza - Canindeyu', 0, 1, 'C')
        self.ln(5)

def generar_pdf(df):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 8)
    cols = ['Codigo', 'Nombre', 'Fecha', 'Litros', 'Combustible']
    w = [25, 50, 30, 30, 45]
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
        
        # LOGICA PARA AUDITORIA (Admin): Ver todos los barriles.
        if encargado_sel == "Auditoria":
            opciones_barril = BARRILES_LISTA
            opciones_origen = BARRILES_LISTA + ["Surtidor Petrobras", "Surtidor Shell"]
        else:
            mi_barril = ENCARGADOS_DATA[encargado_sel]["barril"]
            opciones_barril = [mi_barril]
            opciones_origen = [mi_barril, "Surtidor Petrobras", "Surtidor Shell"]

        c_f1, c_f2 = st.columns(2)
        with c_f1:
            if "Máquina" in operacion:
                sel_m = st.selectbox("Selecciona la Máquina:", options=[f"{k} - {v['nombre']}" for k, v in FLOTA.items()])
                cod_f, nom_f, unidad = sel_m.split(" - ")[0], FLOTA[sel_m.split(" - ")[0]]['nombre'], FLOTA[sel_m.split(" - ")[0]]['unidad']
                origen = st.selectbox("¿De dónde sale el combustible? ⛽", opciones_origen)
            else:
                cod_f = st.selectbox("¿Qué barril vamos a llenar? 📦", options=opciones_barril)
                nom_f, unidad = cod_f, "Litros"
                origen = st.selectbox("¿Desde qué surtidor viene? ⛽", ["Surtidor Petrobras", "Surtidor Shell"])
        
        with c_f2:
            tipo_comb = st.selectbox("Tipo de Combustible ⛽:", TIPOS_COMBUSTIBLE)

        with st.form("form_final_ekos", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                chofer, fecha, actividad = st.text_input("Nombre del Chofer / Operador 🧑‍🌾"), st.date_input("Fecha 📅", date.today()), st.text_input("Actividad a desarrollar 🔨")
            with col2:
                litros, lectura = st.number_input("Cantidad de Litros 💧", min_value=0.0, step=0.1), st.number_input(f"Lectura actual en {unidad} 🔢", min_value=0.0) if "Máquina" in operacion else 0.0
            
            if st.form_submit_button("✅ GUARDAR REGISTRO"):
                if not chofer or not actividad:
                    st.warning("⚠️ Por favor completa los campos obligatorios.")
                else:
                    payload = {"fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f, "nombre_maquina": nom_f, "origen": origen, "chofer": chofer, "responsable_cargo": encargado_sel, "actividad": actividad, "lectura_actual": lectura, "litros": litros, "tipo_combustible": tipo_comb}
                    try:
                        r = requests.post(SCRIPT_URL, json=payload)
                        if r.status_code == 200: st.balloons(); st.success(f"¡Excelente {encargado_sel}! Registro guardado en la nube. 🚀")
                    except: st.error("Error de conexión al servidor.")
    elif pwd_input: st.error("❌ Contraseña incorrecta.")

# --- TAB 2: AUDITORÍA & STOCK (DESGLOSADO POR COMBUSTIBLE) ---
with tab2:
    if st.text_input("PIN Maestro Auditoría", type="password", key="p_aud") == ACCESS_CODE_MAESTRO:
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
                
                st.subheader("📦 Verificación de Stock")
                tipo_audit = st.radio("Seleccione el combustible para verificar stock:", TIPOS_COMBUSTIBLE, horizontal=True)
                
                st.markdown(f"#### Estado de **{tipo_audit}** en cada Barril")
                cb = st.columns(4)
                
                for i, b in enumerate(BARRILES_LISTA):
                    # Filtramos por barril y tipo específico de combustible
                    entradas = df[(df['codigo_maquina'] == b) & (df['tipo_combustible'] == tipo_audit)]['litros'].sum()
                    salidas = df[(df['origen'] == b) & (df['tipo_combustible'] == tipo_audit)]['litros'].sum()
                    stock_real = entradas - salidas
                    cb[i].metric(b, f"{stock_real:.1f} L", f"Entradas: {entradas:.0f}")

                st.markdown("---")
                st.subheader("📋 Historial de Movimientos")
                st.dataframe(df.sort_values(by='fecha', ascending=False), use_container_width=True)
        except: st.error("No se pudo cargar la base de datos.")

# --- TAB 3: INFORME GRAFICO ---
with tab3:
    if st.text_input("PIN Gerencia", type="password", key="p_ger") == ACCESS_CODE_MAESTRO:
        try:
            df_full = pd.read_csv(SHEET_URL)
            if not df_full.empty:
                df_maq = df_full[df_full['tipo_operacion'].str.contains("Máquina")]
                st.subheader("📊 Consumo Total por Equipo (Litros)")
                st.bar_chart(df_maq.groupby('nombre_maquina')['litros'].sum())
                
                pdf_b = generar_pdf(df_maq)
                st.download_button("📄 Descargar Reporte PDF", pdf_b, "Informe_Ekos.pdf")
        except: st.error("Error al procesar los gráficos.")

# --- TAB 4: CONFIRMACIÓN DE DATOS (PETROBRAS) ---
with tab4:
    if st.text_input("PIN Conciliación", type="password", key="p_con") == ACCESS_CODE_MAESTRO:
        st.subheader("🔍 Lado a Lado: Ekos vs Petrobras")
        archivo_p = st.file_uploader("Alzar planilla de Petrobras (Excel)", type=["xlsx"])
        if archivo_p:
            try:
                # Mapeo exacto solicitado: F(5), P(15), K(10), O(14)
                df_p = pd.read_excel(archivo_p, usecols=[5, 10, 14, 15], names=["Fecha", "Responsable", "Comb_Original", "Litros"])
                df_p['Comb_Ekos'] = df_p['Comb_Original'].map(MAPA_COMBUSTIBLE).fillna("Otros")
                st.write("Vista previa de la planilla Petrobras:")
                st.dataframe(df_p.head())
                
                if st.button("🚀 SUBIR DATOS PETROBRAS A LA NUBE"):
                    for _, r in df_p.iterrows():
                        p = {"fecha": str(r['Fecha']), "tipo_operacion": "FACTURA PETROBRAS", "codigo_maquina": "PETRO-F", "nombre_maquina": "Factura", "origen": "Surtidor", "chofer": "N/A", "responsable_cargo": str(r['Responsable']), "actividad": "Conciliación", "lectura_actual": 0, "litros": float(r['Litros']), "tipo_combustible": r['Comb_Ekos'], "fuente_dato": "PETROBRAS_OFFICIAL"}
                        requests.post(SCRIPT_URL, json=p)
                    st.success("✅ Datos de Petrobras sincronizados exitosamente.")
            except Exception as e: st.error(f"Error en la lectura del archivo: {e}")


