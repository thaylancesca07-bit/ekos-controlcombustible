cat > pages/2_Ekos.py <<EOF
import streamlit as st
import pandas as pd
import requests
import base64
import io
import xlsxwriter
from datetime import date, datetime, timedelta
from fpdf import FPDF

# --- CONFIGURACION ORIGINAL ---
st.set_page_config(page_title="Ekos Forestal", layout="wide", initial_sidebar_state="collapsed")

# --- ESTILOS (TU FORMATO ORIGINAL) ---
st.markdown("""
    <style>
        .stButton>button {width: 100%; border-radius: 5px; height: 3em;}
        div[data-testid="stSidebarUserContent"] {padding-top: 2rem;}
        h1 {color: #2E4053;}
        [data-testid="stSidebarNav"] {display: none;} 
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzxEMHJwx_90pUVc621LeAsFIy1vnnnmCNH0WhbJDYbM_slfBu7BJpZhRqkLB4GmwyU/exec"
SHEET_ID = "1OKfvu5T-Aocc0yMMFJaUJN3L-GR6cBuTxeIA3RNY58E"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

TIPOS_COMBUSTIBLE = ["Diesel S500", "Nafta", "Diesel Podium"]
SURTIDORES = ["Surtidor Petrobras", "Surtidor Shell", "Surtidor Crisma", "Surtidor Puma"]

# --- USUARIOS (SIN Ñ COMO PEDISTE) ---
USUARIOS_DB = {
    "Juan Britez":    {"pwd": "jbritez45",   "rol": "operador", "barril": "Barril Juan"},
    "Diego Bordon":   {"pwd": "Bng2121",     "rol": "operador", "barril": "Barril Diego"},
    "Jonatan Vargas": {"pwd": "jv2026",      "rol": "operador", "barril": "Barril Jonatan"},
    "Cesar Cabanas":  {"pwd": "cab14",       "rol": "operador", "barril": "Barril Cesar"},
    "Natalia Santana": {"pwd": "Santana2057", "rol": "admin",    "barril": "Acceso Total"},
    "Auditoria":       {"pwd": "1645",        "rol": "admin",    "barril": "Acceso Total"}
}
BARRILES_LISTA = ["Barril de Diego", "Barril de Juan", "Barril de Jonatan", "Barril de Cesar"]

# --- TARJETAS ---
TARJETAS_DATA = {
    "Diego Bordon": ["MULTI Diego - 70026504990100126"],
    "Cesar Cabanas": ["MULTI CESAR - 70026504990100140", "M-02 - 70026504990100179"],
    "Juan Britez": ["MULTI JUAN - 70026504990100112", "M-13 - 70026504990100024"],
    "Jonatan Vargas": ["M-03 - 70026504990100189", "S-03 - 70026504990100056", "S-05 - 70026504990100063", "MULTI JONATAN - 70026504990100134"]
}

# --- FLOTA CORREGIDA (ORTOGRAFIA) ---
FLOTA = {
    "HV-01": {"nombre": "Caterpillar 320D", "unidad": "Horas", "ideal": 18.0}, 
    "JD-01": {"nombre": "John Deere", "unidad": "Horas", "ideal": 15.0},
    "JD-02": {"nombre": "John Deere 6170", "unidad": "Horas", "ideal": 11.0},
    "JD-03": {"nombre": "John Deere 6110", "unidad": "Horas", "ideal": 4.0},
    "JD-04": {"nombre": "John Deere 5090", "unidad": "Horas", "ideal": 8.0},
    "M-01": {"nombre": "Nissan Frontier (Natalia)", "unidad": "KM", "ideal": 9.0},
    "M-02": {"nombre": "Chevrolet S10", "unidad": "KM", "ideal": 8.0},
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

# --- FUNCIONES DE AYUDA ---
def clean_text(text): 
    # Quita ñ y acentos solo para PDF
    replacements = {'ñ': 'n', 'Ñ': 'N', 'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'}
    text = str(text)
    for k, v in replacements.items(): text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

def generar_pdf_master(df_res, df_det, titulo):
    # PDF Corregido y Simple
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    
    # Pagina 1: Resumen
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, clean_text(f"{titulo} - RENDIMIENTO"), 0, 1, 'C')
    pdf.ln(5)
    cols = ["Codigo", "Recorrido", "Litros", "Rendimiento", "Ideal", "Estado"]
    w = [30, 30, 30, 40, 30, 40]
    pdf.set_font('Arial', 'B', 10)
    for i, c in enumerate(cols): pdf.cell(w[i], 10, clean_text(c), 1, 0, 'C')
    pdf.ln()
    pdf.set_font('Arial', '', 10)
    for _, row in df_res.iterrows():
        und = "Km/L"
        if row['Codigo'] in FLOTA and FLOTA[row['Codigo']]['unidad'] == 'Horas': und = "L/H"
        pdf.cell(w[0], 10, clean_text(row['Codigo']), 1)
        pdf.cell(w[1], 10, str(row['Recorrido']), 1)
        pdf.cell(w[2], 10, str(row['Litros']), 1)
        val = row.get('Km/L', 0) if und == "Km/L" else row.get('L/H', 0)
        pdf.cell(w[3], 10, f"{val} {und}", 1)
        pdf.cell(w[4], 10, str(row['Ideal']), 1)
        pdf.cell(w[5], 10, clean_text(row['Estado']), 1)
        pdf.ln()

    # Pagina 2: Historial
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, clean_text(f"{titulo} - HISTORIAL"), 0, 1, 'C')
    pdf.ln(5)
    cols_d = ["Fecha", "Maquina", "Chofer", "Litros", "Lectura", "Rend.", "Alerta"]
    w_d = [30, 45, 40, 20, 30, 30, 40]
    pdf.set_font('Arial', 'B', 9)
    for i, c in enumerate(cols_d): pdf.cell(w_d[i], 10, clean_text(c), 1, 0, 'C')
    pdf.ln()
    pdf.set_font('Arial', '', 8)
    for _, row in df_det.iterrows():
        fecha = row['fecha'].strftime('%d/%m/%Y') if pd.notnull(row['fecha']) else ""
        pdf.cell(w_d[0], 8, fecha, 1)
        pdf.cell(w_d[1], 8, clean_text(str(row.get('nombre_maquina', ''))[:18]), 1)
        pdf.cell(w_d[2], 8, clean_text(str(row.get('chofer', ''))[:15]), 1)
        pdf.cell(w_d[3], 8, str(row.get('litros', 0)), 1)
        pdf.cell(w_d[4], 8, str(row.get('lectura_actual', 0)), 1)
        pdf.cell(w_d[5], 8, clean_text(str(row.get('Rend_Fila', '-'))), 1)
        alerta = clean_text(str(row.get('Alerta_Duplicado', '')))
        if "REPETIDO" in alerta: pdf.set_text_color(255, 0, 0)
        pdf.cell(w_d[6], 8, alerta, 1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- LOGIN (ORIGINAL) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['usuario'] = None
    st.session_state['rol'] = None
    st.session_state['barril_usuario'] = None

def login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h2 style='text-align: center; color: #2E4053;'>Ekos Forestal S.A.</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            user_input = st.selectbox("Seleccione su Usuario:", [""] + list(USUARIOS_DB.keys()))
            pass_input = st.text_input("Contrasena:", type="password")
            if st.form_submit_button("INGRESAR", type="primary"):
                if user_input in USUARIOS_DB and pass_input == USUARIOS_DB[user_input]["pwd"]:
                    st.session_state['logged_in'] = True
                    st.session_state['usuario'] = user_input
                    st.session_state['rol'] = USUARIOS_DB[user_input]["rol"]
                    st.session_state['barril_usuario'] = USUARIOS_DB[user_input]["barril"]
                    st.rerun()
                else: st.error("Credenciales incorrectas.")

def logout():
    st.session_state.clear()
    st.switch_page("Inicio.py")

if not st.session_state['logged_in']:
    login()
    st.stop()

# --- INTERFAZ ---
usuario_actual = st.session_state['usuario']
rol_actual = st.session_state['rol']
barril_actual = st.session_state['barril_usuario']

with st.sidebar:
    st.title("Perfil")
    st.info(f"Usuario: **{usuario_actual}**\n\nRol: {rol_actual.upper()}")
    if st.button("Cerrar Sesion"): logout()
    if st.button("⬅️ Volver al Menu Principal"): st.switch_page("Inicio.py")

st.title("Ekos Forestal / Control")
st.markdown("""<p style='font-size: 14px; color: gray; margin-top: -15px;'>Plataforma integrada de Gestion</p><hr>""", unsafe_allow_html=True)

# PESTAÑAS (SEGÚN ROL)
pestanas = []
if rol_actual == "operador":
    pestanas = ["Registro de Carga", "Mis Registros"] # AGREGADO: Pestaña simple para ellos
elif rol_actual == "admin":
    pestanas = ["Auditoria General", "Verificacion Conciliacion", "Analisis Anual"]

mis_tabs = st.tabs(pestanas)

# --- TAB 1: REGISTRO (ORIGINAL) ---
# (Este bloque es identico a tu version original para no tocar el formato)
if "Registro de Carga" in pestanas:
    with mis_tabs[0]:
        st.subheader(f"Bienvenido, {usuario_actual}")
        if barril_actual == "Acceso Total": op_barril = BARRILES_LISTA; op_origen = BARRILES_LISTA + SURTIDORES
        else: op_barril = [barril_actual]; op_origen = [barril_actual] + SURTIDORES

        operacion = st.radio("Tipo de Operacion:", ["Cargar una Maquina", "Llenar un Barril"], horizontal=True)
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            if "Maquina" in operacion:
                lista_maquinas = [f"{k} - {v['nombre']}" for k, v in FLOTA.items()] + ["➕ OTRO (Manual)"]
                sel_m = st.selectbox("Seleccionar Maquina:", lista_maquinas)
                if sel_m == "➕ OTRO (Manual)":
                    st.info("Datos de Vehiculo Nuevo:")
                    cod_f = st.text_input("Codigo (Ej: M-99)").strip().upper()
                    nom_f = st.text_input("Nombre / Modelo")
                    origen = st.selectbox("Origen del Combustible:", op_origen)
                else:
                    cod_f = sel_m.split(" - ")[0]
                    nom_f = FLOTA[cod_f]['nombre']
                    origen = st.selectbox("Origen del Combustible:", op_origen)
            else: 
                cod_f = st.selectbox("Barril Destino:", op_barril)
                nom_f, origen = cod_f, st.selectbox("Surtidor Origen:", SURTIDORES)

        with c_f2: 
            tipo_comb = st.selectbox("Tipo de Combustible:", TIPOS_COMBUSTIBLE)
            mis_tarjetas = ["Sin Tarjeta"] + TARJETAS_DATA.get(usuario_actual, []) + ["Otra (Manual)"]
            sel_tarjeta = st.selectbox("Tarjeta Utilizada:", mis_tarjetas)
            tarjeta_final = "N/A"
            if sel_tarjeta == "Otra (Manual)":
                t_val = st.text_input("Escriba el N de Tarjeta:")
                if t_val: tarjeta_final = t_val
            elif sel_tarjeta != "Sin Tarjeta": tarjeta_final = sel_tarjeta

        st.markdown("---")
        with st.form("f_reg", clear_on_submit=False):
            c1, c2 = st.columns(2)
            chofer = c1.text_input("Nombre del Chofer")
            fecha = c1.date_input("Fecha de Carga", date.today(), format="DD/MM/YYYY")
            act = c1.text_input("Actividad Realizada")
            lts = c2.number_input("Litros Cargados", min_value=0.0, step=0.1)
            lect = 0.0
            if "Maquina" in operacion: lect = c2.number_input(f"Lectura Actual", min_value=0.0)
            st.markdown("---")
            foto = st.file_uploader("Evidencia (Foto)", type=["jpg", "png", "jpeg"])

            if st.form_submit_button("REVISAR Y GUARDAR DATOS"):
                if not chofer or not act or lts <= 0: st.warning("Faltan datos obligatorios.")
                else:
                    img_str = ""
                    if foto: img_str = base64.b64encode(foto.read()).decode('utf-8')
                    pl = {"fecha": str(fecha), "tipo_operacion": operacion, "codigo_maquina": cod_f, "nombre_maquina": nom_f, "origen": origen, "chofer": chofer, "responsable_cargo": usuario_actual, "actividad": act, "lectura_actual": lect, "litros": lts, "tipo_combustible": tipo_comb, "tarjeta": tarjeta_final, "imagen_base64": img_str}
                    try:
                        requests.post(SCRIPT_URL, json=pl)
                        st.success("✅ Guardado Correctamente")
                    except: st.error("Error de conexion")

# --- TAB EXTRA: MIS REGISTROS (SOLO PARA OPERADOR - VISUALIZACION SIMPLE) ---
if "Mis Registros" in pestanas and rol_actual == "operador":
    with mis_tabs[1]:
        st.subheader("Mis Cargas Recientes")
        try:
            df = pd.read_csv(SHEET_URL)
            df.columns = df.columns.str.strip().str.lower()
            df = df[df['responsable_cargo'] == usuario_actual] # SOLO SUS CARGAS
            if not df.empty:
                cols = ['fecha', 'codigo_maquina', 'litros', 'chofer']
                st.dataframe(df[cols].sort_values(by='fecha', ascending=False), use_container_width=True)
            else: st.info("No tienes registros aun.")
        except: st.error("Error cargando historial")

# --- TAB ADMIN: AUDITORIA (CON TUS MEJORAS PEDIDAS) ---
if "Auditoria General" in pestanas and rol_actual == "admin":
    with mis_tabs[pestanas.index("Auditoria General")]:
        st.subheader("Panel de Control y Auditoria")
        try:
            df = pd.read_csv(SHEET_URL)
            df.columns = df.columns.str.strip().str.lower()
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', dayfirst=True)
            for c in ['litros', 'lectura_actual']:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # 1. CALCULOS DE RENDIMIENTO Y ESTADO
            df = df.sort_values(by=['codigo_maquina', 'fecha'])
            df['Delta_Lect'] = df.groupby('codigo_maquina')['lectura_actual'].diff()
            df['Alerta_Duplicado'] = ""
            # Alerta de duplicados (Mismo dia y maquina)
            dups = df.duplicated(subset=['fecha', 'codigo_maquina'], keep=False)
            df.loc[dups, 'Alerta_Duplicado'] = "⚠️ REPETIDO EN EL DIA"

            def calc_fila(row):
                cod = row['codigo_maquina']
                if cod in FLOTA and row['litros'] > 0 and row['Delta_Lect'] > 0:
                    unit = FLOTA[cod]['unidad']
                    val = row['Delta_Lect'] / row['litros'] if unit == 'KM' else row['litros'] / row['Delta_Lect']
                    return round(val, 2)
                return 0
            df['Rend_Fila'] = df.apply(calc_fila, axis=1)

            def estado_fila(row):
                cod = row['codigo_maquina']
                if cod in FLOTA and row['Rend_Fila'] > 0:
                    ideal = FLOTA[cod]['ideal']
                    unit = FLOTA[cod]['unidad']
                    if unit == 'KM' and row['Rend_Fila'] < ideal * 0.8: return "ALTO CONSUMO"
                    if unit == 'Horas' and row['Rend_Fila'] > ideal * 1.2: return "ALTO CONSUMO"
                    return "Normal"
                return "-"
            df['Estado_Consumo'] = df.apply(estado_fila, axis=1)

            # 2. FILTROS
            c1, c2, c3 = st.columns(3)
            d1 = c1.date_input("Desde", date.today()-timedelta(30))
            d2 = c2.date_input("Hasta", date.today())
            lista_maquinas = ["Todas"] + sorted(df['codigo_maquina'].unique().tolist())
            maq_sel = c3.selectbox("Filtrar Maquina", lista_maquinas)

            mask = (df['fecha'].dt.date >= d1) & (df['fecha'].dt.date <= d2)
            if maq_sel != "Todas": mask = mask & (df['codigo_maquina'] == maq_sel)
            df_fil = df[mask].copy()

            # 3. MOSTRAR ALERTAS
            duplicados_fil = df_fil[df_fil['Alerta_Duplicado'] != ""]
            if not duplicados_fil.empty:
                st.error(f"⚠️ ATENCION: Hay {len(duplicados_fil)} cargas REPETIDAS (misma maquina/mismo dia) en este filtro.")

            # 4. TABLA RESUMEN RENDIMIENTO
            st.markdown("##### Rendimiento del Periodo")
            res_data = []
            if not df_fil.empty:
                for cod in df_fil['codigo_maquina'].unique():
                    dx = df_fil[df_fil['codigo_maquina'] == cod]
                    if cod in FLOTA:
                        l_tot = dx['litros'].sum()
                        rec = dx['lectura_actual'].max() - dx['lectura_actual'].min()
                        ideal = FLOTA[cod]['ideal']
                        kml = rec/l_tot if l_tot > 0 else 0
                        lh = l_tot/rec if rec > 0 else 0
                        est = "Normal"
                        if FLOTA[cod]['unidad'] == 'KM' and kml < ideal*0.8: est = "ALTO CONSUMO"
                        elif FLOTA[cod]['unidad'] == 'Horas' and lh > ideal*1.2: est = "ALTO CONSUMO"
                        
                        res_data.append({"Codigo": cod, "Recorrido": rec, "Litros": l_tot, "Km/L": round(kml,2), "L/H": round(lh,2), "Ideal": ideal, "Estado": est})
            df_res = pd.DataFrame(res_data)
            st.dataframe(df_res, use_container_width=True)

            # 5. TABLA DETALLE
            st.markdown("##### Detalle de Movimientos")
            cols_ver = ['fecha', 'codigo_maquina', 'litros', 'lectura_actual', 'Rend_Fila', 'Estado_Consumo', 'Alerta_Duplicado', 'chofer', 'responsable_cargo']
            def color_alerta(val): return 'background-color: #ffcdd2' if val != "" else ''
            st.dataframe(df_fil[cols_ver].sort_values('fecha', ascending=False).style.applymap(color_alerta, subset=['Alerta_Duplicado']), use_container_width=True)

            # 6. BOTONES DE DESCARGA (SOLO ADMIN, CON TUS CORRECCIONES)
            st.markdown("---")
            st.subheader("Descargas")
            b1, b2, b3 = st.columns(3)
            
            # Boton 1: Historial (Corregido)
            b1.download_button("📄 Excel Historial", data=to_excel(df_fil[cols_ver]), file_name="Historial.xlsx")
            
            # Boton 2: Rendimiento (Nuevo boton separado)
            if not df_res.empty:
                b2.download_button("📊 Excel Rendimiento", data=to_excel(df_res), file_name="Rendimiento.xlsx")
            
            # Boton 3: PDF Maestro (Corregido)
            if b3.button("📑 Generar Informe PDF"):
                try:
                    pdf_bytes = generar_pdf_master(df_res, df_fil, "Reporte Ekos")
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="Reporte_Master.pdf" style="text-decoration:none; color:white; background-color:#d32f2f; padding:10px; border-radius:5px;">⬇️ DESCARGAR PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                except Exception as e: st.error(f"Error PDF: {e}")

        except Exception as e: st.error(f"Error Base de Datos: {e}")
EOF

# REINICIAR SERVIDOR
docker rm -f $(docker ps -aq) && docker build --no-cache -t rrhh-app . && docker run -d -p 80:8501 --restart always rrhh-app
