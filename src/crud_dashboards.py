from db import get_connection

# 📌 1. Top produtos mais vendidos
def get_top_produtos(limit: int = 5):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT produto, SUM(zs_peso_liquido) AS total_vendido
                FROM domrock.vendas
                GROUP BY produto
                ORDER BY total_vendido DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                {"produto": r[0], "total_vendido": float(r[1]) if r[1] else 0}
                for r in rows
            ]


# 📌 2. Vendas mensais (para linha do tempo)
def get_vendas_mensais():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DATE_TRUNC('month', data) AS mes,
                       SUM(zs_peso_liquido) AS total_vendido
                FROM domrock.vendas
                GROUP BY mes
                ORDER BY mes
                """
            )
            rows = cursor.fetchall()
            return [
                {"mes": r[0], "total_vendido": float(r[1]) if r[1] else 0}
                for r in rows
            ]


# 📌 3. Estoque por cliente
def get_estoque_por_cliente():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT cod_cliente, SUM(es_totalestoque) AS total_estoque
                FROM domrock.estoque
                GROUP BY cod_cliente
                ORDER BY total_estoque DESC
                """
            )
            rows = cursor.fetchall()
            return [
                {"cliente": r[0], "total_estoque": float(r[1]) if r[1] else 0}
                for r in rows
            ]
