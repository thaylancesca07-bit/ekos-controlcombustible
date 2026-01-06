import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN Y PARÁMETROS 🇵🇾 ---
ACCESS_CODE = "1645"
BARRILES = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

# Especificaciones de consumo para auditoría
SPECS = {
    "HV-01": {"min": 18.0, "max": 23.0}, "JD-01": {"min": 6.0, "max": 7.0},
    "V-12": {"min": 7.0, "max": 9.0}, "M-03": {"min": 10.0, "max": 12.5},
    "S-03": {"min": 1.53, "max": 1.81}, "S-05": {"min": 1.42, "max": 1.81},
    "S-06": {"min": 3.3, "max": 4.0}, "S-07": {"min": 3.3, "max": 4.0},
    "S-08": {"min": 1.66, "max": 1.81},
}

# Diccionario de Flota con unidades específicas
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
        pdf.cell(w[0], 10, str(row['Código']), 1)
        pdf.cell(w[1], 10, str(row['Nombre']), 1)
        pdf.cell(w[2], 10, str(row['Ultima Carga']), 1)
        pdf.cell(w[3], 10, f"{row['Total Litros']:.1f}", 1)
        pdf.cell(w[4], 10, str(row['Estado']), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 3. INTERFAZ PRINCIPAL ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🇵🇾 Combustible Control Ekos")
st.markdown("<p style='font-size: 18px; color: gray; margin-top: -20px;'>powered by Excelencia Consultora - Nueva Esperanza</p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["👋 Registro Personal", "🔐 Auditoría & Stock", "📊 Informe Ejecutivo"])

# --- TAB 1: REGISTRO ---
with tab1:
    st.subheader("¡Buen día! Registremos la actividad de hoy 😊")
    operacion = st.radio("¿Qué estamos haciendo? 🛠️", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
    
    # Lógica dinámica para selección de destino
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

    with st.form("form_final_v10", clear_on_submit=True):
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
            try:
                df_actual = conn.read()
                media, estado = 0.0, "N/A"
                
                # Cálculo de media y auditoría
                if "Máquina" in operacion and not df_actual.empty:
                    last_reg = df_actual[df_actual['codigo_maquina'] == cod_f]
                    if not last_reg.empty:
                        v_ant = float(last_reg.iloc[-1]['lectura_actual'])
                        if lectura > v_ant and litros > 0:
                            media = (lectura - v_ant) / litros
                            if cod_f in SPECS:
                                s = SPECS[cod_f]
                                estado = "NORMAL" if s["min"] <= media <= s["max"] else "ANORMAL"

                new_row = pd.DataFrame([{
                    "fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f,
                    "nombre_maquina": nom_f, "origen": origen, "chofer": chofer,
                    "responsable_cargo": resp_cargo, "actividad": actividad,
                    "lectura_actual": lectura, "litros": litros, "media": media, "estado_consumo": estado
                }])
                
                updated_df = pd.concat([df_actual, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.balloons()
                st.success(f"¡Excelente! Registro de {nom_f} guardado en la nube. 🇵🇾")
            except Exception as e:
                st.error("Error al conectar con la nube. Verifica los Secrets.")

# --- TAB 2: AUDITORÍA Y STOCK ---
with tab2:
    pwd1 = st.text_input("PIN de Seguridad", type="password", key="p1")
    if pwd1 == ACCESS_CODE:
        df_audit = conn.read()
        if not df_audit.empty and not df_audit.dropna(how='all').empty:
            st.subheader("📦 Stock Actual de Barriles")
            cols_b = st.columns(4)
            for i, b in enumerate(BARRILES):
                # Entradas: Surtidor -> Barril
                entradas = df_audit[(df_audit['tipo_operacion'].str.contains("Barril")) & (df_audit['codigo_maquina'] == b)]['litros'].sum()
                # Salidas: Barril -> Máquina
                salidas = df_audit[(df_audit['origen'] == b)]['litros'].sum()
                stock = entradas - salidas
                cols_b[i].metric(b, f"{stock:.1f} L", f"Ingresos: {entradas}")

            st.markdown("---")
            st.subheader("📋 Historial de Movimientos")
            d_ini = st.date_input("Ver desde el día 26", date.today() - timedelta(days=30))
            df_filtro = df_audit[df_audit['fecha'] >= str(d_ini)]
            st.dataframe(df_filtro, use_container_width=True)
            
            csv = df_filtro.to_csv(index=False, sep=';', encoding='latin-1').encode('latin-1')
            st.download_button("📥 Descargar Excel para Auditoría", csv, "auditoria_ekos.csv")
        else:
            st.info("Aún no hay datos registrados en la planilla.")
    elif pwd1: st.error("Acceso denegado 🔒")

# --- TAB 3: INFORME EJECUTIVO ---
with tab3:
    pwd2 = st.text_input("PIN de Gerencia", type="password", key="p2")
    if pwd2 == ACCESS_CODE:
        df_exec = conn.read()
        if not df_exec.empty:
            resumo = df_exec[df_exec['tipo_operacion'].str.contains("Máquina")].groupby('codigo_maquina').agg({
                'nombre_maquina': 'first',
                'fecha': 'max',
                'litros': 'sum',
                'estado_consumo': lambda x: x.iloc[-1]
            }).reset_index()
            resumo.columns = ['Código', 'Nombre', 'Ultima Carga', 'Total Litros', 'Estado']
            
            st.subheader("📊 Consumo Total por Máquina")
            st.bar_chart(resumo.set_index('Nombre')['Total Litros'])
            
            st.table(resumo)
            pdf_b = generar_pdf(resumo)
            st.download_button("📄 Descargar Reporte PDF", pdf_b, "Informe_Ekos.pdf")
    elif pwd2: st.error("Acceso denegado 🔒")
