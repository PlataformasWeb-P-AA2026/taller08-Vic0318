import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, 'paises.db')
SQLITE_URL = f"sqlite:///{SQLITE_PATH}"

def get_mysql_credentials(custom_creds=None):
    """
    Retorna las credenciales de MySQL desde el entorno o desde parámetros personalizados.
    """
    if custom_creds:
        return {
            "user": custom_creds.get("user", "root"),
            "password": custom_creds.get("password", ""),
            "host": custom_creds.get("host", "localhost"),
            "port": custom_creds.get("port", "3306"),
            "database": custom_creds.get("database", "paises")
        }
    return {
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "3306"),
        "database": os.getenv("DB_NAME", "paises")
    }

def create_mysql_database_if_not_exists(custom_creds=None):
    """
    Intenta conectarse al servidor MySQL y crea la base de datos si no existe.
    """
    creds = get_mysql_credentials(custom_creds)
    # Conectarse sin especificar base de datos primero para poder crearla
    temp_url = f"mysql+mysqlconnector://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/"
    engine = create_engine(temp_url)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {creds['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            conn.commit()
            print(f"Base de datos MySQL '{creds['database']}' asegurada.")
    except Exception as e:
        print(f"Advertencia al asegurar la base de datos MySQL: {e}")
        print("Asegúrate de que el servidor de MySQL esté encendido y las credenciales sean correctas.")
        raise e

def get_engine(db_type='sqlite', custom_creds=None):
    """
    Retorna un motor de base de datos de SQLAlchemy.
    db_type puede ser 'sqlite' o 'mysql'.
    """
    if db_type == 'sqlite':
        return create_engine(SQLITE_URL, echo=False)
    elif db_type == 'mysql':
        creds = get_mysql_credentials(custom_creds)
        mysql_url = f"mysql+mysqlconnector://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
        return create_engine(mysql_url, echo=False)
    else:
        raise ValueError(f"Tipo de base de datos no soportado: {db_type}")

def get_session(db_type='sqlite', custom_creds=None):
    """
    Retorna una nueva sesión para el tipo de base de datos especificado.
    """
    if db_type == 'mysql':
        create_mysql_database_if_not_exists(custom_creds)
    
    engine = get_engine(db_type, custom_creds)
    Session = sessionmaker(bind=engine)
    return Session()
