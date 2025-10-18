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

def gerar_metricas_domrock():
    import locale
    import pandas as pd
    
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

    connection = get_connection()

    metricas = {
        "estoque_consumido_toneladas": """
            SELECT ROUND(SUM(e.es_totalestoque) / 1000, 2) AS valor
            FROM domrock.estoque e
            WHERE e.data >= CURRENT_DATE - INTERVAL '52 weeks';
        """,
        "frequencia_compra_meses": """
            SELECT COUNT(DISTINCT TO_CHAR(v.data, 'YYYY-MM')) AS valor
            FROM domrock.vendas v
            WHERE v.zs_peso_liquido > 0
              AND v.data >= CURRENT_DATE - INTERVAL '52 weeks';
        """,
        "aging_medio_semanas": """
            SELECT ROUND(AVG(e.dias_em_estoque) / 7, 2) AS valor
            FROM domrock.estoque e
            WHERE e.data >= CURRENT_DATE - INTERVAL '52 weeks';
        """,
        "clientes_consumiram_SKU_1": """
            SELECT COUNT(DISTINCT v.cod_cliente) AS valor
            FROM domrock.vendas v
            WHERE v.SKU = 'SKU_1'
              AND v.zs_peso_liquido > 0;
        """,
        "skus_alto_giro_sem_estoque": """
            SELECT v.SKU, ROUND(COALESCE(SUM(e.es_totalestoque),0), 2) AS estoque_total,
                   AVG(v.giro_sku_cliente) AS giro_medio
            FROM domrock.vendas v
            LEFT JOIN domrock.estoque e ON v.SKU = e.SKU
            WHERE v.data >= CURRENT_DATE - INTERVAL '52 weeks'
              AND v.giro_sku_cliente > 20
            GROUP BY v.SKU
            HAVING COALESCE(SUM(e.es_totalestoque), 0) <= 0.01
            ORDER BY giro_medio DESC
            LIMIT 10;
        """,
        "itens_para_repor": """
            SELECT e.SKU, ROUND(SUM(e.es_totalestoque), 2) AS estoque_total
            FROM domrock.estoque e
            JOIN domrock.vendas v ON e.SKU = v.SKU
            WHERE e.data >= CURRENT_DATE - INTERVAL '52 weeks'
              AND v.data >= CURRENT_DATE - INTERVAL '52 weeks'
            GROUP BY e.SKU
            HAVING SUM(e.es_totalestoque) <= 0.5
            ORDER BY estoque_total ASC
            LIMIT 10;
        """,
        "risco_desabastecimento_SKU_1": """
            WITH consumo_medio_semanal AS (
                SELECT ROUND(SUM(v.zs_peso_liquido) / 52, 4) AS consumo
                FROM domrock.vendas v
                WHERE v.SKU = 'SKU_1'
                  AND v.data >= CURRENT_DATE - INTERVAL '52 weeks'
            ), estoque_atual AS (
                SELECT ROUND(SUM(e.es_totalestoque), 4) AS estoque
                FROM domrock.estoque e
                WHERE e.SKU = 'SKU_1'
                  AND e.data = (SELECT MAX(data) FROM domrock.estoque WHERE SKU = 'SKU_1')
            )
            SELECT e.estoque, c.consumo,
                   CASE 
                     WHEN e.estoque < c.consumo THEN 'Alto'
                     WHEN e.estoque < 2*c.consumo THEN 'Médio'
                     ELSE 'Baixo'
                   END AS risco
            FROM estoque_atual e, consumo_medio_semanal c;
        """
    }

    descricoes = {
        "estoque_consumido_toneladas": "Quantidade de estoque consumido nas últimas 52 semanas: {valor:.2f} toneladas.",
        "frequencia_compra_meses": "A empresa realizou compras em {valor:.0f} dos últimos 12 meses.",
        "aging_medio_semanas": "O tempo médio que o estoque permanece armazenado é de {valor:.2f} semanas.",
        "clientes_consumiram_SKU_1": "{valor:.0f} clientes compraram o material SKU_1 nas últimas 52 semanas.",
        "skus_alto_giro_sem_estoque": "SKUs de alto giro e alta frequência que estão sem estoque: {descricao}.",
        "itens_para_repor": "Itens que precisam ser repostos no estoque (estoque baixo e vendas recentes): {descricao}.",
        "risco_desabastecimento_SKU_1": "O risco de desabastecimento do SKU_1 é {descricao} (estoque atual: {estoque:.2f} toneladas, consumo médio semanal: {consumo:.2f} toneladas)."
    }

    resultados = {}

    try:
        for nome, sql in metricas.items():
            df = pd.read_sql_query(sql, connection)

            print(f"[DEBUG] Consulta '{nome}' retornou {len(df)} linhas e colunas: {list(df.columns)}")

            if nome in ["skus_alto_giro_sem_estoque", "itens_para_repor"]:
                if df.empty:
                    texto = descricoes[nome].format(descricao="Nenhum SKU encontrado.")
                else:
                    if "SKU" in df.columns:
                        skus_list = df["SKU"].astype(str).tolist()
                    elif "sku" in df.columns:
                        skus_list = df["sku"].astype(str).tolist()
                    else:
                        skus_list = []
                    texto = descricoes[nome].format(descricao=", ".join(skus_list))
                resultados[nome] = {
                    "valor": len(df),
                    "descricao": texto
                }

            elif nome == "risco_desabastecimento_SKU_1":
                if df.empty:
                    texto = "Não foi possível calcular o risco de desabastecimento para SKU_1."
                    valor = None
                else:
                    linha = df.iloc[0]
                    estoque = float(linha["estoque"]) if linha["estoque"] is not None else 0.0
                    consumo = float(linha["consumo"]) if linha["consumo"] is not None else 0.0
                    risco = linha["risco"] if linha["risco"] is not None else "Desconhecido"
                    texto = descricoes[nome].format(
                        descricao=risco,
                        estoque=estoque,
                        consumo=consumo
                    )
                    valor = None
                resultados[nome] = {
                    "valor": valor,
                    "descricao": texto
                }

            else:
                valor = float(df.iloc[0]["valor"]) if not df.empty and df.iloc[0]["valor"] is not None else 0.0
                texto = descricoes[nome].format(valor=valor)
                resultados[nome] = {
                    "valor": valor,
                    "descricao": texto
                }

    except Exception as e:
        print(f"Erro ao calcular métricas: {e}")
        resultados["erro"] = str(e)

    finally:
        connection.close()

    return resultados
