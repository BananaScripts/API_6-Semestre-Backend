import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def get_connection():
    try:
        print("Conexão feita")
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise