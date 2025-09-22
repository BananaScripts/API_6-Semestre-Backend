CREATE SCHEMA IF NOT EXISTS domrock AUTHORIZATION postgres;
SET search_path TO domrock;

CREATE TABLE IF NOT EXISTS clientes (
    cod_cliente VARCHAR(50) PRIMARY KEY,
    nome VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS produtos (
    cod_produto VARCHAR(50) PRIMARY KEY,
    nome VARCHAR(255),
    grupo_mercadoria VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS vendas (
    id_venda SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    cod_cliente VARCHAR(50) NOT NULL,
    cod_produto VARCHAR(50) NOT NULL,
    lote VARCHAR(50),
    zs_peso_liquido DECIMAL(12,2),
    giro_sku_cliente INT,
    FOREIGN KEY (cod_cliente) REFERENCES clientes (cod_cliente),
    FOREIGN KEY (cod_produto) REFERENCES produtos (cod_produto)
);

CREATE TABLE IF NOT EXISTS estoque (
    id_estoque SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    cod_cliente VARCHAR(50) NOT NULL,
    cod_produto VARCHAR(50) NOT NULL,
    es_centro VARCHAR(50),
    dias_em_estoque INT,
    es_totalestoque INT,
    FOREIGN KEY (cod_cliente) REFERENCES clientes (cod_cliente),
    FOREIGN KEY (cod_produto) REFERENCES produtos (cod_produto)
);

