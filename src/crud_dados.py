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
        
#####funções para o chatbot

def get_total_produtos_distintos():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute('''SELECT COUNT(DISTINCT "sku") FROM domrock.estoque''')
            result = cursor.fetchone()
            return f"Existem {result[0]} produtos distintos no estoque." if result else "Não foi possível calcular o total de produtos distintos."

def get_total_itens_estoque():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT SUM(es_totalestoque) FROM domrock.estoque")
            result = cursor.fetchone()
            total = f"{result[0]:.2f}" if result and result[0] is not None else "0.00"
            return f"O total de itens em estoque é de {total}."

def get_peso_total_faturado():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT SUM(zs_peso_liquido) FROM domrock.vendas")
            result = cursor.fetchone()
            total = f"{result[0]:.2f}" if result and result[0] is not None else "0.00"
            return f"O peso líquido total faturado é de {total} kg."

def get_top_n_produtos_estoque(n: int = 5):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT produto, SUM(es_totalestoque) as total
                FROM domrock.estoque 
                GROUP BY produto 
                ORDER BY total DESC 
                LIMIT %s
            ''', (n,))
            results = cursor.fetchall()
            if not results:
                return "Não há dados de produtos em estoque."
            
            response = f"Os {n} principais produtos no estoque são:\n"
            for i, (produto, total) in enumerate(results):
                response += f"{i+1}. {produto} (Total: {total:.2f})\n"
            return response

def get_top_n_cidades_faturamento(n: int = 5):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT zs_cidade, SUM(zs_peso_liquido) as total_peso
                FROM domrock.vendas 
                GROUP BY zs_cidade 
                ORDER BY total_peso DESC 
                LIMIT %s
            ''', (n,))
            results = cursor.fetchall()
            if not results:
                return "Não há dados de faturamento por cidade."

            response = f"As {n} cidades que mais recebem faturamento (em peso) são:\n"
            for i, (cidade, total) in enumerate(results):
                response += f"{i+1}. {cidade} (Peso Total: {total:.2f} kg)\n"
            return response
