import csv
import os
import sys
from models import Base, Continente, Pais, Jugador
from db_config import get_session, get_engine

CONTINENTES_PAISES = {
    'Europa': ['Alemania', 'España', 'Francia', 'Inglaterra', 'Portugal'],
    'América': ['Argentina', 'Brasil', 'Ecuador', 'Estados Unidos', 'México'],
    'Asia': ['Japón'],
    'África': ['Marruecos', 'Nigeria', 'Senegal'],
    'Oceanía': ['Australia']
}

# Crear mapeo inverso de País -> Continente
PAIS_A_CONTINENTE = {}
for cont, paises in CONTINENTES_PAISES.items():
    for p in paises:
        PAIS_A_CONTINENTE[p] = cont

def run_migration(db_type='sqlite', custom_creds=None):
    print(f"=========================================")
    print(f"Iniciando migración para: {db_type.upper()}")
    print(f"=========================================")
    
    # 1. Obtener sesión y engine
    try:
        session = get_session(db_type, custom_creds)
        engine = get_engine(db_type, custom_creds)
    except Exception as e:
        print(f"Error al conectar con la base de datos {db_type}: {e}")
        return False

    # 2. Crear las tablas en la base de datos si no existen
    print("Creando tablas si no existen...")
    Base.metadata.create_all(engine)

    try:
        # 3. Insertar Continentes si no existen
        print("Registrando continentes...")
        continentes_db = {}
        for cont_name in CONTINENTES_PAISES.keys():
            cont_obj = session.query(Continente).filter_by(nombre=cont_name).first()
            if not cont_obj:
                cont_obj = Continente(nombre=cont_name)
                session.add(cont_obj)
                session.flush() # Para obtener el ID
            continentes_db[cont_name] = cont_obj

        # 4. Insertar Países si no existen
        print("Registrando países...")
        paises_db = {}
        for cont_name, paises_list in CONTINENTES_PAISES.items():
            cont_obj = continentes_db[cont_name]
            for pais_name in paises_list:
                pais_obj = session.query(Pais).filter_by(nombre=pais_name).first()
                if not pais_obj:
                    pais_obj = Pais(nombre=pais_name, continente_id=cont_obj.id)
                    session.add(pais_obj)
                    session.flush()
                paises_db[pais_name] = pais_obj

        # Confirmar inserciones iniciales de maestros
        session.commit()

        # 5. Leer CSV y registrar Jugadores
        csv_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'jugadores_futbol.csv')
        if not os.path.exists(csv_path):
            print(f"Error: No se encontró el archivo CSV en: {csv_path}")
            return False

        print(f"Leyendo jugadores desde {csv_path}...")
        
        # Limpiar los jugadores existentes para evitar duplicados en reinicios de migración
        deleted_count = session.query(Jugador).delete()
        if deleted_count > 0:
            print(f"Se limpiaron {deleted_count} jugadores previos de la tabla.")

        jugadores_a_insertar = []
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for line_idx, row in enumerate(reader, start=1):
                nombre = row['nombre_jugador'].strip()
                p_nac = row['pais_nacimiento'].strip()
                p_jue = row['pais_donde_juega'].strip()
                posicion = row['posicion'].strip()
                edad = int(row['edad'].strip())
                partidos = int(row['numero_partidos_seleccion'].strip())
                goles = int(row['goles_seleccion'].strip())

                # Validar existencia de países en BD
                if p_nac not in paises_db:
                    print(f"Advertencia (línea {line_idx}): País de nacimiento '{p_nac}' no está en la base de datos. Se omitirá.")
                    continue
                if p_jue not in paises_db:
                    print(f"Advertencia (línea {line_idx}): País donde juega '{p_jue}' no está en la base de datos. Se omitirá.")
                    continue

                nac_id = paises_db[p_nac].id
                jue_id = paises_db[p_jue].id

                jugador = Jugador(
                    nombre=nombre,
                    pais_nacimiento_id=nac_id,
                    pais_donde_juega_id=jue_id,
                    posicion=posicion,
                    edad=edad,
                    numero_partidos_seleccion=partidos,
                    goles_seleccion=goles
                )
                jugadores_a_insertar.append(jugador)

        print(f"Guardando {len(jugadores_a_insertar)} jugadores en la base de datos...")
        session.add_all(jugadores_a_insertar)
        session.commit()
        print("Migración completada exitosamente!")
        return True

    except Exception as e:
        session.rollback()
        print(f"Error durante la migración: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    db_type = 'sqlite'
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ['sqlite', 'mysql']:
            db_type = sys.argv[1].lower()
    run_migration(db_type)
