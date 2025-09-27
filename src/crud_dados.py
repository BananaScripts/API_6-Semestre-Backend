from db import get_connection
from BaseModel.Dados import Venda, Estoque

def get_vendas(skip: int = 0, limit: int = 10):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM domrock.vendas ORDER BY id_venda OFFSET %s LIMIT %s", (skip, limit))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [Venda(**dict(zip(columns, row))) for row in rows]

def get_estoque(skip: int = 0, limit: int = 10):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM domrock.estoque ORDER BY id_estoque OFFSET %s LIMIT %s", (skip, limit))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [Estoque(**dict(zip(columns, row))) for row in rows]
