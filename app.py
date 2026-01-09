import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import io
import tempfile
import time
from datetime import date, datetime, timedelta
from fpdf import FPDF
from docx import Document
from docx.shared import Inches

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ekos Control 🇵🇾", layout="wide")

# URL del Script de Google
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwnPU3LdaHqrNO4bTsiBMKmm06ZSm3dUbxb5OBBnHBQOHRSuxcGv_MK4jWNHsrAn3M/exec"
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E"
# OJO: Aquí leemos la hoja principal para los reportes
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

# --- 2. GENERADORES DE REPORTE ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        titulo = 'INFORME EJECUTIVO - CONTROL EKOS'.encode('latin-1', 'replace').decode('latin-1')
        subtitulo = 'Excelencia Consultora - Nueva Esperanza'.encode('latin-1', 'replace').decode('latin-1')
        self.cell(0, 10, titulo, 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, subtitulo, 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generar_excel(df, sheet_name='Datos'):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        worksheet.set_column('A:N', 20)
    return output.getvalue()

def generar_word(df_data, titulo_reporte, grafico_fig=None):
    doc = Document()
    doc.add_heading(titulo_reporte, 0)
    doc.add_paragraph('Generado por Sistema Ekos Control')
    if grafico_fig:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            grafico_fig.savefig(tmpfile.name, format='png')
            doc.add_picture(tmpfile.name, width=Inches(6))
            doc.add_paragraph('Grafico de Analisis')
    if not df_data.empty:
        t = doc.add_table(rows=1, cols=len(df_data.columns))
        t.style = 'Table Grid'
        hdr_cells = t.rows[0].cells
        for i, col_name in enumerate(df_data.columns): hdr_cells[i].text = str(col_name)
        for _, row in df_data.iterrows():
            row_cells = t.add_row().cells
            for i, item in enumerate(row):
                texto_celda = str(item)
                if isinstance(item, float): texto_celda = f"{item:.2f}"
                row_cells[i].text = texto_celda
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

def generar_pdf_con_graficos(df_data, titulo_reporte, incluir_grafico=False, tipo_grafico="barras"):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, clean_text(titulo_reporte), 0, 1, 'L')
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 8)
    
    cols = list(df_data.columns)
    w_col = 190 / len(cols) if len(cols) > 0 else 30
    
    for col in cols: pdf.cell(w_col, 10, clean_text(col), 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font('Arial', '', 8)
    for _, row in df_data.iterrows():
        for col in cols:
            val = row[col]
            if isinstance(val, float): val = f"{val:.2f}"
            pdf.cell(w_col, 10, clean_text(str(val)), 1)
        pdf.ln()

    if incluir_grafico:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Analisis Grafico", 0, 1, 'L')
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        if tipo_grafico == "anual":
            ax.plot(df_data['Mes'], df_data['Promedio Real'], marker='o', label='Real', color='blue', linewidth=2)
            ax.plot(df_data['Mes'], df_data['Promedio Ideal'], linestyle='--', label='Ideal', color='green', linewidth=2)
            ax.set_title("Evolucion Anual de Rendimiento")
            ax.set_ylabel("Promedio")
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            if 'nombre_maquina' in df_data.columns and 'litros' in df_data.columns:
                ax.bar(df_data['nombre_maquina'], df_data['litros'], color='orange')
                ax.set_title("Consumo Total por Maquina")
                plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            fig.savefig(tmpfile.name, format='png')
            pdf.image(tmpfile.name, x=10, y=40, w=190)
        plt.close(fig) 
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. INTERFAZ ---
st.title("⛽ Ekos Forestal / Control de combustible")
st.markdown("""
<p style='font-size: 18px; color: gray; margin-top: -20px;'>
    Desenvolvido por Excelencia Consultora en Paraguay 🇵🇾 
    <span style='font-size: 14px; font-style: italic; color: gray; margin-left: 10px;'>
        creado por Thaylan Cesca
    </span>
</p>
<hr>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👋 Registro Personal", "🔐 Auditoría", "🔍 Verificación", "🚜 Máquina por Máquina"])

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
            
            if st.form_submit_button("✅ GUARDAR REGISTRO"):
                if not chofer or not act:
                    st.warning("⚠️ Completa los campos.")
                else:
                    error_lectura = False
                    media_calc = 0.0
                    if "Máquina" in operacion and lect > 0:
                        try:
                            df_hist = pd.read_csv(SHEET_URL)
                            df_hist.columns = df_hist.columns.str.strip().str.lower()
                            cols_num = ['lectura_actual', 'litros', 'media']
                            for c in cols_num:
                                if c in df_hist.columns: df_hist[c] = pd.to_numeric(df_hist[c], errors='coerce').fillna(0)
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
                        # NOTA: Aquí target_sheet es None para que vaya a la hoja principal
                        payload = {"fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f, "nombre_maquina": nom_f, "origen": origen, "chofer": chofer, "responsable_cargo": encargado_sel, "actividad": act, "lectura_actual": lect, "litros": lts, "tipo_combustible": tipo_comb, "media": media_calc}
                        try:
                            r = requests.post(SCRIPT_URL, json=payload)
                            if r.status_code == 200: st.balloons(); st.success(f"¡Guardado! Promedio calculado: {media_calc:.2f}")
                            else: st.error("Error en permisos.")
                        except: st.error("Error de conexión.")
    elif pwd_input: st.error("❌ Contraseña incorrecta.")

# --- TAB 2: AUDITORÍA ---
with tab2:
    if st.text_input("PIN Maestro Auditoría", type="password", key="p_aud") == ACCESS_CODE_MAESTRO:
        try:
            df = pd.read_csv(SHEET_URL)
            if not df.empty:
                df.columns = df.columns.str.strip().str.lower()
                cols_num = ['litros', 'media', 'lectura_actual']
                for c in cols_num:
                    if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                
                if 'fecha' in df.columns:
                    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
                    
                    st.subheader("📦 Stock Actual en Barriles")
                    tipo_audit = st.radio("Combustible:", TIPOS_COMBUSTIBLE, horizontal=True)
                    cb = st.columns(4)
                    for i, b in enumerate(BARRILES_LISTA):
                        ent = df[(df['codigo_maquina'] == b) & (df['tipo_combustible'] == tipo_audit)]['litros'].sum()
                        sal = df[(df['origen'] == b) & (df['tipo_combustible'] == tipo_audit)]['litros'].sum()
                        cb[i].metric(b, f"{ent - sal:.1f} L", f"Entradas: {ent:.0f}")
                    
                    st.markdown("---")
                    
                    st.subheader("📅 Filtro de Periodo")
                    c_date1, c_date2 = st.columns(2)
                    with c_date1: f_ini = st.date_input("Desde:", date.today() - timedelta(days=30))
                    with c_date2: f_fin = st.date_input("Hasta:", date.today())
                    
                    mask = (df['fecha'].dt.date >= f_ini) & (df['fecha'].dt.date <= f_fin)
                    df_filtrado = df.loc[mask]
                    
                    if not df_filtrado.empty:
                        st.subheader("📋 Detalle de Movimientos")
                        cols_finales = [c for c in ['fecha', 'nombre_maquina', 'origen', 'litros', 'tipo_combustible', 'responsable_cargo', 'media', 'lectura_actual'] if c in df.columns]
                        st.dataframe(df_filtrado[cols_finales].sort_values(by='fecha', ascending=False), use_container_width=True)
                        
                        st.markdown("---")
                        
                        st.subheader("📊 Análisis Gráfico")
                        df_maq = df_filtrado[df_filtrado['tipo_operacion'].str.contains("Máquina", na=False)]
                        
                        if not df_maq.empty:
                            resumen_data = []
                            maquinas_activas = df_maq['codigo_maquina'].unique()
                            for cod in maquinas_activas:
                                if cod in FLOTA:
                                    datos_maq = df_maq[df_maq['codigo_maquina'] == cod]
                                    total_litros = datos_maq['litros'].sum()
                                    datos_maq['recorrido_est'] = datos_maq['media'] * datos_maq['litros']
                                    total_recorrido = datos_maq['recorrido_est'].sum()
                                    if total_recorrido < 1:
                                        total_recorrido = datos_maq['lectura_actual'].max() - datos_maq['lectura_actual'].min()

                                    unidad = FLOTA[cod]['unidad']
                                    ideal = FLOTA[cod].get('ideal', 0.0)
                                    promedio_real = 0.0
                                    metric_label = "Unid/L"
                                    if total_litros > 0:
                                        if unidad == 'KM': promedio_real = total_recorrido / total_litros; metric_label = "KM/L"
                                        else: 
                                            if total_recorrido > 0: promedio_real = total_litros / total_recorrido; metric_label = "L/Hora"
                                    estado = "N/A"
                                    if ideal > 0:
                                        margen = ideal * MARGEN_TOLERANCIA
                                        min_ok, max_ok = ideal - margen, ideal + margen
                                        estado = "✅ Normal" if min_ok <= promedio_real <= max_ok else "⚠️ Fuera de Rango"

                                    resumen_data.append({
                                        "Máquina": FLOTA[cod]['nombre'],
                                        "Unidad": unidad,
                                        "Litros Usados": round(total_litros, 2),
                                        f"Promedio Real ({metric_label})": round(promedio_real, 2),
                                        f"Promedio Ideal": ideal,
                                        "Estado": estado
                                    })
                            df_res = pd.DataFrame(resumen_data)
                            st.dataframe(df_res, use_container_width=True)
                            st.markdown("##### Consumo Total del Periodo")
                            st.bar_chart(df_maq.groupby('nombre_maquina')['litros'].sum())
                            
                            st.markdown("### 📥 Centro de Descargas")
                            col_down1, col_down2, col_down3 = st.columns(3)
                            with col_down1:
                                excel_data = generar_excel(df_filtrado[cols_finales])
                                st.download_button("📊 Descargar Historial (Excel)", data=excel_data, file_name="Historial_Ekos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                            with col_down2:
                                pdf_b = generar_pdf_con_graficos(df_maq, "Informe General de Consumo", incluir_grafico=True, tipo_grafico="barras")
                                st.download_button("📄 Descargar Informe (PDF)", pdf_b, "Informe_Grafico.pdf")
                            with col_down3:
                                word_b = generar_word(df_res, "Reporte Rendimiento Ekos")
                                st.download_button("📝 Descargar Informe (Word)", word_b, "Informe_Rendimiento.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                        else: st.info("No hubo consumo de máquinas en este periodo.")
                    else: st.warning("No hay datos en el rango seleccionado.")
                else: st.warning("⚠️ Faltan encabezados.")
            else: st.info("Planilla vacía.")
        except Exception as e: st.error(f"Error técnico: {e}")

# --- TAB 3: VERIFICACIÓN (SINCRONIZACIÓN A OTRA HOJA) ---
with tab3:
    if st.text_input("PIN Conciliación", type="password", key="p_con") == ACCESS_CODE_MAESTRO:
        st.subheader("🔍 Verificación: Ekos vs Factura Petrobras")
        archivo_p = st.file_uploader("Subir Archivo Petrobras", type=["xlsx", "csv"])
        
        if archivo_p:
            try:
                # 1. CARGAR DATOS EKOS
                df_ekos = pd.read_csv(SHEET_URL)
                df_ekos.columns = df_ekos.columns.str.strip().str.lower()
                if 'fecha' in df_ekos.columns and 'litros' in df_ekos.columns:
                    df_ekos['fecha'] = pd.to_datetime(df_ekos['fecha'], errors='coerce')
                    df_ekos['litros'] = pd.to_numeric(df_ekos['litros'], errors='coerce').fillna(0)
                
                # 2. CARGAR FACTURA
                if archivo_p.name.endswith('.csv'):
                    try:
                        df_p = pd.read_csv(archivo_p, sep=';', header=0, usecols=[5, 14, 15], names=["Fecha", "Comb_Original", "Litros"], engine='python')
                    except:
                        archivo_p.seek(0)
                        df_p = pd.read_csv(archivo_p, sep=',', header=0, usecols=[5, 14, 15], names=["Fecha", "Comb_Original", "Litros"])
                else:
                    df_p = pd.read_excel(archivo_p, usecols=[5, 14, 15], names=["Fecha", "Comb_Original", "Litros"])
                
                df_p['Fecha'] = pd.to_datetime(df_p['Fecha'], errors='coerce')
                df_p['Combustible'] = df_p['Comb_Original'].map(MAPA_COMBUSTIBLE).fillna("Otros")
                
                # 3. COMPARATIVO
                ekos_agg = df_ekos.groupby([df_ekos['fecha'].dt.date, 'tipo_combustible'])['litros'].sum().reset_index()
                ekos_agg.columns = ['Fecha', 'Combustible', 'Litros_Ekos']
                
                factura_agg = df_p.groupby([df_p['Fecha'].dt.date, 'Combustible'])['Litros'].sum().reset_index()
                factura_agg.columns = ['Fecha', 'Combustible', 'Litros_Factura']
                
                df_comparativo = pd.merge(ekos_agg, factura_agg, on=['Fecha', 'Combustible'], how='outer').fillna(0)
                df_comparativo['Diferencia'] = df_comparativo['Litros_Ekos'] - df_comparativo['Litros_Factura']
                
                st.subheader("📊 Cuadro Comparativo")
                st.dataframe(df_comparativo, use_container_width=True)
                
                # Descargas
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    excel_comp = generar_excel(df_comparativo, "Comparativo")
                    st.download_button("📥 Descargar Comparativo (Excel)", data=excel_comp, file_name="Comparativo.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                with col_d2:
                    pdf_comp = generar_pdf_con_graficos(df_comparativo, "Comparativo Ekos vs Petrobras")
                    st.download_button("📄 Descargar Comparativo (PDF)", pdf_comp, "Comparativo.pdf")

                st.markdown("---")
                
                # 4. SINCRONIZACIÓN A OTRA HOJA
                st.subheader("☁️ Almacenamiento Separado")
                st.info("ℹ️ Los datos se guardarán en la hoja 'Facturas_Petrobras' de tu Google Sheets.")
                
                if st.button("🚀 SINCRONIZAR A HOJA DE FACTURAS"):
                    progress_bar = st.progress(0)
                    total_rows = len(df_p)
                    success_count = 0
                    
                    for index, r in df_p.iterrows():
                        # AQUI AGREGAMOS "target_sheet" PARA QUE EL SCRIPT SEPA DONDE GUARDAR
                        p = {
                            "target_sheet": "Facturas_Petrobras", # <--- CLAVE PARA CAMBIAR DE HOJA
                            "fecha": str(r['Fecha']), 
                            "tipo_operacion": "FACTURA PETROBRAS", 
                            "codigo_maquina": "PETRO-F", 
                            "nombre_maquina": "Factura Importada", 
                            "origen": "Surtidor", 
                            "chofer": "Importacion", 
                            "responsable_cargo": "Auditoria", 
                            "actividad": "Carga Masiva", 
                            "lectura_actual": 0, 
                            "litros": float(r['Litros']), 
                            "tipo_combustible": r['Combustible'], 
                            "media": 0
                        }
                        try:
                            requests.post(SCRIPT_URL, json=p)
                            success_count += 1
                        except: pass
                        
                        time.sleep(0.1) 
                        progress_bar.progress((index + 1) / total_rows)
                    
                    st.success(f"✅ Se guardaron {success_count} registros en la hoja 'Facturas_Petrobras'.")
                    
            except Exception as e: st.error(f"Error al procesar archivo: {e}")

# --- TAB 4: MÁQUINA POR MÁQUINA ---
with tab4:
    if st.text_input("PIN Analítico", type="password", key="p_maq") == ACCESS_CODE_MAESTRO:
        st.subheader("🚜 Análisis Anual: Máquina por Máquina")
        try:
            df_m = pd.read_csv(SHEET_URL)
            df_m.columns = df_m.columns.str.strip().str.lower()
            for c in ['litros', 'media', 'lectura_actual']:
                if c in df_m.columns: df_m[c] = pd.to_numeric(df_m[c], errors='coerce').fillna(0)
            if 'fecha' in df_m.columns:
                df_m['fecha'] = pd.to_datetime(df_m['fecha'], errors='coerce')

                col_sel1, col_sel2 = st.columns(2)
                with col_sel1:
                    lista_maquinas = [f"{k} - {v['nombre']}" for k,v in FLOTA.items()]
                    maq_elegida_str = st.selectbox("Seleccione Máquina:", lista_maquinas)
                    cod_maq = maq_elegida_str.split(" - ")[0]
                with col_sel2:
                    anio_elegido = st.selectbox("Seleccione Año:", [2024, 2025, 2026], index=1)
                
                df_maq_anual = df_m[(df_m['codigo_maquina'] == cod_maq) & (df_m['fecha'].dt.year == anio_elegido)]
                
                if not df_maq_anual.empty:
                    datos_mensuales = []
                    meses_nombre = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                    ideal = FLOTA[cod_maq].get('ideal', 0.0)
                    unidad = FLOTA[cod_maq]['unidad']
                    
                    for mes_idx in range(1, 13):
                        df_mes = df_maq_anual[df_maq_anual['fecha'].dt.month == mes_idx]
                        litros_mes = df_mes['litros'].sum()
                        
                        prom_real_mes = 0.0
                        if litros_mes > 0:
                            df_mes['recorrido_est'] = df_mes['media'] * df_mes['litros']
                            rec_media = df_mes['recorrido_est'].sum()
                            rec_lectura = df_mes['lectura_actual'].max() - df_mes['lectura_actual'].min()
                            total_rec = max(rec_media, rec_lectura) if rec_media > 1 or rec_lectura > 0 else 0
                            
                            if unidad == 'KM': prom_real_mes = total_rec / litros_mes
                            else: 
                                if total_rec > 0: prom_real_mes = litros_mes / total_rec

                        estado = "-"
                        if litros_mes > 0 and ideal > 0:
                             min_ok, max_ok = ideal * (1-MARGEN_TOLERANCIA), ideal * (1+MARGEN_TOLERANCIA)
                             estado = "✅" if min_ok <= prom_real_mes <= max_ok else "⚠️"

                        datos_mensuales.append({
                            "Mes": meses_nombre[mes_idx-1],
                            "Litros": round(litros_mes, 2),
                            "Promedio Real": round(prom_real_mes, 2),
                            "Promedio Ideal": ideal,
                            "Estado": estado
                        })
                    
                    df_resumen_mensual = pd.DataFrame(datos_mensuales)
                    
                    st.subheader(f"📊 Panel de Control: {FLOTA[cod_maq]['nombre']}")
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        st.markdown("**Rendimiento Mensual**")
                        fig_line, ax_line = plt.subplots(figsize=(6, 4))
                        ax_line.plot(df_resumen_mensual['Mes'], df_resumen_mensual['Promedio Real'], marker='o', label='Real', color='blue', linewidth=2)
                        ax_line.plot(df_resumen_mensual['Mes'], df_resumen_mensual['Promedio Ideal'], linestyle='--', label='Ideal', color='green', linewidth=2)
                        ax_line.set_ylabel("Rendimiento")
                        ax_line.legend()
                        ax_line.grid(True, alpha=0.3)
                        plt.setp(ax_line.get_xticklabels(), rotation=45, ha="right")
                        st.pyplot(fig_line)

                    with col_chart2:
                        st.markdown("**Consumo (Litros)**")
                        fig_bar, ax_bar = plt.subplots(figsize=(6, 4))
                        bars = ax_bar.bar(df_resumen_mensual['Mes'], df_resumen_mensual['Litros'], color='orange', alpha=0.8)
                        ax_bar.set_ylabel("Litros")
                        ax_bar.grid(axis='y', alpha=0.3)
                        plt.setp(ax_bar.get_xticklabels(), rotation=45, ha="right")
                        for bar in bars:
                            height = bar.get_height()
                            if height > 0: ax_bar.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
                        st.pyplot(fig_bar)

                    st.markdown("#### Detalle Numérico")
                    st.dataframe(df_resumen_mensual, use_container_width=True)

                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        pdf_anual = generar_pdf_con_graficos(df_resumen_mensual, f"Reporte Anual {anio_elegido}: {FLOTA[cod_maq]['nombre']}", incluir_grafico=True, tipo_grafico="anual")
                        st.download_button("📄 Descargar PDF Anual", pdf_anual, f"Reporte_{cod_maq}_{anio_elegido}.pdf")
                    with col_d2:
                        word_anual = generar_word(df_resumen_mensual, f"Reporte Anual {anio_elegido}: {FLOTA[cod_maq]['nombre']}", grafico_fig=fig_line)
                        st.download_button("📝 Descargar Word Anual", word_anual, f"Reporte_{cod_maq}_{anio_elegido}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    
                else:
                    st.info(f"No hay datos registrados para la máquina {cod_maq} en el año {anio_elegido}.")

        except Exception as e: st.error(f"Error al procesar: {e}")
