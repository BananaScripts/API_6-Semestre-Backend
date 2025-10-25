import pandas as pd
from db import get_connection
from normalizar import tratar_dados
from psycopg2.extras import execute_values


def inserir_clientes(df: pd.DataFrame):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        clientes = df["cod_cliente"].drop_duplicates().dropna().tolist()
        if not clientes:
            return
        query = """
            INSERT INTO domrock.clientes (cod_cliente)
            VALUES %s
            ON CONFLICT (cod_cliente) DO NOTHING
        """
        execute_values(cursor, query, [(c,) for c in clientes])
        connection.commit()
        print(f"{len(clientes)} clientes únicos processados.")
    except Exception as e:
        connection.rollback()
        print(f"Erro ao inserir clientes: {e}")
    finally:
        cursor.close()
        connection.close()


def inserir_produtos(df: pd.DataFrame):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        produtos = df["cod_produto"].drop_duplicates().dropna().tolist()
        if not produtos:
            return
        query = """
            INSERT INTO domrock.produtos (cod_produto)
            VALUES %s
            ON CONFLICT (cod_produto) DO NOTHING
        """
        execute_values(cursor, query, [(p,) for p in produtos])
        connection.commit()
        print(f"{len(produtos)} produtos únicos processados.")
    except Exception as e:
        connection.rollback()
        print(f"Erro ao inserir produtos: {e}")
    finally:
        cursor.close()
        connection.close()


def inserir_dados(df: pd.DataFrame, tabela: str, colunas: list):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Inserir clientes e produtos primeiro
        inserir_clientes(df)
        inserir_produtos(df)

        # Monta a query dinâmica
        cols = ",".join(colunas)
        query = f"""
            INSERT INTO {tabela} ({cols})
            VALUES %s
        """

        # Converte o DataFrame em lista de tuplas (melhor performance)
        values = [tuple(x) for x in df[colunas].to_numpy()]

        # Inserção em lote (tamanho configurável para controle de memória)
        execute_values(cursor, query, values, page_size=1000)

        connection.commit()
        print(f"{len(df)} registros inseridos em {tabela}.")
    except Exception as e:
        connection.rollback()
        print(f"Erro ao inserir em {tabela}: {e}")
    finally:
        cursor.close()
        connection.close()


def importar_csv(filepath: str, tipo: str):
    df = pd.read_csv(filepath, sep="|")
    df_tratado = tratar_dados(df, tipo)

    if tipo == "vendas":
        colunas = [
            "data", "cod_cliente", "cod_produto", "lote", "origem", "zs_gr_mercad",
            "produto", "zs_centro", "zs_cidade", "zs_uf", "SKU",
            "zs_peso_liquido", "giro_sku_cliente"
        ]
        inserir_dados(df_tratado, "domrock.vendas", colunas)

    elif tipo == "estoque":
        colunas = [
            "data", "cod_cliente", "cod_produto", "es_centro", "tipo_material",
            "origem", "lote", "dias_em_estoque", "produto", "grupo_mercadoria",
            "es_totalestoque", "SKU"
        ]
        inserir_dados(df_tratado, "domrock.estoque", colunas)

    else:
        raise ValueError("Tipo inválido. Use 'vendas' ou 'estoque'.")
