
from db import get_connection
from BaseModel.Dados import Venda, Estoque
from db import get_connection
from Classes.Intencao import Intencao
from Classes.logger import log_info, log_error

# O QUERY_CONFIG permanece o mesmo, servindo como nosso mapa de intenções.
QUERY_CONFIG = {
    Intencao.TOTAL_ITENS_ESTOQUE:      {"table": "estoque", "agg_func": "SUM",   "agg_column": "es_totalestoque"},
    Intencao.TOTAL_PRODUTOS_DISTINTOS:  {"table": "estoque", "agg_func": "COUNT", "agg_column": 'SKU', "default_distinct": True},
    Intencao.PESO_TOTAL_FATURADO:      {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido"},
    Intencao.FATURAMENTO_TOTAL:         {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido"},
    Intencao.TOP_PRODUTOS_ESTOQUE:      {"table": "estoque", "group_by": "produto",   "agg_func": "SUM", "agg_column": "es_totalestoque"},
    Intencao.TOP_CIDADES_FATURAMENTO:   {"table": "vendas",  "group_by": "zs_cidade", "agg_func": "SUM", "agg_column": "zs_peso_liquido"},
    Intencao.TOP_CLIENTES_FATURAMENTO:  {"table": "vendas",  "group_by": "cod_cliente", "agg_func": "SUM", "agg_column": "zs_peso_liquido"},
}

def execute_query_from_components(components: dict) -> str:
    intent = components.get("intent")
    
    # CORREÇÃO: Lidar com intenção desconhecida de forma elegante.
    if not intent or intent == Intencao.DESCONHECIDO:
        return "Desculpe, não entendi a sua pergunta. Poderia tentar reformular? Não tenho informações sobre previsões, apenas sobre dados históricos." 

    if intent not in QUERY_CONFIG:
        log_error(f"Intenção '{intent}' reconhecida, mas não configurada no QUERY_CONFIG.")
        return "Entendi o que você pediu, mas ainda não sei como responder a isso."

    config = QUERY_CONFIG[intent]
    table = config["table"]
    agg_func = config["agg_func"]
    agg_column = config["agg_column"]
    modifiers = components.get("modifiers", {})
    filters = components.get("filters", [])

    where_clauses, params = [], []
    if filters:
        for f in filters:
            where_clauses.append(f'{f["column"]} = %s')
            params.append(f["value"])
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    is_distinct = modifiers.get("distinct", config.get("default_distinct", False))
    agg_sql = f"DISTINCT {agg_column}" if is_distinct else agg_column

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                if "group_by" in config:
                    group_col = config["group_by"]
                    n = components.get("n_top", 5)
                    is_specific_query = any(f['column'] == group_col for f in filters)
                    
                    if is_specific_query:
                        query = f"SELECT SUM({agg_sql}) FROM domrock.{table} {where_sql}"
                    else:
                        query = f'''SELECT {group_col}, {agg_func}({agg_sql}) as total FROM domrock.{table} {where_sql} GROUP BY {group_col} ORDER BY total DESC LIMIT %s'''
                        params.append(n)

                    log_info(f"Executando: {cursor.mogrify(query, tuple(params))}")
                    cursor.execute(query, tuple(params))
                    results = cursor.fetchall()

                    # CORREÇÃO: Resposta mais humana para resultados vazios.
                    if not results or (len(results) == 1 and (results[0][0] is None or results[0][0] == 0)):
                        return "Não encontrei dados para a sua consulta específica."

                    if is_specific_query:
                        return f"O total para {filters[0]['value']} é {results[0][0]:,.2f}."
                    else:
                        title = intent.name.replace("TOP_", "").replace("_", " ").title()
                        response = f"Os {len(results)} principais para {title} são:\n"
                        for item, total in results:
                            response += f"- {item}: {total or 0:,.2f}\n"
                        return response

                else: # Agregação Simples
                    query = f"SELECT {agg_func}({agg_sql}) FROM domrock.{table} {where_sql}"
                    log_info(f"Executando: {cursor.mogrify(query, tuple(params))}")
                    cursor.execute(query, tuple(params))
                    result = cursor.fetchone()
                    total_val = result[0] if result and result[0] is not None else 0
                    
                    # CORREÇÃO: Resposta mais humana para resultados zerados.
                    if total_val == 0:
                        return "Não encontrei dados para a sua consulta específica."
                    
                    return f"O resultado é {total_val:,.2f}."

    except Exception as e:
        log_error(f"Erro ao executar a query: {e}")
        return "Ocorreu um erro ao tentar processar sua solicitação. A equipe de desenvolvimento foi notificada."


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
