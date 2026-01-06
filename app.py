import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

# URL del Script de Google (Pestaña Registro)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwnPU3LdaHqrNO4bTsiBMKmm06ZSm3dUbxb5OBBnHBQOHRSuxcGv_MK4jWNHsrAn3M/exec"

# ID de la Planilla Oficial
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

ACCESS_CODE_MAESTRO = "1645"
TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]

# MAPEO DE COMBUSTIBLES PETROBRAS
MAPA_COMBUSTIBLE = {
    "4002147 - Diesel EURO 5 S-50": "Diesel S500",
    "4002151 - NAFTA GRID 95": "Nafta",
    "4001812 - Diesel podium S-10 gr.": "Diesel Podium"
}

# MAPEO DE ENCARGADOS (Auditoria con acceso total)
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

tab1, tab2, tab3, tab4 = st.tabs(["👋 Registro Personal", "🔐 Auditoría & Stock", "📊 Informe Grafico", "🔍 Confirmación de Datos"])

# --- TAB 1: REGISTRO ---
with tab1:
    st.subheader("🔑 Acceso de Encargado")
    c_auth1, c_auth2 = st.columns(2)
    with c_auth1: encargado_sel = st.selectbox("Encargado:", options=list(ENCARGADOS_DATA.keys()))
    with c_auth2: pwd_input = st.text_input("Contraseña:", type="password")

    if pwd_input == ENCARGADOS_DATA[encargado_sel]["pwd"]:
        operacion = st.radio("Operación:", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
        
        if encargado_sel == "Auditoria":
            op_barril, op_origen = BARRILES_LISTA, BARRILES_LISTA + ["Surtidor Petrobras", "Surtidor Shell"]
        else:
            mi_barril = ENCARGADOS_DATA[encargado_sel]["barril"]
            op_barril, op_origen = [mi_barril], [mi_barril, "Surtidor Petrobras", "Surtidor Shell"]

        c_f1, c_f2 = st.columns(2)
        with c_f1:
            if "Máquina" in operacion:
                sel_m = st.selectbox("Máquina:", options=[f"{k} - {v['nombre']}" for k, v in FLOTA.items()])
                cod_f, nom_f, unidad = sel_m.split(" - ")[0], FLOTA[sel_m.split(" - ")[0]]['nombre'], FLOTA[sel_m.split(" - ")[0]]['unidad']
                origen = st.selectbox("Origen:", op_origen)
            else:
                cod_f = st.selectbox("Barril:", options=op_barril)
                nom_f, unidad, origen = cod_f, "Litros", st.selectbox("Surtidor:", ["Surtidor Petrobras", "Surtidor Shell"])
        
        with c_f2: tipo_comb = st.selectbox("Combustible:", TIPOS_COMBUSTIBLE)

        with st.form("form_final_ekos", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                chofer, fecha, act = st.text_input("Chofer"), st.date_input("Fecha", date.today()), st.text_input("Actividad")
            with col2:
                lts = st.number_input("Litros", min_value=0.0, step=0.1)
                lect = st.number_input(f"Lectura ({unidad})", min_value=0.0) if "Máquina" in operacion else 0.0
            
            submit_registro = st.form_submit_button("✅ GUARDAR REGISTRO")

            if submit_registro:
                if not chofer or not act:
                    st.warning("⚠️ Completa los campos.")
                else:
                    error_lectura = False
                    media_calc = 0.0
                    
                    # ----------------------------------------------------
                    # VALIDACIÓN DE LECTURA Y CÁLCULO DE PROMEDIO
                    # ----------------------------------------------------
                    if "Máquina" in operacion and lect > 0:
                        try:
                            # 1. Leer planilla para buscar historial
                            df_hist = pd.read_csv(SHEET_URL)
                            # 2. Filtrar solo esta máquina
                            hist_maq = df_hist[df_hist['codigo_maquina'] == cod_f]
                            
                            if not hist_maq.empty:
                                # Obtener la máxima lectura registrada hasta hoy
                                ult_lectura = hist_maq['lectura_actual'].max()
                                
                                # VALIDACIÓN: Si la nueva lectura es menor, BLOQUEAR.
                                if lect < ult_lectura:
                                    st.error(f"⛔ ERROR CRÍTICO: La lectura ingresada ({lect}) es MENOR a la última registrada ({ult_lectura}). No se puede guardar.")
                                    error_lectura = True
                                else:
                                    # CÁLCULO DE PROMEDIO (Diferencia / Litros)
                                    recorrido = lect - ult_lectura
                                    if lts > 0:
                                        media_calc = recorrido / lts
                            else:
                                # Primer registro de la máquina, media es 0
                                media_calc = 0.0
                        except Exception as e:
                            # Si falla la lectura de la base (ej. vacía), permitimos guardar con media 0
                            # pero avisamos (opcional, aquí lo dejamos pasar para no trabar si es el primer uso)
                            media_calc = 0.0
                    # ----------------------------------------------------

                    if not error_lectura:
                        payload = {
                            "fecha": str(fecha), 
                            "tipo_operacion": operacion, 
                            "codigo_maquina": cod_f, 
                            "nombre_maquina": nom_f, 
                            "origen": origen, 
                            "chofer": chofer, 
                            "responsable_cargo": encargado_sel, 
                            "actividad": act, 
                            "lectura_actual": lect, 
                            "litros": lts, 
                            "tipo_combustible": tipo_comb,
                            "media": media_calc # <-- AQUÍ SE ENVÍA EL PROMEDIO CALCULADO
                        }
                        try:
                            r = requests.post(SCRIPT_URL, json=payload)
                            if r.status_code == 200: 
                                st.balloons()
                                st.success(f"¡Guardado, Excelente Trabajo! Promedio calculado: {media_calc:.2f}")
                            else: 
                                st.error("Error en permisos del Script.")
                        except: 
                            st.error("Error de conexión.")
                            
    elif pwd_input: st.error("❌ Contraseña incorrecta.")

# --- TAB 2: AUDITORÍA & STOCK ---
with tab2:
    if st.text_input("PIN Maestro Auditoría", type="password", key="p_aud") == ACCESS_CODE_MAESTRO:
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                if 'fecha' in df.columns:
                    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
                    st.subheader("📦 Verificación de Stock")
                    tipo_audit = st.radio("¿Qué combustible desea verificar?", TIPOS_COMBUSTIBLE, horizontal=True)
                    
                    cb = st.columns(4)
                    for i, b in enumerate(BARRILES_LISTA):
                        ent = df[(df['codigo_maquina'] == b) & (df['tipo_combustible'] == tipo_audit)]['litros'].sum()
                        sal = df[(df['origen'] == b) & (df['tipo_combustible'] == tipo_audit)]['litros'].sum()
                        cb[i].metric(b, f"{ent - sal:.1f} L", f"Entradas: {ent:.0f}")

                    st.markdown("---")
                    st.subheader("📋 Historial Completo")
                    # Mostrar columna Media también
                    cols_to_show = ['fecha', 'nombre_maquina', 'litros', 'lectura_actual', 'media', 'tipo_combustible', 'responsable_cargo']
                    # Filtramos columnas que existen para evitar error si 'media' aun no existe en viejos registros
                    cols_final = [c for c in cols_to_show if c in df.columns]
                    st.dataframe(df[cols_final].sort_values(by='fecha', ascending=False), use_container_width=True)
                else:
                    st.warning("⚠️ Faltan encabezados en la planilla.")
            else: st.info("Planilla vacía.")
        except Exception as e: 
            st.error(f"Error de base de datos: {e}")

# --- TAB 3: INFORME GRAFICO ---
with tab3:
    if st.text_input("PIN Gerencia", type="password", key="p_ger") == ACCESS_CODE_MAESTRO:
        try:
            df_graph = pd.read_csv(SHEET_URL)
            if not df_graph.empty:
                st.subheader("📊 Consumo Total por Máquina (Litros)")
                df_maq_only = df_graph[df_graph['tipo_operacion'].str.contains("Máquina", na=False)]
                if not df_maq_only.empty:
                    consumo_resumen = df_maq_only.groupby('nombre_maquina')['litros'].sum()
                    st.bar_chart(consumo_resumen)
                    
                    st.subheader("⛽ Consumo por Tipo de Combustible")
                    comb_resumen = df_maq_only.groupby('tipo_combustible')['litros'].sum()
                    st.bar_chart(comb_resumen)
                    
                    pdf_b = generar_pdf(df_maq_only)
                    st.download_button("📄 Descargar Reporte PDF", pdf_b, "Informe_Ekos.pdf")
                else:
                    st.info("No hay datos de máquinas para graficar.")
            else: st.info("No hay datos registrados aún.")
        except Exception as e:
            st.error(f"Error al generar gráficos: {e}")

# --- TAB 4: CONFIRMACIÓN DE DATOS ---
with tab4:
    if st.text_input("PIN Conciliación", type="password", key="p_con") == ACCESS_CODE_MAESTRO:
        st.subheader("🔍 Lado a Lado: Ekos vs Petrobras")
        archivo_p = st.file_uploader("Subir Excel Petrobras", type=["xlsx"])
        if archivo_p:
            try:
                df_p = pd.read_excel(archivo_p, usecols=[5, 10, 14, 15], names=["Fecha", "Responsable", "Comb_Original", "Litros"])
                df_p['Comb_Ekos'] = df_p['Comb_Original'].map(MAPA_COMBUSTIBLE).fillna("Otros")
                st.dataframe(df_p.head())
                if st.button("🚀 SINCRONIZAR"):
                    for _, r in df_p.iterrows():
                        p = {"fecha": str(r['Fecha']), "tipo_operacion": "FACTURA PETROBRAS", "codigo_maquina": "PETRO-F", "nombre_maquina": "Factura", "origen": "Surtidor", "chofer": "N/A", "responsable_cargo": str(r['Responsable']), "actividad": "Conciliación", "lectura_actual": 0, "litros": float(r['Litros']), "tipo_combustible": r['Comb_Ekos'], "fuente_dato": "PETROBRAS_OFFICIAL"}
                        requests.post(SCRIPT_URL, json=p)
                    st.success("✅ Sincronizado.")
            except Exception as e: st.error(f"Error: {e}")

