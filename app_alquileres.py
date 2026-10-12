  import streamlit as st
import sqlite3
import datetime
import pandas as pd
import os
import io
import hashlib
from docx import Document

# --- Configuración de la página ---
st.set_page_config(
    page_title="Gestor Inmobiliario Pro",
    page_icon="🏢",
    layout="wide"
)

# --- Función para encriptar contraseñas ---
def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Base de Datos y Estructura Multiusuario ---
def obtener_conexion():
    carpeta_actual = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    ruta_db = os.path.join(carpeta_actual, 'mis_alquileres_pro.db')
    return sqlite3.connect(ruta_db)

def inicializar_bd():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Tabla de Organizaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_org TEXT NOT NULL UNIQUE,
            activa INTEGER DEFAULT 1
        )
    ''')
    
    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nombre_completo TEXT,
            organizacion_id INTEGER,
            es_admin_general INTEGER DEFAULT 0,
            permiso_escritura INTEGER DEFAULT 1,
            aprobado INTEGER DEFAULT 0,
            FOREIGN KEY (organizacion_id) REFERENCES organizaciones (id)
        )
    ''')
    
    # Asegurar compatibilidad de columnas si la tabla ya existía
    cursor.execute("PRAGMA table_info(usuarios)")
    cols_u = [col[1] for col in cursor.fetchall()]
    if "permiso_escritura" not in cols_u:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN permiso_escritura INTEGER DEFAULT 1")
    if "aprobado" not in cols_u:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN aprobado INTEGER DEFAULT 1")

    cursor.execute("PRAGMA table_info(organizaciones)")
    cols_o = [col[1] for col in cursor.fetchall()]
    if "activa" not in cols_o:
        cursor.execute("ALTER TABLE organizaciones ADD COLUMN activa INTEGER DEFAULT 1")

    # Tabla de Alquileres
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alquileres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organizacion_id INTEGER,
            nombre_propiedad TEXT NOT NULL,
            direccion TEXT NOT NULL,
            inquilino TEXT,
            precio_alquiler REAL DEFAULT 0.0,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            honorarios_cobrados INTEGER DEFAULT 0,
            monto_honorarios REAL DEFAULT 0.0,
            notas TEXT,
            FOREIGN KEY (organizacion_id) REFERENCES organizaciones (id)
        )
    ''')
    
    # Tabla de Actualizaciones de Precios
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
    
    # Tabla de Pagos Mensuales
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
    
    # Crear cuenta Superadministrador Maestro si no existe
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE es_admin_general = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR IGNORE INTO organizaciones (nombre_org, activa) VALUES ('Plataforma Central', 1)")
        cursor.execute("SELECT id FROM organizaciones WHERE nombre_org = 'Plataforma Central'")
        org_id = cursor.fetchone()[0]
        
        pass_maestro = encriptar_password("admin123")
        cursor.execute('''
            INSERT INTO usuarios (email, password, nombre_completo, organizacion_id, es_admin_general, permiso_escritura, aprobado)
            VALUES (?, ?, ?, ?, 1, 1, 1)
        ''', ("admin@gestor.com", pass_maestro, "Administrador Maestro", org_id))
        conn.commit()

    # Blindaje de seguridad: Solo el mail maestro puede ser admin general
    cursor.execute("UPDATE usuarios SET es_admin_general = 0 WHERE email != 'admin@gestor.com'")
    conn.commit()

    conn.close()

inicializar_bd()

# --- Estética Visual "Dark SaaS Pro" ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1621;
        color: #f1f5f9;
    }
    h1, h2, h3, h4, p, span {
        font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
    }
    h1, h2, h3 {
        color: #ffffff !important;
    }
    label, .stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stTextArea label, .stCheckbox label {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    textarea, .stTextArea textarea {
        background-color: #131c2a !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] {
        background-color: #131c2a;
        border-right: 1px solid #1e293b;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #1e293b;
    }
    .metric-card {
        background-color: #162235;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border: 1px solid #1e293b;
        border-left: 5px solid #10b981;
        margin-bottom: 15px;
    }
    .content-card {
        background-color: #162235;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
        border: 1px solid #1e293b;
    }
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
    .stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] {
        background-color: #131c2a !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #1e293b;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Control de Sesión ---
if 'usuario_logueado' not in st.session_state:
    st.session_state['usuario_logueado'] = None

# --- Pantalla de Autenticación (Login / Solicitud) ---
if st.session_state['usuario_logueado'] is None:
    st.markdown("<br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        st.markdown("""
            <div style='text-align: center; padding: 25px; background: #162235; border-radius: 15px; border: 1px solid #1e293b; box-shadow: 0 8px 25px rgba(0,0,0,0.4);'>
                <div style='font-size: 40px; margin-bottom: 5px;'>🏢</div>
                <h2 style='color: #ffffff !important; margin: 0;'>Gestor Inmobiliario Pro</h2>
                <p style='color: #94a3b8; font-size: 13px; margin-top: 5px;'>Plataforma multiusuario de gestión y contratos</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Solicitar Cuenta / Organización"])
        
        with tab_login:
            with st.form("form_login"):
                email_ingresado = st.text_input("Correo Electrónico")
                pass_ingresado = st.text_input("Contraseña", type="password")
                btn_login = st.form_submit_button("Ingresar al Sistema")
                
                if btn_login:
                    conn = obtener_conexion()
                    cursor = conn.cursor()
                    pass_hash = encriptar_password(pass_ingresado)
                    cursor.execute("""
                        SELECT u.id, u.email, u.nombre_completo, u.organizacion_id, u.es_admin_general, u.permiso_escritura, u.aprobado, o.activa 
                        FROM usuarios u
                        JOIN organizaciones o ON u.organizacion_id = o.id
                        WHERE u.email = ? AND u.password = ?
                    """, (email_ingresado, pass_hash))
                    user = cursor.fetchone()
                    conn.close()
                    
                    if user:
                        if user[6] == 0: # aprobado == 0
                            st.warning("⚠️ Tu cuenta se encuentra pendiente de aprobación por el Administrador Maestro.")
                        elif user[7] == 0: # organizacion activa == 0
                            st.error("🚫 La organización asociada a esta cuenta se encuentra suspendida. Contactá al soporte.")
                        else:
                            st.session_state['usuario_logueado'] = {
                                "id": user[0],
                                "email": user[1],
                                "nombre": user[2],
                                "org_id": user[3],
                                "es_admin_general": user[4],
                                "permiso_escritura": user[5]
                            }
                            st.success("¡Ingreso exitoso!")
                            st.rerun()
                    else:
                        st.error("Credenciales incorrectas o usuario no encontrado.")

        with tab_registro:
            st.write("Completá los datos para solicitar una nueva organización en la plataforma. El Administrador Maestro evaluará tu solicitud y te creará el acceso.")
            with st.form("form_registro"):
                reg_nombre = st.text_input("Nombre y Apellido")
                reg_email = st.text_input("Correo Electrónico de Contacto")
                reg_org = st.text_input("Nombre de tu Estudio / Inmobiliaria")
                reg_pass = st.text_input("Contraseña deseada", type="password")
                btn_reg = st.form_submit_button("Enviar Solicitud")
                
                if btn_reg:
                    if reg_nombre and reg_email and reg_org and reg_pass:
                        try:
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO organizaciones (nombre_org, activa) VALUES (?, 1)", (reg_org,))
                            org_id = cursor.lastrowid
                            
                            pass_h = encriptar_password(reg_pass)
                            cursor.execute('''
                                INSERT INTO usuarios (email, password, nombre_completo, organizacion_id, es_admin_general, permiso_escritura, aprobado)
                                VALUES (?, ?, ?, ?, 0, 1, 0)
                            ''', (reg_email, pass_h, reg_nombre, org_id))
                            conn.commit()
                            conn.close()
                            st.success("¡Solicitud enviada correctamente! El Administrador Maestro la revisará y habilitará pronto.")
                        except sqlite3.IntegrityError:
                            st.error("El correo o el nombre de organización ya están registrados.")
                    else:
                        st.warning("Completá todos los campos obligatorios.")
    st.stop()

# --- Usuario Logueado ---
user_info = st.session_state['usuario_logueado']
org_id_actual = user_info['org_id']
tiene_escritura = user_info['permiso_escritura'] == 1

with st.sidebar:
    st.markdown(f"""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #162235 0%, #0e1621 100%); border-radius: 10px; border: 1px solid #1e293b; margin-bottom: 15px;'>
            <div style='font-size: 28px;'>🏢</div>
            <h3 style='color: #ffffff !important; margin: 5px 0 0 0; font-size: 15px;'>Gestión Inmobiliaria</h3>
            <p style='font-size: 11px; color: #10b981; margin: 4px 0 0 0;'><b>{user_info['nombre']}</b></p>
            <p style='font-size: 10px; color: #94a3b8; margin: 2px 0 0 0;'>{'👑 Admin Maestro' if user_info['es_admin_general']==1 else ('✍️ Editor' if tiene_escritura else '👁️ Solo Lectura')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    menu_opciones = [
        "📊 Panel y Gráficos", 
        "➕ Cargar Propiedad", 
        "📈 Actualizar Precios e Historial", 
        "🧮 Calculadora de Ajustes (ICL/IPC)", 
        "💵 Control de Pagos y Recibos",
        "📝 Generador de Contratos",
        "🗑️ Eliminar Propiedad"
    ]
    
    # EXCLUSIVO: Solo la cuenta maestra ve el panel maestro
    if user_info['es_admin_general'] == 1 and user_info['email'] == "admin@gestor.com":
        menu_opciones.append("👑 Panel Maestro (Control Global)")

    opcion = st.radio("Navegación del Sistema:", menu_opciones)
    
    st.markdown("---")
    if st.button("🚪 Cerrar Sesión"):
        st.session_state['usuario_logueado'] = None
        st.rerun()

# Cargar datos filtrados de forma segura por el organizacion_id del usuario actual
conn = obtener_conexion()
df_alquileres = pd.read_sql("SELECT * FROM alquileres WHERE organizacion_id = ?", conn, params=(org_id_actual,))
conn.close()

hoy = datetime.date.today()
un_mes_despues = hoy + datetime.timedelta(days=30)

if opcion == "📊 Panel y Gráficos":
    st.markdown("""
        <div style='padding: 22px; background: linear-gradient(90deg, #162235 0%, #1e293b 100%); border-radius: 10px; color: white; margin-bottom: 20px; border: 1px solid #2a3b50; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
            <h1 style='color: #ffffff !important; margin: 0; font-size: 26px; font-weight: 700;'>Panel General de Administración</h1>
            <p style='color: #94a3b8; margin: 5px 0 0 0; font-size: 13px;'>Control centralizado de propiedades e ingresos de tu organización.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if df_alquileres.empty:
        st.info("Todavía no hay propiedades cargadas para tu organización. Utiliza '➕ Cargar Propiedad' en el menú lateral.")
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

elif opcion == "➕ Cargar Propiedad":
    if not tiene_escritura:
        st.error("🔒 Tu cuenta tiene perfil de **Solo Lectura**. No tenés permisos para cargar nuevas propiedades.")
    else:
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
                        INSERT INTO alquileres (organizacion_id, nombre_propiedad, direccion, inquilino, precio_alquiler, fecha_inicio, fecha_fin, honorarios_cobrados, monto_honorarios, notas)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (org_id_actual, nombre, direccion, inquilino, precio, str(f_inicio), str(f_fin), 1 if honorarios_si else 0, monto_hon, notas))
                    conn.commit()
                    conn.close()
                    st.success("¡Propiedad guardada con éxito!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "📈 Actualizar Precios e Historial":
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.header("📈 Historial y Actualizaciones de Precios")
    
    if df_alquileres.empty:
        st.info("No hay propiedades cargadas.")
    else:
        propiedad_seleccionada = st.selectbox("Seleccioná la propiedad:", df_alquileres['nombre_propiedad'].tolist())
        prop_info = df_alquileres[df_alquileres['nombre_propiedad'] == propiedad_seleccionada].iloc[0]
        alq_id = prop_info['id']
        
        st.markdown(f"**Dirección:** {prop_info['direccion']} &nbsp;|&nbsp; **Precio Vigente:** <span style='color:#10b981; font-weight:bold;'>${prop_info['precio_alquiler']:,.2f}</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not tiene_escritura:
            st.info("👁️ Estás en modo visualización. Solo los editores pueden registrar modificaciones de precios.")
        else:
            with st.form("form_precio"):
                st.subheader("Registrar Nuevo Ajuste")
                nuevo_precio = st.number_input("Nuevo Monto ($)", min_value=0.0, step=1000.0)
                fecha_act = st.date_input("Fecha de Actualización", value=hoy)
                motivo = st.text_input("Motivo / Índice:", value="Actualización ICL / Cuatrimestral")
                
                if st.form_submit_button("Guardar Actualización"):
                    conn = obtener_conexion()
                    cursor = conn.cursor()
                    # 1. Guardar en el historial de precios
                    cursor.execute('''
                        INSERT INTO actualizaciones_precio (alquiler_id, fecha_actualizacion, nuevo_precio, motivo)
                        VALUES (?, ?, ?, ?)
                    ''', (alq_id, str(fecha_act), nuevo_precio, motivo))
                    # 2. Actualizar el precio actual en la tabla principal de alquileres
                    cursor.execute('''
                        UPDATE alquileres 
                        SET precio_alquiler = ? 
                        WHERE id = ?
                    ''', (nuevo_precio, alq_id))
                    conn.commit()
                    conn.close()
                    st.success("¡Actualización guardada y precio vigente actualizado correctamente!")
                    st.rerun()

        st.divider()
        st.subheader("Historial Registrado")
        conn = obtener_conexion()
        df_hist = pd.read_sql("SELECT fecha_actualizacion AS Fecha, nuevo_precio AS 'Nuevo Precio ($)', motivo AS Motivo FROM actualizaciones_precio WHERE alquiler_id = ? ORDER BY fecha_actualizacion DESC", conn, params=(alq_id,))
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
        st.info(f"💰 Alquiler base actual: **${precio_actual:,.2f}**")
        
        st.markdown("### 🌐 Enlaces Oficiales de Consulta (BCRA)")
        st.markdown("""
        - 🔗 [Principales Variables y Series del BCRA](https://www.bcra.gob.ar/principales-variables/)
        - 🔗 [Estadísticas e Indicadores Monetarios (BCRA)](https://www.bcra.gob.ar/)
        """)
        
        st.divider()
        coef_ingresado = st.number_input("Ingresá el Coeficiente obtenido de la web oficial (Ej: 1.35):", min_value=1.0, value=1.30, step=0.01)
        
        if st.button("Calcular Nuevo Alquiler"):
            nuevo_calculado = precio_actual * coef_ingresado
            st.session_state['nuevo_calculado'] = nuevo_calculado
            st.session_state['coef_usado'] = coef_ingresado

        if 'nuevo_calculado' in st.session_state:
            st.divider()
            st.success("¡Cálculo realizado con éxito!")
            st.write(f"- **Coeficiente Aplicado:** {st.session_state['coef_usado']}")
            st.markdown(f"## 🎯 **Nuevo Alquiler Ajustado: ${st.session_state['nuevo_calculado']:,.2f}**")
    st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "💵 Control de Pagos y Recibos":
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.header("💵 Control de Pagos Mensuales y Emisión de Recibos")
    
    if df_alquileres.empty:
        st.info("No hay propiedades registradas.")
    else:
        p_pago = st.selectbox("Seleccionar Propiedad:", df_alquileres['nombre_propiedad'].tolist(), key="p_pago_sel")
        prop_reg = df_alquileres[df_alquileres['nombre_propiedad'] == p_pago].iloc[0]
        alq_id_pago = prop_reg['id']
        mes_actual_str = datetime.date.today().strftime("%Y-%m")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            mes_input = st.text_input("Mes y Año (YYYY-MM):", value=mes_actual_str)
            estado_pago = st.selectbox("Estado del Pago:", ["Pagado 🟢", "Pendiente 🔴", "Atrasado ⚠️"])
        with col_p2:
            monto_pago = st.number_input("Monto Abonado ($):", value=float(prop_reg['precio_alquiler']), min_value=0.0)
            fecha_pago_efectiva = st.date_input("Fecha de Efectivización:", value=hoy)
            
        if not tiene_escritura:
            st.info("👁️ Estás en modo lectura. No podés registrar pagos nuevos.")
        else:
            if st.button("Registrar / Actualizar Estado de Pago"):
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM pagos_mensuales WHERE alquiler_id = ? AND mes_anio = ?", (alq_id_pago, mes_input))
                existe = cursor.fetchone()
                if existe:
                    cursor.execute("UPDATE pagos_mensuales SET estado = ?, monto = ?, fecha_pago = ? WHERE id = ?", 
                                   (estado_pago, monto_pago, str(fecha_pago_efectiva), existe[0]))
                else:
                    cursor.execute("INSERT INTO pagos_mensuales (alquiler_id, mes_anio, estado, monto, fecha_pago) VALUES (?, ?, ?, ?, ?)",
                                   (alq_id_pago, mes_input, estado_pago, monto_pago, str(fecha_pago_efectiva)))
                conn.commit()
                conn.close()
                st.success("¡Pago actualizado con éxito!")
                st.rerun()

        st.divider()
        st.subheader("📲 Generador de Recibo Digital para WhatsApp")
        inquilino_nombre = prop_reg['inquilino'] if prop_reg['inquilino'] else "[Inquilino]"
        texto_whatsapp = f"""*RECIBO DE PAGO - ALQUILER* 🏠
-----------------------------------
*Propiedad:* {prop_reg['nombre_propiedad']}
*Dirección:* {prop_reg['direccion']}
*Inquilino:* {inquilino_nombre}
*Periodo:* {mes_input}
*Monto:* ${monto_pago:,.2f}
*Estado:* {estado_pago}
*Fecha:* {fecha_pago_efectiva}
-----------------------------------
_Gestión Inmobiliaria Pro_"""
        st.text_area("Copiá este mensaje para WhatsApp:", value=texto_whatsapp, height=180)
    st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "📝 Generador de Contratos":
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.header("📝 Generador Automático de Contratos (.docx)")
    
    if df_alquileres.empty:
        st.info("No hay propiedades registradas.")
    else:
        prop_c = st.selectbox("Seleccionar Inmueble:", df_alquileres['nombre_propiedad'].tolist(), key="prop_contrato")
        p_c_info = df_alquileres[df_alquileres['nombre_propiedad'] == prop_c].iloc[0]
        
        with st.expander("🛠️ Datos Complementarios de las Partes", expanded=True):
            col_cc1, col_cc2 = st.columns(2)
            with col_cc1:
                locador_nombre = st.text_input("Nombre Locador", value="PROPIETARIO")
                locador_dni = st.text_input("DNI Locador", value="[DNI]")
                locador_dom = st.text_input("Domicilio Locador", value="[Domicilio]")
            with col_cc2:
                fiador_nombre = st.text_input("Nombre Garante", value="[Garante]")
                fiador_dni = st.text_input("DNI Garante", value="[DNI]")
                fiador_dom = st.text_input("Domicilio Garante", value="[Domicilio]")

        contrato_modelo_base = f"""CONTRATO DE LOCACIÓN DE INMUEBLE
Entre el Sr. {locador_nombre}, DNI N° {locador_dni}, con domicilio en {locador_dom}, en adelante “el locador”, y el Sr./Sra. {p_c_info['inquilino']} con D.N.I. Nº [Completar] con domicilio en {p_c_info['direccion']}, en adelante “el locatario”, se conviene celebrar el presente contrato:

PRIMERA: El locador da en locación el inmueble ubicado en {p_c_info['direccion']} destinado a vivienda.
SEGUNDA: El plazo será de dos (2) años desde el {p_c_info['fecha_inicio']} hasta el {p_c_info['fecha_fin']}.
TERCERA: El valor mensual se fija en la suma de PESOS (${p_c_info['precio_alquiler']:,.2f}), actualizable trimestralmente por índice ICL.

En prueba de conformidad, se firman dos ejemplares."""

        texto_editado = st.text_area("Contrato Editable:", value=contrato_modelo_base, height=300)

        if st.button("📥 Descargar Contrato en Word (.docx)"):
            doc = Document()
            doc.add_heading(f"Contrato - {p_c_info['nombre_propiedad']}", level=1)
            for parrafo in texto_editado.split("\n\n"):
                if parrafo.strip():
                    doc.add_paragraph(parrafo.strip())
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            st.download_button(
                label="⬇️ Descargar archivo .docx",
                data=bio,
                file_name=f"Contrato_{p_c_info['nombre_propiedad'].replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "🗑️ Eliminar Propiedad":
    if not tiene_escritura:
        st.error("🔒 Tu cuenta tiene perfil de **Solo Lectura**.")
    else:
        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.header("🗑️ Baja de Propiedades y Contratos")
        
        if df_alquileres.empty:
            st.info("No hay propiedades registradas.")
        else:
            prop_a_borrar = st.selectbox("Seleccioná la propiedad a eliminar:", df_alquileres['nombre_propiedad'].tolist())
            p_del_info = df_alquileres[df_alquileres['nombre_propiedad'] == prop_a_borrar].iloc[0]
            prop_id = p_del_info['id']
            
            st.error(f"⚠️ Atención: Estás por eliminar **{p_del_info['nombre_propiedad']}**.")
            confirmacion = st.checkbox("Confirmo que deseo dar de baja definitivamente este inmueble.")
            
            if st.button("Eliminar Inmueble"):
                if confirmacion:
                    conn = obtener_conexion()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM actualizaciones_precio WHERE alquiler_id = ?", (prop_id,))
                    cursor.execute("DELETE FROM pagos_mensuales WHERE alquiler_id = ?", (prop_id,))
                    cursor.execute("DELETE FROM alquileres WHERE id = ?", (prop_id,))
                    conn.commit()
                    conn.close()
                    st.success("¡Propiedad eliminada!")
                    st.rerun()
                else:
                    st.warning("Marcá la casilla de confirmación.")
        st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "👑 Panel Maestro (Control Global)" and user_info['es_admin_general'] == 1 and user_info['email'] == "admin@gestor.com":
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.header("👑 Panel de Control Maestro (Superadministrador)")
    
    tab_orgs, tab_solicitudes, tab_usuarios, tab_gestion_usuarios = st.tabs([
        "🏢 Organismos", 
        "🔔 Solicitudes", 
        "👤 Crear Usuario", 
        "⚙️ Gestionar Permisos y Estados de Usuarios"
    ])
    
    with tab_orgs:
        st.subheader("Organizaciones Registradas")
        conn = obtener_conexion()
        df_orgs = pd.read_sql("SELECT id, nombre_org AS Organización, CASE WHEN activa=1 THEN 'Activa 🟢' ELSE 'Suspendida 🔴' END AS Estado FROM organizaciones", conn)
        conn.close()
        st.dataframe(df_orgs, use_container_width=True)
        
        org_id_cambio = st.number_input("ID de la Organización a modificar:", min_value=1, step=1, key="org_cambio_id")
        nuevo_estado = st.selectbox("Acción sobre la Organización:", ["Activar 🟢", "Suspender 🔴"], key="org_nuevo_est")
        if st.button("Actualizar Estado de Organización"):
            val_activa = 1 if "Activar" in nuevo_estado else 0
            conn = obtener_conexion()
            cursor = conn.cursor()
            cursor.execute("UPDATE organizaciones SET activa = ? WHERE id = ?", (val_activa, org_id_cambio))
            conn.commit()
            conn.close()
            st.success("¡Estado actualizado!")
            st.rerun()

    with tab_solicitudes:
        st.subheader("Solicitudes de Registro Pendientes")
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.nombre_completo, u.email, o.nombre_org, o.id 
            FROM usuarios u 
            JOIN organizaciones o ON u.organizacion_id = o.id 
            WHERE u.aprobado = 0
        ''')
        pendientes = cursor.fetchall()
        conn.close()
        
        if not pendientes:
            st.info("No hay solicitudes pendientes.")
        else:
            for p in pendientes:
                col_s1, col_s2, col_s3 = st.columns([2, 2, 1])
                with col_s1:
                    st.markdown(f"**{p[1]}** ({p[2]})")
                with col_s2:
                    st.markdown(f"Organización: <b>{p[3]}</b>", unsafe_allow_html=True)
                with col_s3:
                    if st.button(f"Aprobar Org ID {p[4]}", key=f"aprobar_org_{p[4]}"):
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE usuarios SET aprobado = 1 WHERE organizacion_id = ?", (p[4],))
                        conn.commit()
                        conn.close()
                        st.success(f"¡Organización aprobada con éxito!")
                        st.rerun()

    with tab_usuarios:
        st.subheader("Crear Usuario / Empleado para una Organización")
        conn = obtener_conexion()
        orgs_list = pd.read_sql("SELECT id, nombre_org FROM organizaciones", conn)
        conn.close()
        
        if orgs_list.empty:
            st.warning("No hay organizaciones creadas.")
        else:
            with st.form("form_crear_usuario_maestro"):
                u_email = st.text_input("Correo electrónico del empleado/usuario")
                u_pass = st.text_input("Contraseña temporal", type="password")
                u_nombre = st.text_input("Nombre y Apellido")
                
                dict_orgs = dict(zip(orgs_list['nombre_org'], orgs_list['id']))
                org_elegida = st.selectbox("Seleccionar Organización", list(dict_orgs.keys()))
                
                u_permiso = st.selectbox("Permisos del Usuario:", ["Editor (Puede cargar, cobrar y editar) ✍️", "Solo Lectura (Solo puede ver datos) 👁️"])
                
                btn_crear_u = st.form_submit_button("Crear y Habilitar Usuario")
                if btn_crear_u:
                    if u_email and u_pass and u_nombre:
                        org_id_sel = dict_orgs[org_elegida]
                        escritura_val = 1 if "Editor" in u_permiso else 0
                        try:
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            pass_h = encriptar_password(u_pass)
                            cursor.execute('''
                                INSERT INTO usuarios (email, password, nombre_completo, organizacion_id, es_admin_general, permiso_escritura, aprobado)
                                VALUES (?, ?, ?, ?, 0, ?, 1)
                            ''', (u_email, pass_h, u_nombre, org_id_sel, escritura_val))
                            conn.commit()
                            conn.close()
                            st.success(f"¡Usuario {u_nombre} creado con éxito!")
                        except sqlite3.IntegrityError:
                            st.error("El correo electrónico ya se encuentra registrado.")
                    else:
                        st.warning("Completá todos los campos.")

    with tab_gestion_usuarios:
        st.subheader("Gestionar Usuarios de las Organizaciones")
        conn = obtener_conexion()
        df_todos_usuarios = pd.read_sql("""
            SELECT u.id, u.nombre_completo AS Nombre, u.email AS Correo, o.nombre_org AS Organización, 
                   CASE WHEN u.permiso_escritura=1 THEN 'Editor ✍️' ELSE 'Solo Lectura 👁️' END AS Permisos,
                   CASE WHEN u.aprobado=1 THEN 'Activo 🟢' ELSE 'Suspendido 🔴' END AS Estado
            FROM usuarios u
            JOIN organizaciones o ON u.organizacion_id = o.id
            WHERE u.es_admin_general = 0
        """, conn)
        conn.close()
        
        if df_todos_usuarios.empty:
            st.info("No hay usuarios registrados aparte del administrador maestro.")
        else:
            st.dataframe(df_todos_usuarios, use_container_width=True)
            
            st.markdown("---")
            with st.form("form_editar_usuario"):
                st.subheader("Modificar Permisos o Estado de un Usuario")
                id_usu_mod = st.number_input("ID del Usuario a modificar:", min_value=1, step=1)
                nuevo_permiso_usu = st.selectbox("Cambiar Permiso:", ["Editor ✍️", "Solo Lectura 👁️"])
                nuevo_estado_usu = st.selectbox("Cambiar Estado:", ["Activo (Aprobado) 🟢", "Suspendido 🔴"])
                
                btn_guardar_cambios_usu = st.form_submit_button("Actualizar Usuario")
                if btn_guardar_cambios_usu:
                    escritura_v = 1 if "Editor" in nuevo_permiso_usu else 0
                    aprobado_v = 1 if "Activo" in nuevo_estado_usu else 0
                    
                    conn = obtener_conexion()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE usuarios 
                        SET permiso_escritura = ?, aprobado = ? 
                        WHERE id = ? AND es_admin_general = 0
                    """, (escritura_v, aprobado_v, id_usu_mod))
                    conn.commit()
                    conn.close()
                    st.success("¡Usuario actualizado correctamente!")
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
