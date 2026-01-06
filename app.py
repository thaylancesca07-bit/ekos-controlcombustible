import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN Y PARÁMETROS ---
ACCESS_CODE = "1645"
BARRILES = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

# Especificaciones de consumo (Basado en tus imágenes)
SPECS = {
    "HV-01": {"min": 18.0, "max": 23.0}, "JD-01": {"min": 6.0, "max": 7.0},
    "V-12": {"min": 7.0, "max": 9.0}, "M-03": {"min": 10.0, "max": 12.5},
    "S-03": {"min": 1.53, "max": 1.81}, "S-05": {"min": 1.42, "max": 1.81},
    "S-06": {"min": 3.3, "max": 4.0}, "S-07": {"min": 3.3, "max": 4.0},
    "S-08": {"min": 1.66, "max": 1.81},
}

VEICULOS_CADASTRO = {
    "HV-01": "Caterpilar 320D", "JD-01": "John Deere", "M-11": "N. Frontier",
    "M-17": "GM S-10", "V-12": "Valtra 180", "JD-03": "John Deere 6110",
    "MC-06": "MB Canter", "M-02": "Chevrolet - S10", "JD-02": "John Deere 6170",
    "MF-02": "Massey", "V-07": "Valmet 1580", "TM-01": "Pala Michigan",
    "JD-04": "John Deere 5090", "V-02": "Valmet 785", "V-11": "Valmet 8080",
    "M13": "Nisan Frontier (M13)", "TF01": "Ford", "MICHIGAN": "Pala Michigan",
    "S-08": "Scania Rojo", "S-05": "Scania Azul", "M-03": "GM S-10 (M-03)",
    "S-03": "Scania 113H", "S-06": "Scania P112H", "S-07": "Scania R380"
}

# --- 2. CLASE PARA PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'INFORME EJECUTIVO - CONTROL EKOS', 0, 1, 'C')
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
st.set_page_config(page_title="Combustible Control Ekos", layout="wide")

# Conexión a la Nube (Google Sheets)
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("⛽ Combustible Control Ekos")
st.markdown("<p style='font-size: 18px; color: gray; margin-top: -20px;'>powered by Excelencia Consultora - Nueva Esperanza - Canindeyu</p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["👋 Registro Personal", "🔐 Auditoría & Stock", "📊 Informe Ejecutivo"])

# --- TAB 1: REGISTRO ---
with tab1:
    st.subheader("¡Buen día! Registremos la actividad de hoy 😊")
    operacion = st.radio("¿Qué estamos haciendo? 🛠️", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
    
    with st.form("form_final", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            if "Máquina" in operacion:
                sel = st.selectbox("Selecciona la Máquina:", options=[f"{k} - {v}" for k,v in VEICULOS_CADASTRO.items()])
                cod_f = sel.split(" - ")[0]
                nom_f = VEICULOS_CADASTRO[cod_f]
                origen = st.selectbox("¿De dónde sale el combustible? ⛽", BARRILES + ["Surtidor Petrobras", "Surtidor Shell"])
            else:
                cod_f = st.selectbox("¿Qué barril vamos a llenar? 📦", options=BARRILES)
                nom_f = cod_f
                origen = st.selectbox("¿Desde qué surtidor viene? ⛽", ["Surtidor Petrobras", "Surtidor Shell"])
            
            chofer = st.text_input("Tu nombre (Chofer/Operador) 🧑‍🌾")
            resp_cargo = st.text_input("Responsable del Cargo / Encargado 👤")

        with col2:
            actividad = st.text_input("Actividad a desarrollar 🔨")
            litros = st.number_input("Cantidad de Litros 💧", min_value=0.0, step=0.1)
            lectura = st.number_input("Lectura actual del tablero (KM/H) 🔢", min_value=0.0) if "Máquina" in operacion else 0.0
            fecha = st.date_input("Fecha 📅", date.today())
        
        btn = st.form_submit_button("✅ GUARDAR REGISTRO")

    if btn:
        if not chofer or not resp_cargo or not actividad:
            st.warning("Oye, no olvides completar todos los campos. 😉")
        else:
            try:
                # Leer datos actuales de Google Sheets
                df_actual = conn.read()
                media, estado = 0.0, "N/A"
                
                # Cálculo de media y estado (Comparando con el último registro en la nube)
                if "Máquina" in operacion and not df_actual.empty:
                    last_reg = df_actual[df_actual['codigo_maquina'] == cod_f]
                    if not last_reg.empty:
                        v_ant = float(last_reg.iloc[-1]['lectura_actual'])
                        if lectura > v_ant:
                            media = (lectura - v_ant) / litros
                            if cod_f in SPECS:
                                s = SPECS[cod_f]
                                estado = "NORMAL" if s["min"] <= media <= s["max"] else "ANORMAL"

                # Nueva fila para insertar
                new_row = pd.DataFrame([{
                    "fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f,
                    "nombre_maquina": nom_f, "origen": origen, "chofer": chofer,
                    "responsable_cargo": resp_cargo, "actividad": actividad,
                    "lectura_actual": lectura, "litros": litros, "media": media, "estado_consumo": estado
                }])
                
                updated_df = pd.concat([df_actual, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.balloons()
                st.success(f"¡Excelente! Registro de {nom_f} guardado en la nube. 🚀")
            except Exception as e:
                st.error("Error al conectar con Google Sheets. Verifica los Secrets.")

# --- TAB 2: AUDITORÍA Y STOCK ---
with tab2:
    pwd1 = st.text_input("Ingrese PIN de seguridad para Auditoría", type="password", key="p1")
    if pwd1 == ACCESS_CODE:
        df_audit = conn.read()
        if not df_audit.empty:
            st.subheader("📦 Stock Actual de Barriles")
            c_b1, c_b2, c_b3, c_b4 = st.columns(4)
            cols_gui = [c_b1, c_b2, c_b3, c_b4]
            
            for i, b in enumerate(BARRILES):
                # Entradas: Operación Llenar Barril donde el destino es ese barril
                entradas = df_audit[(df_audit['tipo_operacion'].str.contains("Barril")) & (df_audit['codigo_maquina'] == b)]['litros'].sum()
                # Salidas: Cualquier operación donde el origen sea ese barril
                salidas = df_audit[(df_audit['origen'] == b)]['litros'].sum()
                stock = entradas - salidas
                cols_gui[i].metric(b, f"{stock:.1f} L", f"Entradas: {entradas}")

            st.markdown("---")
            st.subheader("📥 Exportar Datos para Excel")
            d_ini = st.date_input("Inicio (26)", date.today() - timedelta(days=30))
            d_fin = st.date_input("Fin (25)", date.today())
            
            df_filtro = df_audit[(df_audit['fecha'] >= str(d_ini)) & (df_audit['fecha'] <= str(d_fin))]
            st.dataframe(df_filtro, use_container_width=True)
            
            csv = df_filtro.to_csv(index=False, sep=';', encoding='latin-1').encode('latin-1')
            st.download_button("Descargar Planilla (.csv)", csv, f"auditoria_ekos_{d_ini}.csv")
    elif pwd1: st.error("Contraseña incorrecta 🔒")

# --- TAB 3: INFORME EJECUTIVO ---
with tab3:
    pwd2 = st.text_input("Ingrese PIN para Informe Ejecutivo", type="password", key="p2")
    if pwd2 == ACCESS_CODE:
        df_exec = conn.read()
        if not df_exec.empty:
            # Filtrar solo máquinas para el resumen
            resumo = df_exec[df_exec['tipo_operacion'].str.contains("Máquina")].groupby('codigo_maquina').agg({
                'nombre_maquina': 'first',
                'fecha': 'max',
                'litros': 'sum',
                'estado_consumo': lambda x: x.iloc[-1]
            }).reset_index()
            resumo.columns = ['Código', 'Nombre', 'Ultima Carga', 'Total Litros', 'Estado']
            
            st.subheader("📊 Consumo Total de Litros por Máquina")
            st.bar_chart(resumo.set_index('Nombre')['Total Litros'])
            
            st.subheader("📋 Resumen de Auditoría de Flota")
            st.table(resumo)
            
            pdf_file = generar_pdf(resumo)
            st.download_button("📄 Descargar Reporte PDF", pdf_file, "Informe_Ejecutivo_Ekos.pdf")
    elif pwd2: st.error("Contraseña incorrecta 🔒")
