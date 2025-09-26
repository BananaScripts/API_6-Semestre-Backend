import pandas as pd
from io import BytesIO
from db import get_connection

#transformar em bytes para enviar por email
def df_to_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer.read()


def gerar_relatorios():
    connection = get_connection()

    #relatório de vendas
    query_vendas = """
        SELECT 
            v.cod_cliente AS cliente,
            v.cod_produto AS codigo_produto,
            v.produto AS nome_produto,
            COUNT(*) AS total_vendido,
            SUM(v.zs_peso_liquido) AS peso_total,
            MAX(v.data) AS ultima_compra,
            CURRENT_DATE - MAX(v.data) AS dias_desde_ultima_compra
        FROM domrock.vendas v
        GROUP BY v.cod_cliente, v.cod_produto, v.produto
        ORDER BY total_vendido DESC;
    """
    df_vendas = pd.read_sql_query(query_vendas, connection)

    #relatório de estoque
    query_estoque = """
       SELECT 
            e.cod_cliente AS cliente,
            e.cod_produto AS codigo_produto,
            e.produto AS nome_produto,
            e.es_totalestoque AS quantidade_total,
            e.dias_em_estoque,
            e.es_centro AS centro,
            CASE
                WHEN e.dias_em_estoque > 180 THEN 'Alto'
                WHEN e.dias_em_estoque BETWEEN 90 AND 180 THEN 'Médio'
                ELSE 'Baixo'
            END AS risco_obsolescencia
        FROM domrock.estoque e
        ORDER BY quantidade_total DESC;
    """
    df_estoque = pd.read_sql_query(query_estoque, connection)

    #relatório geral
    query_geral = """
       SELECT 
            v.cod_cliente AS cliente,
            v.cod_produto AS codigo_produto,
            v.produto AS nome_produto,
            COUNT(*) AS total_vendido,
            COALESCE(SUM(e.es_totalestoque), 0) AS estoque_atual,
            CASE 
                WHEN COUNT(*) > 0 THEN ROUND(COALESCE(SUM(e.es_totalestoque),0)::decimal / COUNT(*), 2)
                ELSE NULL
            END AS dias_cobertura,
            CASE
                WHEN COALESCE(SUM(e.es_totalestoque), 0) = 0 THEN 'Sem Estoque'
                WHEN (COALESCE(SUM(e.es_totalestoque), 0)::decimal / COUNT(*)) < 10 THEN 'Crítico'
                WHEN (COALESCE(SUM(e.es_totalestoque), 0)::decimal / COUNT(*)) < 30 THEN 'Atenção'
                ELSE 'OK'
            END AS risco_ruptura
        FROM domrock.vendas v
        LEFT JOIN domrock.estoque e 
            ON v.cod_cliente = e.cod_cliente AND v.cod_produto = e.cod_produto
        GROUP BY v.cod_cliente, v.cod_produto, v.produto
        ORDER BY total_vendido DESC;
    """
    df_geral = pd.read_sql_query(query_geral, connection)

    connection.close()

    return {
        "relatorio_vendas": df_to_bytes(df_vendas),
        "relatorio_estoque": df_to_bytes(df_estoque),
        "relatorio_geral": df_to_bytes(df_geral)
    }
