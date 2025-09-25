CREATE SCHEMA IF NOT EXISTS domrock AUTHORIZATION postgres;
SET search_path TO domrock;

CREATE TABLE IF NOT EXISTS clientes (
    id_cliente SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS produtos (
    id_produto SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    grupo_mercadoria VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS vendas (
    id_venda SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    cliente_id INT NOT NULL,
    produto_id INT NOT NULL,
    lote VARCHAR(50),
    peso_liquido DECIMAL(12,2),
    quantidade INT,
    FOREIGN KEY (cliente_id) REFERENCES clientes (id_cliente),
    FOREIGN KEY (produto_id) REFERENCES produtos (id_produto)
);

CREATE TABLE IF NOT EXISTS estoque (
    id_estoque SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    cliente_id INT NOT NULL,
    produto_id INT NOT NULL,
    centro VARCHAR(50),
    dias_em_estoque INT,
    quantidade_total INT,
    FOREIGN KEY (cliente_id) REFERENCES clientes (id_cliente),
    FOREIGN KEY (produto_id) REFERENCES produtos (id_produto)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL
);