import streamlit as st
import pandas as pd
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from db_config import get_session, get_engine
from models import Jugador, Pais, Continente

# Configuración de página de Streamlit
st.set_page_config(
    page_title="FutbolStats - ORM y Integración de Datos",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar de Streamlit
st.sidebar.header("Configuración")
db_selection = st.sidebar.selectbox(
    "Seleccionar Fuente de Base de Datos:",
    ["SQLite", "MySQL / MariaDB"],
    index=0
)

db_type = 'sqlite' if db_selection == "SQLite" else 'mysql'

# Cargar configuración personalizada para MySQL
custom_creds = None
if db_type == 'mysql':
    import os
    st.sidebar.markdown("---")
    st.sidebar.subheader("Credenciales MySQL")
    default_user = os.getenv("DB_USER", "root")
    default_host = os.getenv("DB_HOST", "localhost")
    default_port = os.getenv("DB_PORT", "3306")
    default_db = os.getenv("DB_NAME", "paises")
    
    user = st.text_input("Usuario:", value=default_user)
    password = st.text_input("Contraseña:", value="", type="password")
    host = st.text_input("Host:", value=default_host)
    port = st.text_input("Puerto:", value=default_port)
    database = st.text_input("Base de datos:", value=default_db)
    
    custom_creds = {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "database": database
    }

# Intentar conectar con la Base de Datos seleccionada
connected = False
error_msg = ""
session = None

try:
    session = get_session(db_type, custom_creds)
    # Ejecutar una consulta simple para comprobar conexión
    session.execute(func.now() if db_type == 'mysql' else func.random())
    connected = True
except Exception as e:
    connected = False
    error_msg = str(e)
finally:
    if session:
        session.close()

# Mostrar Estado de Conexión en Sidebar
if connected:
    st.sidebar.success(f"Conectado a {db_selection}")
else:
    st.sidebar.error(f"Error de conexión a {db_selection}")
    st.sidebar.text(f"Detalles: {error_msg[:100]}...")
    if db_type == 'mysql':
        st.sidebar.info("Verifica las credenciales y que el servicio MySQL esté activo.")

# Botón para ejecutar migración
st.sidebar.markdown("---")
st.sidebar.markdown("**Administración de Base de Datos**")
if st.sidebar.button("Inicializar y Migrar Datos", help="Ejecuta la migración de datos para poblar las tablas usando ORM"):
    with st.spinner("Ejecutando migración..."):
        from migrate import run_migration
        success = run_migration(db_type, custom_creds)
        if success:
            st.sidebar.success("Migración exitosa")
            st.rerun()
        else:
            st.sidebar.error("Falló la migración. Revisa los logs.")

# Encabezado Principal
st.title("FutbolStats Dashboard")
st.markdown("Visualización de jugadores y estadísticas de selecciones usando ORM")
st.write("---")

if not connected:
    st.warning("Selecciona una base de datos activa para cargar la información.")
else:
    # Carga de datos utilizando el ORM
    session = get_session(db_type, custom_creds)
    
    try:
        # 1. Obtener jugadores con sus países y continentes correspondientes
        query_jugadores = session.query(Jugador).options(
            joinedload(Jugador.pais_nacimiento).joinedload(Pais.continente),
            joinedload(Jugador.pais_donde_juega)
        )
        jugadores = query_jugadores.all()
        
        # Formatear a DataFrame la primera tabla
        data_players = []
        for p in jugadores:
            data_players.append({
                "nombre_jugador": p.nombre,
                "pais_nacimiento": p.pais_nacimiento.nombre,
                "pais_donde_juega": p.pais_donde_juega.nombre,
                "posicion": p.posicion,
                "edad": p.edad,
                "numero_partidos_seleccion": p.numero_partidos_seleccion,
                "goles_seleccion": p.goles_seleccion,
                "continente": p.pais_nacimiento.continente.nombre
            })
        df_players = pd.DataFrame(data_players)
        
        # 2. Tabla de Continentes agregada vía ORM
        res_cont = session.query(
            Continente.nombre.label('continente'),
            func.count(Jugador.id).label('número de jugadores de la base'),
            func.sum(Jugador.goles_seleccion).label('número goles en función de los goles de cada jugador')
        ).join(Pais, Pais.continente_id == Continente.id)\
         .join(Jugador, Jugador.pais_nacimiento_id == Pais.id)\
         .group_by(Continente.nombre).all()
        
        df_continents = pd.DataFrame([
            {
                "continente": r.continente,
                "número de jugadores de la base": r[1],
                "número goles en función de los goles de cada jugador": r[2]
            } for r in res_cont
        ])
        
        # 3. Tabla de Países agregada vía ORM
        res_pais = session.query(
            Pais.nombre.label('pais'),
            func.count(Jugador.id).label('número de jugadores de la base'),
            func.sum(Jugador.goles_seleccion).label('número de goles en función de los goles de cada jugador')
        ).join(Jugador, Jugador.pais_nacimiento_id == Pais.id)\
         .group_by(Pais.nombre).all()
         
        df_countries = pd.DataFrame([
            {
                "pais": r.pais,
                "número de jugadores de la base": r[1],
                "número de goles en función de los goles de cada jugador": r[2]
            } for r in res_pais
        ])
        
        # --- MÉTRICAS KPI NATIVAS ---
        total_players = len(df_players)
        total_goals = int(df_players["goles_seleccion"].sum()) if total_players > 0 else 0
        avg_age = float(df_players["edad"].mean()) if total_players > 0 else 0
        
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1:
            st.metric("Total Jugadores", total_players)
        with col_kpi2:
            st.metric("Total Goles en Selección", total_goals)
        with col_kpi3:
            st.metric("Edad Promedio", f"{avg_age:.1f} años")

        st.write("---")

        # --- SECCIÓN DE TABS ---
        tab1, tab2, tab3 = st.tabs([
            "Detalle de Jugadores", 
            "Resumen por Continente", 
            "Resumen por País"
        ])
        
        with tab1:
            st.subheader("Información Detallada de Jugadores")
            
            # Filtros interactivos
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                search_term = st.text_input("Buscar jugador por nombre:", "")
            with col_f2:
                posiciones_disponibles = ["Todos"] + sorted(list(df_players["posicion"].unique()))
                filter_pos = st.selectbox("Filtrar por posición:", posiciones_disponibles)
            
            df_filtered = df_players.copy()
            if search_term:
                df_filtered = df_filtered[df_filtered["nombre_jugador"].str.contains(search_term, case=False)]
            if filter_pos != "Todos":
                df_filtered = df_filtered[df_filtered["posicion"] == filter_pos]
                
            st.dataframe(
                df_filtered,
                use_container_width=True,
                column_config={
                    "nombre_jugador": "Nombre Jugador",
                    "pais_nacimiento": "País Nacimiento",
                    "pais_donde_juega": "País de Juego",
                    "posicion": "Posición",
                    "edad": "Edad",
                    "numero_partidos_seleccion": "Partidos Selección",
                    "goles_seleccion": "Goles Selección",
                    "continente": "Continente"
                }
            )
            st.caption(f"Mostrando {len(df_filtered)} de {len(df_players)} jugadores.")

        with tab2:
            st.subheader("Estadísticas Agregadas por Continente")
            
            st.dataframe(
                df_continents,
                use_container_width=True,
                column_config={
                    "continente": "Continente",
                    "número de jugadores de la base": st.column_config.NumberColumn(
                        "Número Jugadores",
                        help="Cantidad de jugadores nacidos en este continente"
                    ),
                    "número goles en función de los goles de cada jugador": st.column_config.NumberColumn(
                        "Goles Totales",
                        help="Suma de los goles de selección de todos los jugadores de este continente"
                    )
                }
            )
            
            if not df_continents.empty:
                st.markdown("### Gráfico de Goles por Continente")
                st.bar_chart(
                    data=df_continents,
                    x="continente",
                    y="número goles en función de los goles de cada jugador",
                )

        with tab3:
            st.subheader("Estadísticas Agregadas por País")
            
            st.dataframe(
                df_countries,
                use_container_width=True,
                column_config={
                    "pais": "País",
                    "número de jugadores de la base": st.column_config.NumberColumn(
                        "Número Jugadores",
                        help="Cantidad de jugadores nacidos en este país"
                    ),
                    "número de goles en función de los goles de cada jugador": st.column_config.NumberColumn(
                        "Goles Totales",
                        help="Suma de los goles de selección de todos los jugadores de este país"
                    )
                }
            )
            
            if not df_countries.empty:
                st.markdown("### Gráfico de Goles por País")
                st.bar_chart(
                    data=df_countries,
                    x="pais",
                    y="número de goles en función de los goles de cada jugador",
                )
                
    except Exception as e:
        st.error(f"Error al realizar consultas ORM: {e}")
    finally:
        session.close()
