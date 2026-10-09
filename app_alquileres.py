import streamlit as st
import sqlite3
import datetime
import pandas as pd
import os
import io
from docx import Document

# --- Configuración de la página ---
st.set_page_config(
    page_title="Gestor Inmobiliario - Estudio Jurídico Risso",
    page_icon="⚖️",
    layout="wide"
)

# --- Estética Visual "Dark SaaS Pro" (Inspirada en el estilo de referencia) ---
st.markdown("""
    <style>
    /* Fondo general oscuro estilo panel de control corporativo */
    .stApp {
        background-color: #0e1621;
        color: #e2e8f0;
    }
    
    /* Tipografías institucionales generales */
    h1, h2, h3, h4, p, span, label {
        font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
    }
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* Barra lateral institucional oscura tipo SaaS */
    [data-testid="stSidebar"] {
        background-color: #131c2a;
        border-right: 1px solid #1e293b;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #1e293b;
    }

    /* Tarjetas de métricas estilo oscuro con acento sutil */
    .metric-card {
        background-color: #162235;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border: 1px solid #1e293b;
        border-left: 5px solid #10b981;
        margin-bottom: 15px;
    }

    /* Contenedores con estilo de tarjeta limpia oscura */
    .content-card {
        background-color: #162235;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
        border: 1px solid #1e293b;
    }

    /* Botones principales corporativos con diseño moderno */
    .stButton>button {
        background-color: #10b981;
        color: #0e1621;
        border-radius: 8px;
        border: none;
        font-weight: 700;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #059669;
        color: #ffffff;
        box-shadow: 0 6px 15px rgba(16, 185, 129, 0.4);
        transform: translateY(-1px);
    }
    
    /* Estilo para los inputs, selectores y áreas de texto en modo oscuro */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #0e1621 !important;
        color: #ffffff !important;
        border: 1px solid #2f3e46 !important;
        border-radius: 8px !important;
    }
    
    /* Corrección específica para que el área de texto del contrato sea perfectamente legible en modo oscuro */
    div[data-baseweb="textarea"] textarea {
        background-color: #0e1621 !important;
        color: #f8fafc !important;
        font-family: 'Segoe UI', Courier, monospace !important;
        font-size: 14px !important;
    }
    
    /* Tablas y dataframes en modo oscuro */
    [data-testid="stDataFrame"] {
        border: 1px solid #1e293b;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Base de Datos ---
def obtener_conexion():
    carpeta_actual = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    ruta_db = os.path.join(carpeta_actual, 'mis_alquileres_pro.db')
    return sqlite3.connect(ruta_db)

def inicializar_bd():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alquileres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_propiedad TEXT NOT NULL,
            direccion TEXT NOT NULL,
            inquilino TEXT,
            precio_alquiler REAL DEFAULT 0.0,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            honorarios_cobrados INTEGER DEFAULT 0,
            monto_honorarios REAL DEFAULT 0.0,
            notas TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actualizaciones_precio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alquiler_id INTEGER,
            fecha_actualizacion TEXT,
            nuevo_precio REAL,
            motivo TEXT,
            FOREIGN KEY (alquiler_id) REFERENCES alquileres (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagos_mensuales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alquiler_id INTEGER,
            mes_anio TEXT,
            estado TEXT,
            monto REAL,
            fecha_pago TEXT,
            FOREIGN KEY (alquiler_id) REFERENCES alquileres (id)
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM alquileres")
    if cursor.fetchone()[0] == 0:
        datos_iniciales = [
            ("Departamento Calle San Nicolas", "San Niclas 515 Piso 4 DEPTO A", "Susana Teresa Gomez", 547300.0, "2025-01-01", "2026-12-31", 0, 0.0, ""),
            ("Depto Rosario", "Guemes 2036", "Stella Maris Cima", 464000.0, "2025-06-01", "2027-05-31", 0, 0.0, ""),
            ("Oficina Pueyrredón", "Pueyrredón 1171 PB OF 2", "Romina Abatte", 342000.0, "2026-01-01", "2027-12-31", 0, 0.0, ""),
            ("Casa 3 de Febrero", "3 de Febrero 351", "Alvarez Sofia", 490300.0, "2025-01-07", "2027-07-31", 0, 0.0, ""),
            ("Casa Calle Moreno 29", "Moreno 29", "Ivana Maricel Orona", 586000.0, "2026-03-01", "2028-02-28", 0, 0.0, ""),
            ("Casa planta alta Colon", "BV Colon 525", "Monica Raimundo", 550000.0, "2026-10-01", "2028-09-30", 1, 300000.0, "")
        ]
        cursor.executemany('''
            INSERT INTO alquileres (nombre_propiedad, direccion, inquilino, precio_alquiler, fecha_inicio, fecha_fin, honorarios_cobrados, monto_honorarios, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', datos_iniciales)
        conn.commit()

    conn.close()

inicializar_bd()

# --- Menú Lateral Profesional Dark ---
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 10px; background: linear-gradient(135deg, #162235 0%, #0e1621 100%); border-radius: 10px; border: 1px solid #1e293b; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);'>
            <div style='font-size: 35px; margin-bottom: 5px;'>⚖️</div>
            <h2 style='color: #ffffff !important; margin: 0; font-size: 15px; font-weight: 700; letter-spacing: 0.5px;'>ESTUDIO JURÍDICO</h2>
            <h1 style='color: #10b981 !important; margin: 0; font-size: 22px; font-weight: 800; letter-spacing: 1px;'>RISSO</h1>
            <p style='font-size: 9px; color: #94a3b8; margin-top: 8px; text-transform: uppercase; letter-spacing: 1.5px;'>Gestión Inmobiliaria Pro</p>
        </div>
    """, unsafe_allow_html=True)
    
    opcion = st.radio("Navegación del Sistema:", [
        "📊 Panel y Gráficos", 
        "➕ Cargar Propiedad", 
        "📈 Actualizar Precios e Historial", 
        "🧮 Calculadora de Ajustes (ICL/IPC)", 
        "💵 Control de Pagos y Recibos",
        "📝 Generador de Contratos",
        "🗑️ Eliminar Propiedad"
    ])

conn = obtener_conexion()
df_alquileres = pd.read_sql("SELECT * FROM alquileres", conn)
conn.close()

hoy = datetime.date.today()
un_mes_despues = hoy + datetime.timedelta(days=30)

if opcion == "📊 Panel y Gráficos":
    st.markdown("""
        <div style='padding: 22px; background: linear-gradient(90deg, #162235 0%, #1e293b 100%); border-radius: 10px; color: white; margin-bottom: 20px; border: 1px solid #2a3b50; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
            <h1 style='color: #ffffff !important; margin: 0; font-size: 26px; font-weight: 700;'>Panel General de Administración</h1>
            <p style='color: #94a3b8; margin: 5px 0 0 0; font-size: 13px;'>Control centralizado de contratos, valores vigentes y estadísticas clave del estudio.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if df_alquileres.empty:
        st.info("Todavía no hay propiedades cargadas en el sistema.")
    else:
        total_propiedades = len(df_alquileres)
        recaudacion_potencial = df_alquileres['precio_alquiler'].sum()
        vencidos_o_proximos = 0
        
        for _, row in df_alquileres.iterrows():
            if row['fecha_fin']:
                try:
                    f_fin = datetime.date.fromisoformat(row['fecha_fin'])
                    if f_fin <= un_mes_despues:
                        vencidos_o_proximos += 1
                except ValueError:
                    pass

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
                <div class="metric-card">
                    <p style="color: #94a3b8; font-size: 11px; margin: 0; font-weight: 700; letter-spacing: 0.5px;">PROPIEDADES ACTIVAS</p>
                    <h2 style="color: #ffffff !important; margin: 6px 0 0 0; font-size: 28px; font-weight: 800;">{total_propiedades}</h2>
                </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
                <div class="metric-card">
                    <p style="color: #94a3b8; font-size: 11px; margin: 0; font-weight: 700; letter-spacing: 0.5px;">RECAUDACIÓN MENSUAL</p>
                    <h2 style="color: #10b981 !important; margin: 6px 0 0 0; font-size: 26px; font-weight: 800;">${recaudacion_potencial:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #ef4444;">
                    <p style="color: #94a3b8; font-size: 11px; margin: 0; font-weight: 700; letter-spacing: 0.5px;">VENCIMIENTOS (< 30 DÍAS)</p>
                    <h2 style="color: #ef4444 !important; margin: 6px 0 0 0; font-size: 28px; font-weight: 800;">{vencidos_o_proximos}</h2>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.subheader("📋 Listado Rápido de Inmuebles")
        st.dataframe(df_alquileres[['nombre_propiedad', 'direccion', 'inquilino', 'precio_alquiler', 'fecha_fin']], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.subheader("📈 Distribución de Ingresos por Inmueble")
        if not df_alquileres.empty:
            chart_data = df_alquileres.set_index('nombre_propiedad')[['precio_alquiler']]
            st.bar_chart(chart_data)
        st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "➕ Cargar Propiedad":
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.header("➕ Cargar Nueva Propiedad y Contrato")
    
    with st.form("form_carga"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre / Identificación de la Propiedad *")
            direccion = st.text_input("Dirección *")
            inquilino = st.text_input("Nombre del Inquilino")
            precio = st.number_input("Precio Inicial del Alquiler ($)", min_value=0.0, step=1000.0)
        
        with col2:
            f_inicio = st.date_input("Fecha Inicio Contrato", value=hoy)
            f_fin = st.date_input("Fecha Fin Contrato", value=hoy + datetime.timedelta(days=365))
            honorarios_si = st.checkbox("¿Se cobraron honorarios de redacción?")
            monto_hon = st.number_input("Monto Honorarios ($)", min_value=0.0, step=500.0)
            
        notas = st.text_area("Notas Adicionales (Cláusulas especiales, CBU, etc.)")
        
        submitted = st.form_submit_button("Guardar Propiedad en el Sistema")
        if submitted:
            if not nombre or not direccion:
                st.error("El nombre de la propiedad y la dirección son obligatorios.")
            else:
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alquileres (nombre_propiedad, direccion, inquilino, precio_alquiler, fecha_inicio, fecha_fin, honorarios_cobrados, monto_honorarios, notas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (nombre, direccion, inquilino, precio, str(f_inicio), str(f_fin), 1 if honorarios_si else 0, monto_hon, notas))
                conn.commit()
                conn.close()
                st.success("¡Propiedad y contrato guardados con éxito!")
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "📈 Actualizar Precios e Historial":
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.header("📈 Historial y Actualizaciones de Precios")
    
    if df_alquileres.empty:
        st.info("No hay propiedades cargadas.")
    else:
        propiedad_seleccionada = st.selectbox(
            "Seleccioná la propiedad:",
            df_alquileres['nombre_propiedad'].tolist()
        )
        
        prop_info = df_alquileres[df_alquileres['nombre_propiedad'] == propiedad_seleccionada].iloc[0]
        alq_id = prop_info['id']
        
        st.markdown(f"**Dirección:** {prop_info['direccion']} &nbsp;|&nbsp; **Precio Vigente:** <span style='color:#10b981; font-weight:bold;'>${prop_info['precio_alquiler']:,.2f}</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form("form_precio"):
            st.subheader("Registrar Nuevo Ajuste")
            nuevo_precio = st.number_input("Nuevo Monto ($)", min_value=0.0, step=1000.0)
            fecha_act = st.date_input("Fecha de Actualización", value=hoy)
            motivo = st.text_input("Motivo / Índice:", value="Actualización ICL / Cuatrimestral")
            
            if st.form_submit_button("Guardar Actualización"):
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO actualizaciones_precio (alquiler_id, fecha_actualizacion, nuevo_precio, motivo)
                    VALUES (?, ?, ?, ?)
                ''', (alq_id, str(fecha_act), nuevo_precio, motivo))
                cursor.execute('UPDATE alquileres SET precio_alquiler = ? WHERE id = ?', (nuevo_precio, alq_id))
                conn.commit()
                conn.close()
                st.success("¡Actualización guardada correctamente!")
                st.rerun()

        st.divider()
        st.subheader("Historial Registrado")
        conn = obtener_conexion()
        df_hist = pd.read_sql(f"SELECT fecha_actualizacion AS Fecha, nuevo_precio AS 'Nuevo Precio ($)', motivo AS Motivo FROM actualizaciones_precio WHERE alquiler_id = {alq_id} ORDER BY fecha_actualizacion DESC", conn)
        conn.close()
        if df_hist.empty:
            st.write("Sin registros previos.")
        else:
            st.dataframe(df_hist, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "🧮 Calculadora de Ajustes (ICL/IPC)":
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.header("🧮 Calculadora de Actualización de Alquileres")
    
    if df_alquileres.empty:
        st.info("Cargá primero una propiedad para realizar cálculos.")
    else:
        prop_sel = st.selectbox("Seleccionar Inmueble para simular ajuste:", df_alquileres['nombre_propiedad'].tolist())
        p_info = df_alquileres[df_alquileres['nombre_propiedad'] == prop_sel].iloc[0]
        
        precio_actual = p_info['precio_alquiler']
        st.info
        
