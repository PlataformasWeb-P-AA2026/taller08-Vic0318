import os
import sys
import subprocess

def print_header(title):
    print("=" * 60)
    print(f" {title.upper()} ".center(60, "="))
    print("=" * 60)

def check_dependencies():
    print("Comprobando dependencias...")
    try:
        import sqlalchemy
        import streamlit
        import dotenv
        import mysql.connector
        print("Todas las dependencias estan instaladas.")
        return True
    except ImportError as e:
        print(f"Falta una dependencia: {e}")
        print("Instalando dependencias usando: pip install -r requirements.txt ...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Dependencias instaladas con exito.")
            return True
        except Exception as ex:
            print(f"Error al instalar dependencias: {ex}")
            return False

def run_sqlite():
    print_header("1. Ejecutando migracion para SQLite")
    from migrate import run_migration
    success = run_migration('sqlite')
    if success:
        print("\nBase de datos SQLite 'paises.db' creada y poblada con exito.")
        print(f"  Ruta: {os.path.abspath('paises.db')}")
    else:
        print("\nFallo la migracion de SQLite.")
    return success

def run_mysql():
    print_header("2. Configuracion y Migracion para MySQL")
    print("Para probar con MySQL/MariaDB:")
    print("1. Asegurate de que el servicio MySQL este corriendo.")
    print("2. Abre o crea un archivo '.env' en la raiz y configura tus credenciales:")
    print("   DB_USER=root")
    print("   DB_PASSWORD=tu_contrasena")
    print("   DB_HOST=localhost")
    print("   DB_PORT=3306")
    print("   DB_NAME=paises")
    print("\n¿Deseas intentar ejecutar la migracion de MySQL ahora? (s/n): ", end="")
    
    choice = input().strip().lower()
    if choice == 's':
        from migrate import run_migration
        success = run_migration('mysql')
        if success:
            print("\nBase de datos MySQL 'paises' creada y poblada con exito.")
            return True
        else:
            print("\nFallo la migracion de MySQL.")
            print("  Puedes configurarla despues en la barra lateral de la app web.")
    else:
        print("\nMigracion de MySQL omitida.")
    return False

def start_streamlit():
    print_header("3. Iniciando Frontend en Streamlit")
    print("Se iniciara la interfaz web. Si tu navegador no se abre automaticamente,")
    print("puedes ingresar a: http://localhost:8501")
    print("Presiona Ctrl+C en esta consola para detener el servidor.\n")
    try:
        # Ejecutar streamlit usando el modulo de python
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\nServidor de Streamlit detenido.")
    except Exception as e:
        print(f"Error al iniciar Streamlit: {e}")

def main():
    print_header("Taller 08 - Integracion de datos y ORM")
    if not check_dependencies():
        return
    
    # 1. SQLite
    sqlite_ok = run_sqlite()
    
    # 2. MySQL (opcional en CLI, configurable en Web)
    run_mysql()
    
    # 3. Streamlit
    if sqlite_ok:
        start_streamlit()
    else:
        print("\nNo se puede iniciar Streamlit debido a errores en la base de datos de origen.")

if __name__ == "__main__":
    main()
