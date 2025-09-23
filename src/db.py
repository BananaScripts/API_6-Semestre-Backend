import psycopg2

DB_CONFIG = {
    "host": "localhost", #coloque o host do seu banco
    "port": 5432, #coloque a porta do seu banco (o padrão do PostgreSQL é 5432)
    "dbname": "domrock", #coloque o nome do seu banco
    "user": "postgres", #coloque o usuário do seu banco
    "password": "root" #coloque a senha do seu usuário configurado no banco de dados
}

def get_connection():
    try:
        print("Conexão feita")
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise