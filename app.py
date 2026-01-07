import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

# URL del Script de Google
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwnPU3LdaHqrNO4bTsiBMKmm06ZSm3dUbxb5OBBnHBQOHRSuxcGv_MK4jWNHsrAn3M/exec"

# ID de la Planilla Oficial
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

ACCESS_CODE_MAESTRO = "1645"
TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]
MARGEN_TOLERANCIA = 0.20 # 20% de margen

# MAPEO DE COMBUSTIBLES PETROBRAS
MAPA_COMBUSTIBLE = {
    "4002147 - Diesel EURO 5 S-50": "Diesel S500",
    "4002151 - NAFTA GRID 95": "Nafta",
    "4001812 - Diesel podium S-10 gr.": "Diesel Podium"
}

# MAPEO DE ENCARGADOS
ENCARGADOS_DATA = {
    "Juan Britez": {"pwd": "jb2026", "barril": "Barril Juan"},
    "Diego Bordon": {"pwd": "db2026", "barril": "Barril Diego"},
    "Jonatan Vargas": {"pwd": "jv2026", "barril": "Barril Jonatan"},
    "Cesar Cabañas": {"pwd": "cc2026", "barril": "Barril Cesar"},
    "Auditoria": {"pwd": "1645", "barril": "Acceso Total"}
}

BARRILES_LISTA = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

# --- FLOTA CON PROMEDIOS IDEALES ---
# Ajusta estos valores a la realidad
FLOTA = {
    "HV-01": {"nombre": "Caterpilar 320D", "unidad": "Horas", "ideal": 18.0}, 
    "JD-01": {"nombre": "John Deere", "unidad": "Horas", "ideal": 15.0},
    "M-11": {"nombre": "N. Frontier", "unidad": "KM", "ideal": 9.0},
    "M-17": {"nombre": "GM S-10", "unidad": "KM", "ideal": 10.0},
    "V-12": {"nombre": "Valtra 180", "unidad": "Horas", "ideal": 12.0},
    "JD-03": {"nombre": "John Deere 6110", "unidad": "Horas", "ideal": 10.0},
    "MC-06": {"nombre": "MB Canter", "unidad": "KM", "ideal": 6.0},
    "M-02": {"nombre": "Chevrolet - S10", "unidad": "KM", "ideal": 8.0},
    "JD-02": {"nombre": "John Deere 6170", "unidad": "Horas", "ideal": 16.0},
    "MF-02": {"nombre": "Massey", "unidad": "Horas", "ideal": 9.0},
    "V-07": {"nombre": "Valmet 1580", "unidad": "Horas", "ideal": 11.0},
    "TM-01": {"nombre": "Pala Michigan", "unidad": "Horas", "ideal": 14.0},
    "JD-04": {"nombre": "John Deere 5090", "unidad": "Horas", "ideal": 8.0},
    "V-02": {"nombre": "Valmet 785", "unidad": "Horas", "ideal": 7.0},
    "V-11": {"nombre": "Valmet 8080", "unidad": "Horas", "ideal": 9.5},
    "M13": {"nombre": "Nisan Frontier (M13)", "unidad": "Horas", "ideal": 5.0},
    "TF01": {"nombre": "Ford", "unidad": "Horas", "ideal": 0.0},
    "MICHIGAN": {"nombre": "Pala Michigan", "unidad": "Horas", "ideal": 14.0},
    "S-08": {"nombre": "Scania Rojo", "unidad": "KM", "ideal": 2.2},
    "S-05": {"nombre": "Scania Azul", "unidad": "KM", "ideal": 2.4},
    "M-03": {"nombre": "GM S-10 (M-03)", "unidad": "KM", "ideal": 8.5},
    "S-03": {"nombre": "Scania 113H", "unidad": "KM", "ideal": 2.3},
    "S-06": {"nombre": "Scania P112H", "unidad": "Horas", "ideal": 0.0},
    "S-07": {"nombre": "Scania R380", "unidad": "Horas", "ideal": 0.0},
    "O-01": {"nombre": "Otros", "unidad": "Horas", "ideal": 0.0}
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
        try:
            litros_val = float(row['litros'])
        except:
            litros_val = 0.0
            
        pdf.cell(w[0], 10, str(row['codigo_maquina']), 1)
        pdf.cell(w[1], 10, str(row['nombre_maquina']), 1)
        pdf.cell(w[2], 10, str(row['fecha']), 1)
        pdf.cell(w[3], 10, f"{litros_val:.1f}", 1)
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
                    
                    if "Máquina" in operacion and lect > 0:
                        try:
                            df_hist = pd.read_csv(SHEET_URL)
                            df_hist.columns = df_hist.columns.str.strip().str.lower()
                            # LIMPIEZA DE DATOS (Prevención de errores)
                            cols_num = ['lectura_actual', 'litros', 'media']
                            for c in cols_num:
                                if c in df_hist.columns:
                                    df_hist[c] = pd.to_numeric(df_hist[c], errors='coerce').fillna(0)

                            hist_maq = df_hist[df_hist['codigo_maquina'] == cod_f]
                            if not hist_maq.empty:
                                ult_lectura = hist_maq['lectura_actual'].max()
                                if lect < ult_lectura:
                                    st.error(f"⛔ ERROR: La lectura ({lect}) es MENOR a la anterior ({ult_lectura}).")
                                    error_lectura = True
                                else:
                                    recorrido = lect - ult_lectura
                                    if lts > 0: media_calc = recorrido / lts
                        except: pass 

                    if not error_lectura:
                        payload = {"fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f, "nombre_maquina": nom_f, "origen": origen, "chofer": chofer, "responsable_cargo": encargado_sel, "actividad": act, "lectura_actual": lect, "litros": lts, "tipo_combustible": tipo_comb, "media": media_calc}
                        try:
                            r = requests.post(SCRIPT_URL, json=payload)
                            if r.status_code == 200: st.balloons(); st.success(f"¡Guardado! Promedio calculado: {media_calc:.2f}")
                            else: st.error("Error en permisos.")
                        except: st.error("Error de conexión.")
    elif pwd_input: st.error("❌ Contraseña incorrecta.")

# --- TAB 2: AUDITORÍA & STOCK ---
with tab2:
    if st.text_input("PIN Maestro Auditoría", type="password", key="p_aud") == ACCESS_CODE_MAESTRO:
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                if len(df.columns) > 0 and "html" in str(df.columns[0]).lower():
                    st.error("🚨 ERROR DE PERMISOS. Pon la planilla como 'Pública - Lector'.")
                else:
                    df.columns = df.columns.str.strip().str.lower()
                    
                    # LIMPIEZA AUTOMÁTICA DE DATOS
                    cols_num = ['litros', 'media', 'lectura_actual']
                    for c in cols_num:
                        if c in df.columns:
                            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

                    if 'fecha' in df.columns:
                        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
                        
                        st.subheader("📦 Verificación de Stock (Total Histórico)")
                        tipo_audit = st.radio("¿Qué combustible desea verificar?", TIPOS_COMBUSTIBLE, horizontal=True)
                        
                        cb = st.columns(4)
                        for i, b in enumerate(BARRILES_LISTA):
                            ent = df[(df['codigo_maquina'] == b) & (df['tipo_combustible'] == tipo_audit)]['litros'].sum()
                            sal = df[(df['origen'] == b) & (df['tipo_combustible'] == tipo_audit)]['litros'].sum()
                            cb[i].metric(b, f"{ent - sal:.1f} L", f"Entradas: {ent:.0f}")

                        st.markdown("---")
                        st.subheader("📋 Historial de Movimientos")
                        c_date1, c_date2 = st.columns(2)
                        with c_date1: f_ini = st.date_input("Fecha Inicio:", date.today() - timedelta(days=30))
                        with c_date2: f_fin = st.date_input("Fecha Fin:", date.today())
                        
                        mask = (df['fecha'].dt.date >= f_ini) & (df['fecha'].dt.date <= f_fin)
                        df_filtrado = df.loc[mask]
                        
                        cols_finales = [c for c in ['fecha', 'nombre_maquina', 'origen', 'litros', 'tipo_combustible', 'responsable_cargo', 'media', 'lectura_actual'] if c in df.columns]
                        st.dataframe(df_filtrado[cols_finales].sort_values(by='fecha', ascending=False), use_container_width=True)
                    else: st.warning("⚠️ Faltan encabezados en la planilla.")
            else: st.info("Planilla vacía.")
        except Exception as e: st.error(f"Error técnico: {e}")

# --- TAB 3: INFORME GRAFICO AVANZADO ---
with tab3:
    if st.text_input("PIN Gerencia", type="password", key="p_ger") == ACCESS_CODE_MAESTRO:
        try:
            df_graph = pd.read_csv(SHEET_URL)
            df_graph.columns = df_graph.columns.str.strip().str.lower()
            
            # --- LIMPIEZA CRÍTICA PARA EVITAR ERROR 'int' + 'str' ---
            cols_num = ['litros', 'media']
            for c in cols_num:
                if c in df_graph.columns:
                    df_graph[c] = pd.to_numeric(df_graph[c], errors='coerce').fillna(0)
            
            if not df_graph.empty and 'fecha' in df_graph.columns:
                df_graph['fecha'] = pd.to_datetime(df_graph['fecha'], errors='coerce')
                
                st.subheader("📊 Análisis de Consumo)")
                
                c_g1, c_g2 = st.columns(2)
                with c_g1: g_ini = st.date_input("Desde:", date.today() - timedelta(days=30), key="g_ini_r")
                with c_g2: g_fin = st.date_input("Hasta:", date.today(), key="g_fin_r")
                
                mask_g = (df_graph['fecha'].dt.date >= g_ini) & (df_graph['fecha'].dt.date <= g_fin)
                df_g = df_graph.loc[mask_g]
                
                df_maq = df_g[df_g['tipo_operacion'].str.contains("Máquina", na=False)]
                
                if not df_maq.empty:
                    resumen_data = []
                    maquinas_activas = df_maq['codigo_maquina'].unique()
                    
                    for cod in maquinas_activas:
                        if cod in FLOTA:
                            datos_maq = df_maq[df_maq['codigo_maquina'] == cod]
                            total_litros = datos_maq['litros'].sum()
                            
                            datos_maq['recorrido_est'] = datos_maq['media'] * datos_maq['litros']
                            total_recorrido = datos_maq['recorrido_est'].sum()
                            
                            unidad = FLOTA[cod]['unidad']
                            ideal = FLOTA[cod].get('ideal', 0.0)
                            
                            promedio_real = 0.0
                            metric_label = "Unid/L"
                            
                            if total_litros > 0:
                                if unidad == 'KM':
                                    promedio_real = total_recorrido / total_litros
                                    metric_label = "KM/L"
                                else: 
                                    if total_recorrido > 0:
                                        promedio_real = total_litros / total_recorrido 
                                    metric_label = "L/Hora"
                            
                            estado = "N/A"
                            if ideal > 0:
                                margen = ideal * MARGEN_TOLERANCIA
                                min_ok = ideal - margen
                                max_ok = ideal + margen
                                
                                if min_ok <= promedio_real <= max_ok:
                                    estado = "✅ Normal"
                                else:
                                    estado = "⚠️ Fuera de Rango"

                            resumen_data.append({
                                "Máquina": FLOTA[cod]['nombre'],
                                "Unidad": unidad,
                                "Litros Usados": round(total_litros, 2),
                                f"Promedio Real ({metric_label})": round(promedio_real, 2),
                                f"Promedio Ideal": ideal,
                                "Estado": estado
                            })
                    
                    st.dataframe(pd.DataFrame(resumen_data), use_container_width=True)
                    st.caption(f"Nota: Margen de tolerancia +/- {int(MARGEN_TOLERANCIA*100)}%")
                    
                    st.markdown("---")
                    st.subheader("Gráficos de Consumo")
                    st.bar_chart(df_maq.groupby('nombre_maquina')['litros'].sum())
                    
                    pdf_b = generar_pdf(df_maq)
                    st.download_button("📄 Descargar Reporte PDF", pdf_b, "Informe_Ekos.pdf")
                else: st.info("No hay movimientos en este rango.")
            else: st.warning("Sin datos.")
        except Exception as e: st.error(f"Error en reporte: {e}")

# --- TAB 4: CONFIRMACIÓN DE DATOS ---
with tab4:
    if st.text_input("PIN Conciliación", type="password", key="p_con") == ACCESS_CODE_MAESTRO:
        st.subheader("🔍 Lado a Lado: Ekos vs Petrobras")
        archivo_p = st.file_uploader("Subir Archivo Petrobras (Excel o CSV)", type=["xlsx", "csv"])
        if archivo_p:
            try:
                if archivo_p.name.endswith('.csv'):
                    df_p = pd.read_csv(archivo_p, header=0, usecols=[5, 12, 14, 15], names=["Fecha", "Responsable", "Comb_Original", "Litros"])
                else:
                    df_p = pd.read_excel(archivo_p, usecols=[5, 12, 14, 15], names=["Fecha", "Responsable", "Comb_Original", "Litros"])

                df_p['Comb_Ekos'] = df_p['Comb_Original'].map(MAPA_COMBUSTIBLE).fillna("Otros")
                st.dataframe(df_p.head())
                if st.button("🚀 SINCRONIZAR"):
                    for _, r in df_p.iterrows():
                        p = {"fecha": str(r['Fecha']), "tipo_operacion": "FACTURA PETROBRAS", "codigo_maquina": "PETRO-F", "nombre_maquina": "Factura", "origen": "Surtidor", "chofer": "N/A", "responsable_cargo": str(r['Responsable']), "actividad": "Conciliación", "lectura_actual": 0, "litros": float(r['Litros']), "tipo_combustible": r['Comb_Ekos'], "fuente_dato": "PETROBRAS_OFFICIAL"}
                        requests.post(SCRIPT_URL, json=p)
                    st.success("✅ Sincronizado.")
            except Exception as e: st.error(f"Error: {e}")
