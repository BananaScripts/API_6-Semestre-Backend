from db import get_connection
from BaseModel.Dados import Venda, Estoque
from Classes.Intencao import Intencao
from Classes.logger import log_info, log_error

QUERY_CONFIG = {
    Intencao.TOTAL_ITENS_ESTOQUE:      {"table": "estoque", "agg_func": "SUM",   "agg_column": "es_totalestoque", "desc": "O total de itens em estoque"},
    Intencao.TOTAL_PRODUTOS_DISTINTOS:  {"table": "estoque", "agg_func": "COUNT", "agg_column": 'SKU', "default_distinct": True, "desc": "O total de produtos distintos"},
    Intencao.FATURAMENTO_TOTAL:         {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "O faturamento total"},
    Intencao.TOP_PRODUTOS_ESTOQUE:      {"table": "estoque", "group_by": "produto",   "agg_func": "SUM", "agg_column": "es_totalestoque", "desc": "produtos com mais estoque"},
    Intencao.TOP_PRODUTOS_VENDIDOS:     {"table": "vendas",  "group_by": "produto",   "agg_func": "SUM", "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "produtos mais vendidos"},
    Intencao.TOP_CIDADES_FATURAMENTO:   {"table": "vendas",  "group_by": "zs_cidade", "agg_func": "SUM", "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "cidades com maior faturamento"},
    Intencao.TOP_CLIENTES_FATURAMENTO:  {"table": "vendas",  "group_by": "cod_cliente", "agg_func": "SUM", "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "clientes com maior faturamento"},
    Intencao.FATURAMENTO_POR_CIDADE:    {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "O faturamento"},
    Intencao.FATURAMENTO_POR_PRODUTO:   {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "O faturamento"},
    Intencao.FATURAMENTO_POR_CLIENTE:   {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "O faturamento"},
    Intencao.FILTRO_DATA:               {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "O faturamento"},
}

def execute_query_from_components(components: dict) -> list:
    intent = components.get("intent")
    if not intent or intent == Intencao.DESCONHECIDO: return ["Desculpe, não entendi a sua pergunta. Poderia tentar reformular?"]
    if intent == Intencao.FORA_DE_ESCOPO: return ["Não tenho informações sobre pedidos não faturados, cancelados ou devolvidos."]
    if intent not in QUERY_CONFIG: log_error(f"Intenção '{intent}' não configurada."); return ["Entendi o que você pediu, mas ainda não sei como responder a isso."]

    config = QUERY_CONFIG[intent]
    table, agg_func, agg_column = config["table"], config["agg_func"], config["agg_column"]
    date_column = config.get("date_column")
    modifiers, filters, n = components.get("modifiers", {}), components.get("filters", []), components.get("n_top", 5)

    where_clauses, params, filter_descriptions = [], [], []

    for f in filters:
        if f.get('type') == 'date_range' and date_column:
            where_clauses.append(f'{date_column} BETWEEN %s AND %s')
            params.extend([f['value']['start_date'], f['value']['end_date']])
            filter_descriptions.append(f"no período de {f['value']['start_date']} a {f['value']['end_date']}")
        elif f.get('column'):
            operator = "=" if f["value"].isnumeric() else "ILIKE"
            where_clauses.append(f'{f["column"]} {operator} %s')
            params.append(f["value"])
            filter_descriptions.append(f"para {f['column'].replace('_',' ')} {f['value']}")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    is_distinct = modifiers.get("distinct", config.get("default_distinct", False))
    agg_sql = f"DISTINCT {agg_column}" if is_distinct else agg_column

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                if "group_by" in config:
                    group_col = config["group_by"]
                    query = f'SELECT {group_col}, {agg_func}({agg_sql}) as total FROM domrock.{table} {where_sql} GROUP BY {group_col} ORDER BY total DESC LIMIT %s'
                    params.append(n)
                else:
                    query = f"SELECT {agg_func}({agg_sql}) FROM domrock.{table} {where_sql}"

                log_info(f"Executando: {cursor.mogrify(query, tuple(params))}")
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()

                if not results or (len(results) == 1 and results[0][0] is None):
                    return ["Não encontrei dados para a sua consulta específica."]

                if "group_by" in config:
                    num_results = len(results)
                    title = config.get("desc", "resultados")
                    if num_results < n:
                        header = f"Você pediu os {n} principais, mas encontrei apenas {num_results}. São eles:"
                    else:
                        header = f"Os {n} principais {title} são:"
                    
                    response = [header] + [f"- {item}: {total or 0:,.2f}" for item, total in results]
                    return response
                else:
                    total_val = results[0][0]
                    base_desc = config.get("desc", "O resultado")
                    filter_desc = " " + " e ".join(filter_descriptions) if filter_descriptions else ""
                    return [f"{base_desc}{filter_desc} é {total_val:,.2f}."]

    except Exception as e: log_error(f"Erro ao executar a query: {e}"); return ["Ocorreu um erro ao tentar processar sua solicitação."]





def get_vendas(skip: int = 0, limit: int = 10):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM domrock.vendas ORDER BY id_venda OFFSET %s LIMIT %s", (skip, limit))
            rows, columns = cursor.fetchall(), [desc[0] for desc in cursor.description]
            return [Venda(**dict(zip(columns, row))) for row in rows]

def get_estoque(skip: int = 0, limit: int = 10):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM domrock.estoque ORDER BY id_estoque OFFSET %s LIMIT %s", (skip, limit))
            rows, columns = cursor.fetchall(), [desc[0] for desc in cursor.description]
            return [Estoque(**dict(zip(columns, row))) for row in rows]
