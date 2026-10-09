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
        st.info(f"💰 Alquiler base actual: **${precio_actual:,.2f}**")
        
        st.markdown("### 🌐 Enlaces Oficiales de Consulta (BCRA)")
        st.markdown("""
        Hacé clic para verificar los valores oficiales de los índices según la fecha del contrato:
        - 🔗 [Principales Variables y Series del BCRA](https://www.bcra.gob.ar/principales-variables/)
        - 🔗 [Estadísticas e Indicadores Monetarios (BCRA)](https://www.bcra.gob.ar/)
        """)
        
        st.divider()
        
        coef_ingresado = st.number_input("Ingresá el Coeficiente o Porcentaje obtenido de la web oficial (Ej: 1.35 para un 35% de aumento):", min_value=1.0, value=1.30, step=0.01)
        
        if st.button("Calcular Nuevo Alquiler"):
            nuevo_calculado = precio_actual * coef_ingresado
            st.session_state['nuevo_calculado'] = nuevo_calculado
            st.session_state['coef_usado'] = coef_ingresado

        if 'nuevo_calculado' in st.session_state:
            st.divider()
            st.success("¡Cálculo realizado con éxito!")
            st.write(f"- **Coeficiente Aplicado:** {st.session_state['coef_usado']}")
            st.write(f"- **Monto Anterior:** ${precio_actual:,.2f}")
            st.markdown(f"## 🎯 **Nuevo Alquiler Ajustado: ${st.session_state['nuevo_calculado']:,.2f}**")
    st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "💵 Control de Pagos y Recibos":
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.header("💵 Control de Pagos Mensuales y Emisión de Recibos")
    
    if df_alquileres.empty:
        st.info("No hay propiedades registradas.")
    else:
        p_pago = st.selectbox("Seleccionar Propiedad para Estado de Cuenta:", df_alquileres['nombre_propiedad'].tolist(), key="p_pago_sel")
        prop_reg = df_alquileres[df_alquileres['nombre_propiedad'] == p_pago].iloc[0]
        alq_id_pago = prop_reg['id']
        
        mes_actual_str = datetime.date.today().strftime("%Y-%m")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            mes_input = st.text_input("Mes y Año del Periodo (YYYY-MM):", value=mes_actual_str)
            estado_pago = st.selectbox("Estado del Pago:", ["Pagado 🟢", "Pendiente 🔴", "Atrasado ⚠️"])
        with col_p2:
            monto_pago = st.number_input("Monto Abonado ($):", value=float(prop_reg['precio_alquiler']), min_value=0.0)
            fecha_pago_efectiva = st.date_input("Fecha de Efectivización:", value=hoy)
            
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
            st.success("¡Registro de pago actualizado con éxito!")
            st.rerun()

        st.divider()
        st.subheader("📲 Generador de Recibo Digital para WhatsApp")
        
        inquilino_nombre = prop_reg['inquilino'] if prop_reg['inquilino'] else "[Nombre Inquilino]"
        texto_whatsapp = f"""*RECIBO DE PAGO - ALQUILER* 🏠
-----------------------------------
*Propiedad:* {prop_reg['nombre_propiedad']}
*Dirección:* {prop_reg['direccion']}
*Inquilino:* {inquilino_nombre}
*Periodo Abonado:* {mes_input}
*Monto:* ${monto_pago:,.2f}
*Estado:* {estado_pago}
*Fecha de Pago:* {fecha_pago_efectiva}
-----------------------------------
_Estudio Jurídico Risso - Gestión Inmobiliaria_"""

        st.text_area("Copiá este mensaje y envíaselo por WhatsApp al inquilino:", value=texto_whatsapp, height=180)
    st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "📝 Generador de Contratos":
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.header("📝 Generador Automático de Contratos de Locación (.docx)")
    
    if df_alquileres.empty:
        st.info("No hay propiedades registradas para generar contratos.")
    else:
        prop_c = st.selectbox("Seleccionar Inmueble para el Contrato:", df_alquileres['nombre_propiedad'].tolist(), key="prop_contrato")
        p_c_info = df_alquileres[df_alquileres['nombre_propiedad'] == prop_c].iloc[0]
        
        st.write(f"**Dirección:** {p_c_info['direccion']} | **Inquilino actual:** {p_c_info['inquilino']} | **Valor:** ${p_c_info['precio_alquiler']:,.2f}")
        
        with st.expander("🛠️ Datos Complementarios de las Partes (Opcional para el Contrato)", expanded=True):
            col_cc1, col_cc2 = st.columns(2)
            with col_cc1:
                locador_nombre = st.text_input("Nombre del Locador", value="JUAN JOSE GARCIA")
                locador_dni = st.text_input("DNI Locador", value="4.679.131")
                locador_dom = st.text_input("Domicilio Locador", value="Echeverría 229 de Pergamino")
            with col_cc2:
                fiador_nombre = st.text_input("Nombre del Fiador / Garante", value="MONICA VIVIANA RAIMUNDO")
                fiador_dni = st.text_input("DNI Fiador", value="23.690.839")
                fiador_dom = st.text_input("Domicilio Fiador", value="Av. Colon Nº 525, Planta Alta, Pergamino")

        contrato_modelo_base = f"""CONTRATO DE LOCACIÓN DE INMUEBLE
Entre el Sr. {locador_nombre}, Documento de Identidad N° {locador_dni}, con domicilio en calle {locador_dom}, por una parte y en adelante denominado “el locador”, y por la otra parte el Sr./Sra. {p_c_info['inquilino']} con D.N.I. Nº [Completar DNI] con domicilio en {p_c_info['direccion']}, Pergamino, en adelante denominado “el locatario”, se conviene en celebrar el presente contrato de locación de inmueble sujeto a las siguientes cláusulas y condiciones:

PRIMERA: El locador da en locación al locatario el inmueble de su propiedad ubicado en {p_c_info['direccion']} de la ciudad de Pergamino, destinado a vivienda, el cual se entrega en perfectas condiciones de uso y funcionamiento, tal como se recibe en este acto, obligándose a devolverlo al término del contrato en iguales condiciones.

SEGUNDA: El plazo de la presente locación será de dos (2) años contados desde el {p_c_info['fecha_inicio']}, por lo que su vencimiento se producirá de pleno derecho el día {p_c_info['fecha_fin']}, sin necesidad de notificación o requerimiento alguno por parte del locador.

TERCERA: El valor locativo mensual se conviene en la suma de PESOS (${p_c_info['precio_alquiler']:,.2f}) pagaderos mensualmente y por mes adelantado dentro del 1ro. al 10mo. día de cada mes, en el lugar que el LOCADOR indique mediante notificación fehaciente. El canon se actualizará trimestralmente utilizando el Índice para Contratos de Locación (ICL) publicado por el Banco Central de la República Argentina.

CUARTA: En el caso de mora en el pago mensual, el LOCATARIO abonará al LOCADOR como interés punitorio el 2% acumulativo por cada día de retraso.

QUINTA: El locatario recibe el inmueble desocupado y en perfectas condiciones de habitabilidad, obligándose a restituirlo en el mismo estado.

SEXTA: Al locatario le está expresamente prohibido subarrendar en todo o en parte el inmueble y ceder el presente contrato bajo pena de rescisión.

SÉPTIMA: El locatario deberá abonar además del canon locativo los servicios de electricidad, gas natural, servicios sanitarios y tasas municipales.

OCTAVA: El locador no se responsabiliza por los daños derivados de desperfectos originados en la falta de mantenimiento de la vivienda.

NOVENA: La falta de pago del alquiler por dos (2) meses seguidos o tres (3) alternados dará opción al locador a resolver el contrato y demandar el desalojo.

DECIMA: El locatario podrá rescindir anticipadamente el presente contrato notificando fehacientemente con sesenta (60) días de antelación y abonando la indemnización legal correspondiente.

DECIMO PRIMERA: El Impuesto de Sellos del presente contrato será abonado en su totalidad por parte del locatario.

DECIMO SEGUNDA: El locador tendrá derecho a visitar cada sesenta días y con previo aviso el inmueble locado para verificar su estado de conservación.

DECIMO TERCERA: La Sra. {fiador_nombre}, DNI Nº {fiador_dni}, con domicilio en {fiador_dom} se constituye por el presente en fiador solidario, liso, llano y principal pagador de todas las obligaciones contraídas.

DECIMO CUARTA: Para todos los efectos legales, las partes constituyen domicilios especiales en los lugares indicados y se someten a la competencia de los Tribunales Ordinarios de la ciudad de Pergamino.

En prueba de conformidad, se firman dos ejemplares de un mismo tenor y a un solo efecto en la ciudad de Pergamino."""

        st.subheader("👁️ Vista Previa y Edición Fina del Contrato")
        texto_editado = st.text_area("Contrato Editable:", value=contrato_modelo_base, height=350)

        if st.button("📥 Generar y Descargar Contrato en formato Word (.docx)"):
            doc = Document()
            doc.add_heading(f"Contrato - {p_c_info['nombre_propiedad']}", level=1)
            for parrafo in texto_editado.split("\n\n"):
                if parrafo.strip():
                    doc.add_paragraph(parrafo.strip())
            
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            
            nombre_archivo = f"Contrato_{p_c_info['nombre_propiedad'].replace(' ', '_')}.docx"
            
            st.download_button(
                label="⬇️ Hacer clic aquí para descargar el archivo .docx",
                data=bio,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.success("¡Documento listo para descargar e imprimir!")
    st.markdown("</div>", unsafe_allow_html=True)

elif opcion == "🗑️ Eliminar Propiedad":
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.header("🗑️ Baja de Propiedades y Contratos")
    
    if df_alquileres.empty:
        st.info("No hay propiedades registradas en la base de datos.")
    else:
        prop_a_borrar = st.selectbox("Seleccioná la propiedad que querés dar de baja:", df_alquileres['nombre_propiedad'].tolist())
        p_del_info = df_alquileres[df_alquileres['nombre_propiedad'] == prop_a_borrar].iloc[0]
        prop_id = p_del_info['id']
        
        st.error(f"⚠️ Atención: Estás por eliminar el registro de **{p_del_info['nombre_propiedad']}** (Dirección: {p_del_info['direccion']}). Esta acción también borrará su historial de precios y pagos asociados.")
        
        confirmacion = st.checkbox("Confirmo que deseo dar de baja definitivamente este inmueble.")
        
        if st.button("Eliminar Inmueble de la Base de Datos"):
            if confirmacion:
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM actualizaciones_precio WHERE alquiler_id = ?", (prop_id,))
                cursor.execute("DELETE FROM pagos_mensuales WHERE alquiler_id = ?", (prop_id,))
                cursor.execute("DELETE FROM alquileres WHERE id = ?", (prop_id,))
                conn.commit()
                conn.close()
                st.success("¡Propiedad eliminada correctamente!")
                st.rerun()
            else:
                st.warning("Por favor, marcá la casilla de confirmación para habilitar la eliminación.")
    st.markdown("</div>", unsafe_allow_html=True)
