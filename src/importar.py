import pandas as pd
from db import get_connection
from normalizar import tratar_dados

#função para inserir clientes únicos para evitar erros de chave estrangeira
def inserir_clientes(df: pd.DataFrame):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        clientes = df["cod_cliente"].drop_duplicates()
        for cod in clientes:
            cursor.execute(
                "INSERT INTO domrock.clientes (cod_cliente) VALUES (%s) ON CONFLICT (cod_cliente) DO NOTHING",
                (cod,)
            )
        connection.commit()
    except Exception as e:
        connection.rollback()
        print(f"Erro ao inserir clientes: {e}")
    finally:
        cursor.close()
        connection.close()

#função para inserir produtos únicos para evitar erros de chave estrangeira
def inserir_produtos(df: pd.DataFrame):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        produtos = df["cod_produto"].drop_duplicates()
        for cod in produtos:
            cursor.execute(
                "INSERT INTO domrock.produtos (cod_produto) VALUES (%s) ON CONFLICT (cod_produto) DO NOTHING",
                (cod,)
            )
        connection.commit()
    except Exception as e:
        connection.rollback()
        print(f"Erro ao inserir produtos: {e}")
    finally:
        cursor.close()
        connection.close()

def inserir_dados(df: pd.DataFrame, tabela: str, coluna:list):
    connection = get_connection()
    cursor = connection.cursor() #cursor para executar comandos SQL

    #insere clientes e produtos
    inserir_clientes(df)
    inserir_produtos(df)

    cols = ",".join(coluna)  #junta os nomes das colunas em uma string separada por vírgula
    placeholders = ",".join(["%s"] * len(coluna))  #placeholders para os valores do insert
    query = f"INSERT INTO {tabela} ({cols}) VALUES ({placeholders})"

    try:
        for row in df[coluna].itertuples(index=False, name=None):  #itera sobre as linhas do df apenas nas colunas desejadas
            cursor.execute(query, row)
        connection.commit()  #confirma as alterações no banco
        print(f"{len(df)} registros inseridos em {tabela}.")
    except Exception as e:
        connection.rollback()
        print(f"Erro ao inserir em {tabela}: {e}")
    finally:
        cursor.close()
        connection.close()

def importar_csv(filepath:str, tipo:str):
    #lê o csv
    df = pd.read_csv(filepath, sep="|") 

    #normaliza e trata os dados
    df_tratado  = tratar_dados(df, tipo)

    #inserção dos dados
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
