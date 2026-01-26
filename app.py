cat > pages/2_Ekos.py <<EOF
import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import io
import time
import base64
from datetime import date, datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURACION ---
st.set_page_config(page_title="Ekos Forestal", layout="wide", initial_sidebar_state="collapsed")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
        .stButton>button {width: 100%; border-radius: 5px; height: 3em;}
        h1 {color: #2E4053;}
        div[data-testid="stMetricValue"] {font-size: 1.2rem;}
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzxEMHJwx_90pUVc621LeAsFIy1vnnnmCNH0WhbJDYbM_slfBu7BJpZhRqkLB4GmwyU/exec"
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]
MARGEN_TOLERANCIA = 0.20
SURTIDORES = ["Surtidor Petrobras", "Surtidor Shell", "Surtidor Crisma", "Surtidor Puma"]

# --- USUARIOS ---
USUARIOS_DB = {
    "Juan Britez":    {"pwd": "jbritez45",   "rol": "operador", "barril": "Barril Juan"},
    "Diego Bordon":   {"pwd": "Bng2121",     "rol": "operador", "barril": "Barril Diego"},
    "Jonatan Vargas": {"pwd": "jv2026",      "rol": "operador", "barril": "Barril Jonatan"},
    "Cesar Cabañas":  {"pwd": "cab14",       "rol": "operador", "barril": "Barril Cesar"},
    "Natalia Santana": {"pwd": "Santana2057", "rol": "admin",    "barril": "Acceso Total"},
    "Auditoria":       {"pwd": "1645",        "rol": "admin",    "barril": "Acceso Total"}
}
BARRILES_LISTA = ["Barril Diego", "Barril Juan", "Barril Jonatan", "Barril Cesar"]

# --- TARJETAS ---
TARJETAS_DATA = {
    "Diego Bordon": ["MULTI Diego - 70026504990100126"],
    "Cesar Cabañas": ["MULTI CESAR - 70026504990100140", "M-02 - 70026504990100179"],
    "Juan Britez": ["MULTI JUAN - 70026504990100112", "M-13 - 70026504990100024"],
    "Jonatan Vargas": ["M-03 - 70026504990100189", "S-03 - 70026504990100056", "S-05 - 70026504990100063", "MULTI JONATAN - 70026504990100134"]
}

# --- FLOTA CORREGIDA ---
FLOTA = {
    "HV-01": {"nombre": "Caterpillar 320D", "unidad": "Horas", "ideal": 18.0}, 
    "JD-01": {"nombre": "John Deere", "unidad": "Horas", "ideal": 15.0},
    "JD-02": {"nombre": "John Deere 6170", "unidad": "Horas", "ideal": 11.0},
    "JD-03": {"nombre": "John Deere 6110", "unidad": "Horas", "ideal": 4.0},
    "JD-04": {"nombre": "John Deere 5090", "unidad": "Horas", "ideal": 8.0},
    "M-01": {"nombre": "Nissan Frontier (Natalia)", "unidad": "KM", "ideal": 9.0},
    "M-02": {"nombre": "Chevrolet - S10", "unidad": "KM", "ideal": 8.0},
    "M-03": {"nombre": "GM S-10 (M-03)", "unidad": "KM", "ideal": 8.5},
    "M-11": {"nombre": "Nissan Frontier", "unidad": "KM", "ideal": 9.0},
    "M-17": {"nombre": "GM S-10", "unidad": "KM", "ideal": 10.0},
    "M13": {"nombre": "Nissan Frontier (M13)", "unidad": "Horas", "ideal": 5.0},
    "MC-06": {"nombre": "MB Canter", "unidad": "KM", "ideal": 6.0},
    "MF-02": {"nombre": "Massey Ferguson", "unidad": "Horas", "ideal": 9.0},
    "MICHIGAN": {"nombre": "Pala Michigan", "unidad": "Horas", "ideal": 14.0},
    "RA-01": {"nombre": "Ranger Alquilada 0-01", "unidad": "KM", "ideal": 9.0},
    "S-03": {"nombre": "Scania 113H", "unidad": "KM", "ideal": 2.3},
    "S-05": {"nombre": "Scania Azul", "unidad": "KM", "ideal": 2.4},
    "S-06": {"nombre": "Scania P112H", "unidad": "Horas", "ideal": 0.0},
    "S-07": {"nombre": "Scania R380", "unidad": "Horas", "ideal": 0.0},
    "S-08": {"nombre": "Scania Rojo", "unidad": "KM", "ideal": 2.2},
    "V-02": {"nombre": "Valmet 785", "unidad": "Horas", "ideal": 7.0},
    "V-07": {"nombre": "Valmet 1580", "unidad": "Horas", "ideal": 11.0},
    "V-11": {"nombre": "Valmet 8080", "unidad": "Horas", "ideal": 9.5},
    "V-12": {"nombre": "Valtra 180", "unidad": "Horas", "ideal": 12.0}
}

# --- FUNCIONES ---
def clean_text(text): return str(text).encode('latin-1', 'replace').decode('latin-1')

def generar_pdf_completo(df_resumen, df_detalle, titulo):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    
    # Pagina 1: Resumen
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, clean_text(f"{titulo} - RESUMEN"), 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 10)
    # Encabezados Resumen
    cols_res = ["Codigo", "Recorrido", "Litros Total", "Rendimiento", "Ideal", "Estado"]
    ancho_col = [30, 30, 30, 30, 30, 40]
    
    for i, col in enumerate(cols_res):
        pdf.cell(ancho_col[i], 10, clean_text(col), 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font('Arial', '', 10)
    for _, row in df_resumen.iterrows():
        pdf.cell(ancho_col[0], 10, clean_text(row['Codigo']), 1)
        pdf.cell(ancho_col[1], 10, str(row['Recorrido']), 1)
        pdf.cell(ancho_col[2], 10, str(row['Litros']), 1)
        
        # Detectar unidad para mostrar label correcto
        und = "N/A"
        if row['Codigo'] in FLOTA:
            und = "Km/L" if FLOTA[row['Codigo']]['unidad'] == 'KM' else "L/H"
            
        val_rend = row.get('Km/L', 0) if und == "Km/L" else row.get('L/H', 0)
        pdf.cell(ancho_col[3], 10, f"{val_rend} {und}", 1)
        pdf.cell(ancho_col[4], 10, str(row['Ideal']), 1)
        pdf.cell(ancho_col[5], 10, clean_text(row['Estado']), 1)
        pdf.ln()

    # Pagina 2: Detalle
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, clean_text(f"{titulo} - DETALLE DE MOVIMIENTOS"), 0, 1, 'C')
    pdf.ln(5)
    
    # Encabezados Detalle
    cols_det = ["Fecha", "Maquina", "Chofer", "Litros", "Lectura", "Rend.", "Estado"]
    w_det = [30, 50, 40, 20, 30, 30, 40]
    
    pdf.set_font('Arial', 'B', 9)
    for i, c in enumerate(cols_det):
        pdf.cell(w_det[i], 10, clean_text(c), 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font('Arial', '', 8)
    for _, row in df_detalle.iterrows():
        f_str = row['fecha'].strftime('%d/%m/%Y') if pd.notnull(row['fecha']) else ""
        pdf.cell(w_det[0], 8, f_str, 1)
        pdf.cell(w_det[1], 8, clean_text(str(row.get('nombre_maquina', ''))[:20]), 1)
        pdf.cell(w_det[2], 8, clean_text(str(row.get('chofer', ''))[:15]), 1)
        pdf.cell(w_det[3], 8, str(row.get('litros', 0)), 1)
        pdf.cell(w_det[4], 8, str(row.get('lectura_actual', 0)), 1)
        pdf.cell(w_det[5], 8, clean_text(str(row.get('Rendimiento_Calc', '-'))), 1)
        pdf.cell(w_det[6], 8, clean_text(str(row.get('Estado_Calc', '-'))), 1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1', 'replace')

@st.dialog("Confirmar")
def confirmar_envio(pl):
    st.write(f"**Maquina:** {pl['codigo_maquina']}")
    st.write(f"**Litros:** {pl['litros']}")
    st.write(f"**Chofer:** {pl['chofer']}")
    
    if st.button("CONFIRMAR Y GUARDAR", type="primary"):
        try:
            requests.post(SCRIPT_URL, json=pl)
            st.session_state['exito'] = True
            st.rerun()
        except Exception: st.error("Error de conexion")

# --- APP START ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🚜 Ekos Forestal")
        with st.form("login"):
            u = st.selectbox("Usuario", [""]+list(USUARIOS_DB.keys()))
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Entrar"):
                if u in USUARIOS_DB and p == USUARIOS_DB[u]['pwd']:
                    st.session_state['logged_in'] = True
                    st.session_state['usuario'] = u
                    st.session_state['rol'] = USUARIOS_DB[u]['rol']
                    st.session_state['barril'] = USUARIOS_DB[u]['barril']
                    st.rerun()
    st.stop()

# --- MAIN INTERFACE ---
user = st.session_state['usuario']
rol = st.session_state['rol']
st.sidebar.info(f"Usuario: {user}")
if st.sidebar.button("Salir"): 
    st.session_state.clear()
    st.rerun()

if st.session_state.get('exito'):
    st.success("✅ Datos Guardados Correctamente")
    st.session_state['exito'] = False

tabs = st.tabs(["Carga", "Auditoria", "Conciliacion"])

# TAB 1: CARGA
with tabs[0]:
    st.header("Registro de Combustible")
    op = st.radio("Operacion", ["Maquina", "Barril"], horizontal=True)
    
    with st.form("main_form"):
        c1, c2 = st.columns(2)
        if op == "Maquina":
            maqs = [f"{k} - {v['nombre']}" for k,v in FLOTA.items()] + ["Otro"]
            sel = c1.selectbox("Maquina", maqs)
            cod = sel.split(" - ")[0] if sel != "Otro" else c1.text_input("Cod Manual")
            nom = FLOTA[cod]['nombre'] if sel != "Otro" else c1.text_input("Nombre Manual")
            ori = c1.selectbox("Origen", BARRILES_LISTA + SURTIDORES)
        else:
            cod = c1.selectbox("Destino", BARRILES_LISTA)
            nom = cod
            ori = c1.selectbox("Origen", SURTIDORES)
        
        litros = c2.number_input("Litros", min_value=0.0)
        lect = c2.number_input("Lectura (Km/Hs)", min_value=0.0) if op == "Maquina" else 0.0
        chofer = c1.text_input("Chofer")
        act = c2.text_input("Actividad")
        foto = st.file_uploader("Foto")

        if st.form_submit_button("Guardar"):
            img = ""
            if foto: img = base64.b64encode(foto.read()).decode('utf-8')
            pl = {
                "fecha": str(date.today()), "tipo_operacion": op, "codigo_maquina": cod,
                "nombre_maquina": nom, "origen": ori, "chofer": chofer, "responsable_cargo": user,
                "actividad": act, "lectura_actual": lect, "litros": litros, 
                "tipo_combustible": "Diesel", "imagen_base64": img
            }
            confirmar_envio(pl)

# TAB 2: AUDITORIA (MEJORADA)
with tabs[1]:
    if rol == "admin":
        st.header("Auditoria y Rendimiento")
        try:
            df = pd.read_csv(SHEET_URL)
            df.columns = df.columns.str.strip().str.lower()
            df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
            for c in ['litros', 'lectura_actual']:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

            # --- CALCULO FILA POR FILA (LOGICA COMPLEJA) ---
            df = df.sort_values(by=['codigo_maquina', 'fecha'])
            df['Delta_Lectura'] = df.groupby('codigo_maquina')['lectura_actual'].diff().fillna(0)
            
            def calc_rend(row):
                if row['litros'] > 0 and row['Delta_Lectura'] > 0:
                    cod = row['codigo_maquina']
                    if cod in FLOTA:
                        unit = FLOTA[cod]['unidad']
                        ideal = FLOTA[cod]['ideal']
                        val = 0
                        
                        if unit == 'KM': val = row['Delta_Lectura'] / row['litros'] # Km/L
                        else: val = row['litros'] / row['Delta_Lectura'] # L/H
                        
                        # Estado
                        est = "Normal"
                        if unit == 'KM' and val < ideal * 0.8: est = "Alto Consumo"
                        elif unit == 'Horas' and val > ideal * 1.2: est = "Alto Consumo"
                        
                        return round(val, 2), est, f"{val:.2f} ({unit})"
                return 0, "N/A", "-"

            res_calc = df.apply(calc_rend, axis=1, result_type='expand')
            df[['Rendimiento_Num', 'Estado_Calc', 'Rendimiento_Calc']] = res_calc
            
            # FILTROS
            c1, c2 = st.columns(2)
            d1 = c1.date_input("Desde", date.today()-timedelta(30))
            d2 = c2.date_input("Hasta", date.today())
            
            mask = (df['fecha'].dt.date >= d1) & (df['fecha'].dt.date <= d2)
            df_fil = df[mask].copy()

            # TABLA PRINCIPAL (AHORA CON COLUMNAS NUEVAS)
            st.subheader("Detalle de Cargas")
            cols_show = ['fecha', 'codigo_maquina', 'litros', 'lectura_actual', 'Rendimiento_Calc', 'Estado_Calc', 'chofer']
            st.dataframe(df_fil[cols_show].sort_values('fecha', ascending=False), use_container_width=True)

            # TABLA RESUMEN (TOTALES)
            st.subheader("Resumen de Rendimiento (Periodo Seleccionado)")
            res_data = []
            if not df_fil.empty:
                for cod in df_fil['codigo_maquina'].unique():
                    dx = df_fil[df_fil['codigo_maquina'] == cod]
                    if cod in FLOTA: # Solo maquinas de flota
                        l_tot = dx['litros'].sum()
                        # Recorrido aprox (Max - Min del periodo)
                        rec = dx['lectura_actual'].max() - dx['lectura_actual'].min()
                        
                        # Calculo Global
                        kml, lh = 0, 0
                        ideal = FLOTA[cod]['ideal']
                        est = "Normal"
                        
                        if FLOTA[cod]['unidad'] == 'KM':
                            kml = rec / l_tot if l_tot > 0 else 0
                            if kml < ideal * 0.8: est = "CRITICO"
                        else:
                            lh = l_tot / rec if rec > 0 else 0
                            if lh > ideal * 1.2: est = "CRITICO"
                        
                        res_data.append({
                            "Codigo": cod, "Recorrido": rec, "Litros": l_tot,
                            "Km/L": round(kml, 2), "L/H": round(lh, 2), 
                            "Ideal": ideal, "Estado": est
                        })
            
            df_resumen = pd.DataFrame(res_data)
            st.dataframe(df_resumen, use_container_width=True)

            # --- BOTON DE DESCARGA MAESTRO ---
            st.markdown("### 📥 Descargar Informe Completo")
            if st.button("Generar PDF (Todo incluido)"):
                pdf_bytes = generar_pdf_completo(df_resumen, df_fil, "Reporte Ekos")
                b64 = base64.b64encode(pdf_bytes).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="Reporte_Ekos_Completo.pdf" style="text-decoration:none; color:white; background-color:red; padding:10px; border-radius:5px;">⬇️ DESCARGAR PDF AHORA</a>'
                st.markdown(href, unsafe_allow_html=True)

        except Exception as e: st.error(f"Error: {e}")

# TAB 3: CONCILIACION
with tabs[2]:
    st.write("Modulo de Conciliacion en Mantenimiento...")
EOF
