from db import get_connection
import unidecode
from BaseModel.Dados import Venda, Estoque
from Classes.Intencao import Intencao
from Classes.logger import log_info, log_error

QUERY_CONFIG = {
    Intencao.TOTAL_ITENS_ESTOQUE:      {"table": "estoque", "agg_func": "SUM",   "agg_column": "es_totalestoque", "desc": "itens em estoque", "format": "float"},
    Intencao.TOTAL_PRODUTOS_DISTINTOS: {"table": "estoque", "agg_func": "COUNT", "agg_column": 'SKU', "default_distinct": True, "desc": "produtos distintos", "format": "int"},
    Intencao.FATURAMENTO_TOTAL:        {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "faturamento total", "format": "currency"},
    Intencao.TOP_PRODUTOS_ESTOQUE:     {"table": "estoque", "group_by": "produto",   "agg_func": "SUM", "agg_column": "es_totalestoque", "desc": "produtos com mais estoque"},
    Intencao.TOP_PRODUTOS_VENDIDOS:    {"table": "vendas",  "group_by": "produto",   "agg_func": "SUM", "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "produtos mais vendidos"},
    Intencao.TOP_CIDADES_FATURAMENTO:  {"table": "vendas",  "group_by": "zs_cidade", "agg_func": "SUM", "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "cidades com maior faturamento"},
    Intencao.TOP_CLIENTES_FATURAMENTO: {"table": "vendas",  "group_by": "cod_cliente", "agg_func": "SUM", "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "clientes com maior faturamento"},
    Intencao.FATURAMENTO_POR_CIDADE:   {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido", "desc": "faturamento", "format": "currency"},
    Intencao.FATURAMENTO_POR_PRODUTO:  {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "faturamento"},
    Intencao.FATURAMENTO_POR_CLIENTE:  {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "faturamento"},
    Intencao.FILTRO_DATA:              {"table": "vendas",  "agg_func": "SUM",   "agg_column": "zs_peso_liquido", "date_column": "data_emissao", "desc": "faturamento"},
}

def format_value(value, fmt_type):
    if value is None: return "0"
    if fmt_type == "int": return f"{int(value)}"
    elif fmt_type == "currency": return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{value:,.2f}"

def execute_query_from_components(components: dict) -> list:
    intent = components.get("intent")
    
    if not intent or intent == Intencao.DESCONHECIDO: return ["Desculpe, não entendi."]
    if intent == Intencao.FORA_DE_ESCOPO: return ["Não cubro esses dados."]
    if intent not in QUERY_CONFIG: return ["Entendi, mas não sei calcular."]

    config = QUERY_CONFIG[intent]
    table = config["table"]
    filters = components.get("filters", [])
    n_top = components.get("n_top", 5)

    def build_query(local_filters):
        """Função interna para montar query com filtros dinâmicos"""
        where_clauses, params, descs = [], [], []
        for f in local_filters:
            col, val = f['column'], f['value']
            if str(val).isnumeric():
                where_clauses.append(f'{col} = %s')
            else:
                where_clauses.append(f'{col} ILIKE %s') # ILIKE ajuda, mas não resolve acentos no Postgres padrão
            params.append(val)
            descs.append(f"{f['type']} {val}")
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        agg_expr = f"DISTINCT {config['agg_column']}" if config.get("default_distinct") else config['agg_column']
        
        if "group_by" in config:
            query = f"SELECT {config['group_by']}, {config['agg_func']}({agg_expr}) as total FROM domrock.{table} {where_sql} GROUP BY {config['group_by']} ORDER BY total DESC LIMIT %s"
            params.append(n_top)
        else:
            query = f"SELECT {config['agg_func']}({agg_expr}) FROM domrock.{table} {where_sql}"
            
        return query, params, descs

    # 1. Tentativa Principal
    query, params, descriptions = build_query(filters)

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()

                # 2. Lógica de Retentativa (Se falhar por causa de acentos)
                # Se não achou nada e tem filtros de texto, tenta tirar os acentos do valor de busca
                if (not results or results[0][0] is None) and filters:
                    new_filters = []
                    changed = False
                    for f in filters:
                        val = str(f['value'])
                        if not val.isnumeric():
                            # Remove acentos: São Paulo -> Sao Paulo
                            no_acc_val = unidecode.unidecode(val)
                            if no_acc_val != val:
                                new_filters.append({**f, 'value': no_acc_val})
                                changed = True
                                continue
                        new_filters.append(f)
                    
                    if changed:
                        log_info("Retentando query sem acentos...")
                        query_retry, params_retry, _ = build_query(new_filters)
                        cursor.execute(query_retry, tuple(params_retry))
                        results = cursor.fetchall()

                # Se ainda assim falhar
                if not results or (len(results) == 1 and results[0][0] is None):
                    return [f"Não encontrei dados para {' '.join(descriptions)}. (Verifique a grafia)"]

                fmt_type = config.get("format", "float")
                
                # === RESPOSTA LISTA ===
                if "group_by" in config:
                    qtd = len(results)
                    # Correção Gramatical Plural
                    txt_item = "item" if qtd == 1 else "itens"
                    desc = config.get('desc')
                    
                    if qtd < n_top:
                        header = f"Desculpa, você pediu {n_top}, mas só encontrei {qtd} {desc}:"
                    else:
                        header = f"Aqui estão os top {qtd} {desc}:"
                    
                    lines = [header] + [f"- {item}: {format_value(total, fmt_type)}" for item, total in results]
                    return lines
                
                # === RESPOSTA ÚNICA ===
                else:
                    val = results[0][0] or 0
                    desc = config.get("desc")
                    
                    # Correção: Só adiciona "para [filtros]" se houver filtros
                    if descriptions:
                         msg_final = f"O {desc} para {' '.join(descriptions)} é {format_value(val, fmt_type)}."
                    else:
                         msg_final = f"O {desc} é {format_value(val, fmt_type)}."
                         
                    return [msg_final]

    except Exception as e:
        log_error(f"Erro SQL: {e}")
        return ["Erro técnico no banco de dados."]

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
