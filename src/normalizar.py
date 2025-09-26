import pandas as pd
from pathlib import Path

def tratar_dados(df, tipo:str):
    # Remover duplicados e cópia independente
    df = df.drop_duplicates().copy()

    # Garantir datas no formato YYYY-MM-DD
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors='coerce')

    # Corrigir valores nulos
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("NA") #string fica "NA"
        else:
            df[col] = df[col].fillna(0) #numérico fica 0

    # Normalizar colunas de texto
    text_cols = [
        "produto", "origem", "zs_gr_mercad", "zs_cidade", "zs_uf", "SKU",
        "tipo_material", "grupo_mercadoria"
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # Padronizar cod_cliente para 5 dígitos
    if "cod_cliente" in df.columns:
        df["cod_cliente"] = df["cod_cliente"].astype(str).str.zfill(5)

    # Padronizar cod_produto para string maiúscula sem espaços
    if "cod_produto" in df.columns:
        df["cod_produto"] = df["cod_produto"].astype(str).str.strip().str.upper()

    # Padronizar centros logísticos
    if "zs_centro" in df.columns:
        df["zs_centro"] = df["zs_centro"].astype(str).str.strip().str.upper()
    if "es_centro" in df.columns:
        df["es_centro"] = df["es_centro"].astype(str).str.strip().str.upper()

    # Tipos numéricos
    if tipo == "estoque":
        if "es_totalestoque" in df.columns:
            df["es_totalestoque"] = pd.to_numeric(df["es_totalestoque"], errors="coerce").fillna(0)
        if "dias_em_estoque" in df.columns:
            df["dias_em_estoque"] = pd.to_numeric(df["dias_em_estoque"], errors="coerce").fillna(0).astype(int)
    elif tipo == "vendas":
        if "giro_sku_cliente" in df.columns:
            df["giro_sku_cliente"] = pd.to_numeric(df["giro_sku_cliente"], errors="coerce").fillna(0)
        if "zs_peso_liquido" in df.columns:
            df["zs_peso_liquido"] = pd.to_numeric(df["zs_peso_liquido"], errors="coerce").fillna(0)

    return df