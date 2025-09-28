CREATE SCHEMA IF NOT EXISTS domrock AUTHORIZATION postgres;
SET search_path TO domrock;

CREATE TABLE IF NOT EXISTS clientes (
    cod_cliente VARCHAR(50) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS produtos (
    cod_produto VARCHAR(50) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS vendas (
    id_venda SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    cod_cliente VARCHAR(50) NOT NULL,
    cod_produto VARCHAR(50) NOT NULL,
    lote VARCHAR(50),
    origem VARCHAR(100),
    zs_gr_mercad VARCHAR(100),
    produto VARCHAR(100),
    zs_centro VARCHAR(50),
    zs_cidade VARCHAR(100),
    zs_uf VARCHAR(2),
    SKU VARCHAR(50),
    zs_peso_liquido DECIMAL(18,8),
    giro_sku_cliente DECIMAL(18,8),
    FOREIGN KEY (cod_cliente) REFERENCES clientes (cod_cliente),
    FOREIGN KEY (cod_produto) REFERENCES produtos (cod_produto)
);

CREATE TABLE IF NOT EXISTS estoque (
    id_estoque SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    cod_cliente VARCHAR(50) NOT NULL,
    cod_produto VARCHAR(50) NOT NULL,
    es_centro VARCHAR(50),
    tipo_material VARCHAR(100),
    origem VARCHAR(100),
    lote VARCHAR(50),
    dias_em_estoque INT,
    produto VARCHAR(100),
    grupo_mercadoria VARCHAR(100),
    es_totalestoque DECIMAL(18,8),
    SKU VARCHAR(50),
    FOREIGN KEY (cod_cliente) REFERENCES clientes (cod_cliente),
    FOREIGN KEY (cod_produto) REFERENCES produtos (cod_produto)
);

CREATE TABLE IF NOT EXISTS usuario(
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(100) NOT NULL
)

