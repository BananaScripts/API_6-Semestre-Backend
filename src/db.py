import psycopg2
import os
from dotenv import load_dotenv

# Garante que o .env dentro da mesma pasta do db.py seja carregado
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD").strip()
}

def get_connection():
    try:
        print("Tentando conectar ao banco com as seguintes configs:")
        print(DB_CONFIG)
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        print("Conexão feita com sucesso!")
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise
