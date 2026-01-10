import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import io
import tempfile
import time
import base64
from datetime import date, datetime, timedelta
from fpdf import FPDF
from docx import Document
from docx.shared import Inches

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

# URL DEL SCRIPT DE GOOGLE
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwnPU3LdaHqrNO4bTsiBMKmm06ZSm3dUbxb5OBBnHBQOHRSuxcGv_MK4jWNHsrAn3M/exec"
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

ACCESS_CODE_MAESTRO = "1645"
TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]
MARGEN_TOLERANCIA = 0.20 

MAPA_COMBUSTIBLE = {
    "4002147 - Diesel EURO 5 S-50": "Diesel S500",
    "4002151 - NAFTA GRID 95": "Nafta",
    "4001812 - Diesel podium S-10 gr.": "Diesel Podium"
}

ENCARGADOS_DATA = {
    "Juan Britez": {"pwd": "jb2026", "barril": "Barril Juan"},
    "Diego Bordon": {"pwd": "db2026", "barril": "Barril Diego"},
    "Jonatan Vargas": {"pwd": "jv2026", "barril": "Barril Jonatan"},
    "Cesar Cabañas": {"pwd": "cc2026", "barril": "Barril Cesar"},
    "Auditoria": {"pwd": "1645", "barril": "Acceso Total"}
}
BARRILES_LISTA = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

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

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'INFORME EKOS', 0, 1, 'C')
        self.ln(5)

def clean_text(text): return str(text).encode('latin-1', 'replace').decode('latin-1')

def generar_excel(df, sheet_name='Datos'):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def generar_pdf_con_graficos(df, titulo, inc_graf=False, tipo="barras"):
    pdf = PDF(); pdf.add_page(); pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, clean_text(titulo), 0, 1, 'L'); pdf.ln(5)
    pdf.set_font('Arial', '', 8)
    for i, col in enumerate(df.columns): pdf.cell(30, 10, clean_text(col), 1)
    pdf.ln()
    for _, row in df.iterrows():
        for col in df.columns: pdf.cell(30, 10, clean_text(str(row[col])), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'replace')

def generar_word(df, titulo):
    doc = Document(); doc.add_heading(titulo, 0)
    if not df.empty:
        t = doc.add_table(rows=1, cols=len(df.columns)); t.style = 'Table Grid'
        for i, col in enumerate(df.columns): t.rows[0].cells[i].text = str(col)
        for _, row in df.iterrows():
            row_cells = t.add_row().cells
            for i, item in enumerate(row): row_cells[i].text = str(item)
    b = io.BytesIO(); doc.save(b); return b.getvalue()

# --- INTERFAZ ---
st.title("⛽ Ekos Forestal / Control de combustible")
st.markdown("""<p style='font-size: 18px; color: gray; margin-top: -20px;'>Desenvolvido por Excelencia Consultora en Paraguay 🇵🇾 <span style='font-size: 14px; font-style: italic;'>creado por Thaylan Cesca</span></p><hr>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👋 Registro Personal", "🔐 Auditoría", "🔍 Verificación", "🚜 Máquina por Máquina"])

with tab1: # REGISTRO
    st.subheader("🔑 Acceso de Encargado")
    c_auth1, c_auth2 = st.columns(2)
    with c_auth1: encargado_sel = st.selectbox("Encargado:", list(ENCARGADOS_DATA.keys()))
    with c_auth2: pwd_input = st.text_input("Contraseña:", type="password")
    if pwd_input == ENCARGADOS_DATA[encargado_sel]["pwd"]:
        operacion = st.radio("Operación:", ["Cargar una Máquina 🚜", "Llenar un Barril 📦"])
        if encargado_sel == "Auditoria": op_barril, op_origen = BARRILES_LISTA, BARRILES_LISTA + ["Surtidor Petrobras", "Surtidor Shell"]
        else: mi_barril = ENCARGADOS_DATA[encargado_sel]["barril"]; op_barril, op_origen = [mi_barril], [mi_barril, "Surtidor Petrobras", "Surtidor Shell"]
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            if "Máquina" in operacion:
                sel_m = st.selectbox("Máquina:", [f"{k} - {v['nombre']}" for k, v in FLOTA.items()])
                cod_f, nom_f, unidad = sel_m.split(" - ")[0], FLOTA[sel_m.split(" - ")[0]]['nombre'], FLOTA[sel_m.split(" - ")[0]]['unidad']
                origen = st.selectbox("Origen:", op_origen)
            else: cod_f = st.selectbox("Barril:", op_barril); nom_f, unidad, origen = cod_f, "Litros", st.selectbox("Surtidor:", ["Surtidor Petrobras", "Surtidor Shell"])
        with c_f2: tipo_comb = st.selectbox("Combustible:", TIPOS_COMBUSTIBLE)
        
        with st.form("f_reg", clear_on_submit=True):
            c1, c2 = st.columns(2)
            chofer = c1.text_input("Chofer"); fecha = c1.date_input("Fecha", date.today()); act = c1.text_input("Actividad")
            lts = c2.number_input("Litros", min_value=0.0, step=0.1)
            
            if "Máquina" in operacion:
                lect = c2.number_input(f"Lectura ({unidad})", min_value=0.0)
            else:
                lect = 0.0

            st.markdown("---")
            foto = st.file_uploader("📸 Foto Evidencia (Opcional)", type=["jpg", "png", "jpeg"])

            if st.form_submit_button("✅ GUARDAR"):
                if not chofer or not act: st.warning("Completa todo.")
                else:
                    mc = 0.0
                    try: 
                        if "Máquina" in operacion and lect > 0:
                            df_h = pd.read_csv(SHEET_URL); df_h.columns = df_h.columns.str.strip().str.lower()
                            if 'lectura_actual' in df_h.columns:
                                df_h['lectura_actual'] = pd.to_numeric(df_h['lectura_actual'], errors='coerce').fillna(0)
                                ult = df_h[df_h['codigo_maquina'] == cod_f]['lectura_actual'].max()
                                if lect > ult and lts > 0: mc = (lect - ult) / lts
                    except: pass
                    
                    img_str, img_name, img_mime = "", "", ""
                    if foto is not None:
                        try:
                            img_bytes = foto.read()
                            img_str = base64.b64encode(img_bytes).decode('utf-8')
                            img_name = f"EVIDENCIA_{fecha}_{encargado_sel}.jpg"
                            img_mime = foto.type
                        except: pass

                    pl = {
                        "fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f, "nombre_maquina": nom_f, 
                        "origen": origen, "chofer": chofer, "responsable_cargo": encargado_sel, "actividad": act, 
                        "lectura_actual": lect, "litros": lts, "tipo_combustible": tipo_comb, "media": mc,
                        "estado_conciliacion": "N/A", "fuente_dato": "APP_MANUAL",
                        "imagen_base64": img_str, "nombre_archivo": img_name, "mime_type": img_mime
                    }
                    try: requests.post(SCRIPT_URL, json=pl); st.success("Guardado.")
                    except: st.error("Error conexión.")

with tab2: # AUDITORÍA (LÓGICA MATEMÁTICA CORREGIDA)
    if st.text_input("PIN Auditoría", type="password", key="p1") == ACCESS_CODE_MAESTRO:
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                df.columns = df.columns.str.strip().str.lower()
                for c in ['litros', 'media', 'lectura_actual']:
                    if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
                df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', dayfirst=True)
                
                st.subheader("📦 Stock Actual")
                ta = st.radio("Combustible:", TIPOS_COMBUSTIBLE, horizontal=True)
                cols = st.columns(4)
                
                for i, b in enumerate(BARRILES_LISTA):
                    ent = df[(df['codigo_maquina'] == b) & (df['tipo_combustible'] == ta)]['litros'].sum()
                    sal = df[(df['origen'] == b) & (df['tipo_combustible'] == ta)]['litros'].sum()
                    cols[i].metric(label=f"🛢️ {b}", value=f"{ent - sal:.1f} L")
                
                st.markdown("---"); st.subheader("📅 Historial")
                c1, c2 = st.columns(2); d1 = c1.date_input("Desde", date.today()-timedelta(30)); d2 = c2.date_input("Hasta", date.today())
                dff = df[(df['fecha'].dt.date >= d1) & (df['fecha'].dt.date <= d2)]
                
                if not dff.empty:
                    st.subheader("📋 Detalle")
                    cols_ver = ['fecha','nombre_maquina','origen','litros','tipo_combustible','responsable_cargo']
                    st.dataframe(dff[cols_ver].sort_values(by='fecha', ascending=False).style.format({"litros": "{:.1f}"}), use_container_width=True)
                    
                    st.subheader("📊 Rendimiento General (Calculado por Rango)")
                    if 'tipo_operacion' in dff.columns:
                        df_maq = dff[dff['tipo_operacion'].astype(str).str.contains("Máquina", na=False)]
                        if not df_maq.empty:
                            res = []
                            for cod in df_maq['codigo_maquina'].unique():
                                if cod in FLOTA:
                                    dm = df_maq[df_maq['codigo_maquina'] == cod]
                                    
                                    # NUEVA LÓGICA DE CÁLCULO
                                    # 1. Total Litros en el periodo
                                    l_total = dm['litros'].sum()
                                    
                                    # 2. Recorrido Real = Max Lectura - Min Lectura
                                    lect_max = dm['lectura_actual'].max()
                                    lect_min = dm['lectura_actual'].min()
                                    rec_real = lect_max - lect_min
                                    
                                    # 3. Litros Ajustados (Para el promedio, quitamos la primera carga del periodo
                                    #    porque su consumo corresponde al periodo anterior no registrado aquí)
                                    #    Si hay solo 1 registro, usamos sus litros directos.
                                    if len(dm) > 1:
                                        # Ordenar por lectura y quitar el primero
                                        dm_sorted = dm.sort_values('lectura_actual')
                                        l_ajustados = dm_sorted.iloc[1:]['litros'].sum()
                                    else:
                                        l_ajustados = l_total # Fallback para 1 solo dato

                                    # Variables separadas
                                    km_total = 0.0
                                    hr_total = 0.0
                                    prom_kml = 0.0
                                    prom_lh = 0.0
                                    
                                    # Asignación por tipo
                                    if FLOTA[cod]['unidad'] == 'KM':
                                        km_total = rec_real
                                        if l_ajustados > 0: prom_kml = rec_real / l_ajustados
                                    else:
                                        hr_total = rec_real
                                        if rec_real > 0: prom_lh = l_ajustados / rec_real # Litros / Horas
                                    
                                    res.append({
                                        "Máquina": FLOTA[cod]['nombre'],
                                        "Litros Totales": round(l_total, 1),
                                        "Total KM": round(km_total, 1),
                                        "Total Horas": round(hr_total, 1),
                                        "Promedio (Km/L)": round(prom_kml, 2),
                                        "Promedio (L/H)": round(prom_lh, 2)
                                    })
                            
                            df_res = pd.DataFrame(res)
                            
                            st.dataframe(df_res.style.format({
                                "Litros Totales": "{:.1f}",
                                "Total KM": "{:.1f}",
                                "Total Horas": "{:.1f}",
                                "Promedio (Km/L)": "{:.2f}",
                                "Promedio (L/H)": "{:.2f}"
                            }), use_container_width=True)
                            
                            st.bar_chart(df_maq.groupby('nombre_maquina')['litros'].sum())
                            
                            st.markdown("### 📥 Descargas")
                            c1, c2, c3 = st.columns(3)
                            c1.download_button("Excel", generar_excel(dff[cols_ver]), "Historial.xlsx")
                            c2.download_button("PDF", generar_pdf_con_graficos(df_res, "Reporte"), "Reporte.pdf")
                            c3.download_button("Word", generar_word(df_res, "Reporte"), "Reporte.docx")
                    else: st.info("Falta columna tipo_operacion.")
                else: st.info("Sin datos.")
        except Exception as e: st.error(e)

with tab3: # VERIFICACIÓN
    if st.text_input("PIN Conciliación", type="password", key="p2") == ACCESS_CODE_MAESTRO:
        st.subheader("🔍 Conciliación Total")
        up = st.file_uploader("Archivo Petrobras", ["xlsx", "csv"])
        if up:
            try:
                dfe = pd.read_csv(SHEET_URL); dfe.columns = dfe.columns.str.strip().str.lower()
                dfe['fecha'] = pd.to_datetime(dfe['fecha'], errors='coerce', dayfirst=True)
                dfe['litros'] = pd.to_numeric(dfe['litros'], errors='coerce').fillna(0)
                dfe['KEY'] = dfe['fecha'].dt.strftime('%Y-%m-%d') + "_" + dfe['responsable_cargo'].str.strip().str.upper() + "_" + dfe['litros'].astype(int).astype(str)

                if up.name.endswith('.csv'): 
                    try: dfp = pd.read_csv(up, sep=';', header=0, usecols=[5, 12, 14, 15], names=["Fecha", "Resp", "Comb", "Litros"], engine='python')
                    except: up.seek(0); dfp = pd.read_csv(up, sep=',', header=0, usecols=[5, 12, 14, 15], names=["Fecha", "Resp", "Comb", "Litros"])
                else: dfp = pd.read_excel(up, usecols=[5, 12, 14, 15], names=["Fecha", "Resp", "Comb", "Litros"])
                
                dfp['Fecha'] = pd.to_datetime(dfp['Fecha'], errors='coerce', dayfirst=True)
                dfp['Litros'] = pd.to_numeric(dfp['Litros'], errors='coerce').fillna(0)
                dfp['KEY'] = dfp['Fecha'].dt.strftime('%Y-%m-%d') + "_" + dfp['Resp'].astype(str).str.strip().str.upper() + "_" + dfp['Litros'].astype(int).astype(str)

                m = pd.merge(dfp, dfe, on='KEY', how='outer', indicator=True)
                
                def clasificar(r):
                    if r['_merge'] == 'both': return "✅ Correcto"
                    elif r['_merge'] == 'left_only': return "⚠️ Faltante en Sistema"
                    else: return "❓ Sobrante en Sistema"

                m['Estado'] = m.apply(clasificar, axis=1)
                m['Fecha_F'] = m['Fecha'].combine_first(m['fecha'])
                m['Resp_F'] = m['Resp'].combine_first(m['responsable_cargo'])
                m['Comb_F'] = m['Comb'].combine_first(m['tipo_combustible'])
                m['Litros_F'] = m['Litros'].combine_first(m['litros'])
                
                fv = m[['Fecha_F', 'Resp_F', 'Comb_F', 'Litros_F', 'Estado']].sort_values(by='Fecha_F', ascending=False)
                
                def color(val):
                    if "Correcto" in val: return 'background-color: #d4edda; color: black'
                    elif "Faltante" in val: return 'background-color: #f8d7da; color: black'
                    else: return 'background-color: #fff3cd; color: black'

                st.dataframe(fv.style.format({"Litros_F": "{:.1f}"}).applymap(color, subset=['Estado']), use_container_width=True)
                
                st.markdown("---")
                if st.button("🚀 SINCRONIZAR REPORTE COMPLETO"):
                    bar = st.progress(0); n = len(fv); ok = 0
                    for i, r in fv.iterrows():
                        p = {
                            "target_sheet": "Facturas_Petrobras", 
                            "fecha": str(r['Fecha_F']), 
                            "tipo_operacion": "CONCILIACION", 
                            "codigo_maquina": "PETRO-F", 
                            "nombre_maquina": "Reporte", 
                            "origen": "Petrobras", 
                            "chofer": "N/A", 
                            "responsable_cargo": str(r['Resp_F']), 
                            "actividad": "Auditoria", 
                            "lectura_actual": 0, 
                            "litros": float(r['Litros_F']), 
                            "tipo_combustible": str(r['Comb_F']), 
                            "media": 0, 
                            "estado_conciliacion": r['Estado'],
                            "fuente_dato": "PETROBRAS_IMPORT"
                        }
                        try: requests.post(SCRIPT_URL, json=p); ok += 1
                        except: pass
                        time.sleep(0.1); bar.progress((i+1)/n)
                    st.success(f"✅ Sincronizado: {ok} registros.")

            except Exception as e: st.error(f"Error: {e}")

with tab4: # MÁQUINA (MATEMÁTICA CORREGIDA Y ESTADO)
    if st.text_input("PIN Analítico", type="password", key="p3") == ACCESS_CODE_MAESTRO:
        try:
            dfm = pd.read_csv(SHEET_URL); dfm.columns = dfm.columns.str.strip().str.lower()
            for c in ['litros','media','lectura_actual']: 
                if c in dfm.columns: dfm[c] = pd.to_numeric(dfm[c], errors='coerce').fillna(0)
            dfm['fecha'] = pd.to_datetime(dfm['fecha'], errors='coerce', dayfirst=True)
            
            c1, c2 = st.columns(2)
            maq = c1.selectbox("Máquina", [f"{k} - {v['nombre']}" for k,v in FLOTA.items()])
            y = c2.selectbox("Año", [2024, 2025, 2026], index=1)
            cod = maq.split(" - ")[0]
            
            dy = dfm[(dfm['codigo_maquina'] == cod) & (dfm['fecha'].dt.year == y)]
            if not dy.empty:
                res = []
                mn = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
                for i in range(1, 13):
                    dm = dy[dy['fecha'].dt.month == i]
                    l_total = dm['litros'].sum()
                    
                    if l_total > 0:
                        # 1. Recorrido Real del Mes
                        rec = dm['lectura_actual'].max() - dm['lectura_actual'].min()
                        
                        # 2. Litros Ajustados (Quitamos la primera carga si hay más de 1)
                        if len(dm) > 1:
                            dm_sorted = dm.sort_values('lectura_actual')
                            l_ajustados = dm_sorted.iloc[1:]['litros'].sum()
                        else:
                            l_ajustados = l_total

                        # 3. Promedio
                        if FLOTA[cod]['unidad'] == 'KM':
                            pr = rec/l_ajustados if l_ajustados > 0 else 0
                        else:
                            pr = l_ajustados/rec if rec > 0 else 0
                    else:
                        pr = 0
                        l_total = 0
                    
                    # 4. Estado
                    estado = "N/A"
                    if l_total > 0 and pr > 0:
                        ideal = FLOTA[cod]['ideal']
                        if FLOTA[cod]['unidad'] == 'KM':
                            if pr < ideal * (1 - MARGEN_TOLERANCIA): estado = "⚠️ Alto Consumo"
                            elif pr > ideal * (1 + MARGEN_TOLERANCIA): estado = "✨ Muy Bueno"
                            else: estado = "✅ Ideal"
                        else:
                            if pr > ideal * (1 + MARGEN_TOLERANCIA): estado = "⚠️ Alto Consumo"
                            elif pr < ideal * (1 - MARGEN_TOLERANCIA): estado = "✨ Muy Bueno"
                            else: estado = "✅ Ideal"

                    res.append({
                        "Mes": mn[i-1], 
                        "Litros": round(l_total, 1), 
                        "Promedio": round(pr, 2),
                        "Estado": estado
                    })
                
                dr = pd.DataFrame(res)
                st.subheader(f"📊 {maq} (Ideal: {FLOTA[cod]['ideal']} {FLOTA[cod]['unidad']})")
                c1, c2 = st.columns(2)
                
                fig_line, ax_line = plt.subplots(figsize=(6, 4))
                fig_line.patch.set_facecolor('white'); ax_line.set_facecolor('white')
                ax_line.plot(dr['Mes'], dr['Promedio'], marker='o', label='Real', color='blue')
                ax_line.axhline(y=FLOTA[cod]['ideal'], color='r', linestyle='--', label='Ideal')
                ax_line.set_title("Rendimiento"); ax_line.legend(); ax_line.grid(True, alpha=0.3)
                c1.pyplot(fig_line)
                
                fig_bar, ax_bar = plt.subplots(figsize=(6, 4))
                fig_bar.patch.set_facecolor('white'); ax_bar.set_facecolor('white')
                ax_bar.bar(dr['Mes'], dr['Litros'], color='orange')
                ax_bar.set_title("Consumo (Litros)")
                c2.pyplot(fig_bar)

                st.dataframe(dr.style.format({"Litros": "{:.1f}", "Promedio": "{:.2f}"}), use_container_width=True)
                
                c1, c2 = st.columns(2)
                c1.download_button("PDF", generar_pdf_con_graficos(dr, f"Reporte {cod}"), f"{cod}.pdf")
                c2.download_button("Word", generar_word(dr, f"Reporte {cod}"), f"{cod}.docx")
            else: st.info("Sin datos.")
        except: st.error("Error datos.")
