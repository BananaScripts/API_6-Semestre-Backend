import pandas as pd
from pathlib import Path

def tratar_dados(df, tipo:str):

    #remover duplicados e cópia independente
    df = df.drop_duplicates().copy()

    #garantir datas no formato YYYY-MM-DD
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors='coerce')

    #corrgir valores nulos
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("NA") #strings nulas viram NA
        else:
            df[col] = df[col].fillna(0) #numeros nulos viram 0

    #uniformizar nomes
    if "produto" in df.columns:
        df["produto"] = df["produto"].str.strip().str.title() #tirar espacos em branco e colocar a primeira letra maiuscula
    
    if "cod_cliente" in df.columns:
        df["cod_cliente"] = df["cod_cliente"].astype(str).str.zfill(5) #padrozinar para 5 digitos

    if  tipo == "estoque":
        if "es_totalestoque" in df.columns:
            df["es_totalestoque"] = df["es_totalestoque"].astype(int) #garantir que a quantidade seja inteiro

    elif tipo == "vendas":
        if "giro_sku_cliente" in df.columns:
            df["giro_sku_cliente"] = df["giro_sku_cliente"].astype(int) #garantir que a quantidade seja inteiro
        if "zs_peso_liquido" in df.columns:
            df["zs_peso_liquido"] = df["zs_peso_liquido"].astype(float) #garantir que o peso seja float
    
    return df