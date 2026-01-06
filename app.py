import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF

# --- CONFIGURACIÓN DE PARÁMETROS ---
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

ACCESS_CODE = "1645"

st.set_page_config(page_title="Combustible Control Ekos", layout="wide")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("⛽ Combustible Control Ekos")
st.markdown("<p style='font-size: 18px; color: gray; margin-top: -20px;'>powered by Excelencia Consultora - Nueva Esperanza - Canindeyu</p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["👋 Registro Personal", "🔐 Auditoria", "📈 Informe Ejecutivo"])

# --- REGISTRO ---
with tab1:
    st.subheader("¡Hola! Registremos los datos de hoy 😊")
    operacion = st.radio("¿Qué estamos haciendo? 🛠️", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
    
    opciones = {f"{k} - {v}": k for k, v in VEICULOS_CADASTRO.items()} if "Máquina" in operacion else {"Barril Diego": "Barril Diego", "Barril Juan": "Barril Juan", "Barril Jonatan": "Barril Jonatan", "Barril Cesar": "Barril Cesar"}
    seleccion = st.selectbox("Selecciona equipo o barril:", options=list(opciones.keys()))
    cod_f = opciones[seleccion]
    nom_f = VEICULOS_CADASTRO.get(cod_f, cod_f)

    with st.form("form_nube", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            origen = st.selectbox("¿Origen del combustible? ⛽", ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar", "Surtidor Petrobras", "Surtidor Shell"])
            chofer = st.text_input("Chofer / Operador 🧑‍🌾")
            resp_cargo = st.text_input("Responsable del Cargo 👤")
        with c2:
            actividad = st.text_input("Actividad 🔨")
            litros = st.number_input("Litros 💧", min_value=0.0)
            lectura = st.number_input("Lectura (KM/H) 🔢", min_value=0.0) if "Máquina" in operacion else 0.0
            fecha = st.date_input("Fecha 📅", date.today())
        
        btn = st.form_submit_button("✅ GUARDAR REGISTRO")

    if btn:
        if not chofer or not resp_cargo:
            st.warning("Completa los nombres, por favor. 😉")
        else:
            df_actual = conn.read()
            # Lógica de guardado simplificada para la nube
            new_data = pd.DataFrame([{
                "fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f,
                "nombre_maquina": nom_f, "origen": origen, "chofer": chofer,
                "responsable_cargo": resp_cargo, "actividad": actividad,
                "lectura_actual": lectura, "litros": litros, "media": 0.0, "estado_consumo": "N/A"
            }])
            updated_df = pd.concat([df_actual, new_data], ignore_index=True)
            conn.update(data=updated_df)
            st.balloons()
            st.success("¡Datos guardados en la nube! 🚀")

# (Las pestañas de Auditoría e Informe se mantienen igual, leyendo de 'conn.read()')