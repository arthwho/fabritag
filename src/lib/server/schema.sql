-- Esquema do banco de dados Fabritag (PostgreSQL)

-- Table 1: PREDIO (Unidade física macro)
CREATE TABLE IF NOT EXISTS PREDIO (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    endereco TEXT
);

-- Table 2: CAMARA (Setor específico)
CREATE TABLE IF NOT EXISTS CAMARA (
    id SERIAL PRIMARY KEY,
    predio_id INT REFERENCES PREDIO(id),
    nome VARCHAR(100) NOT NULL,
    capacidade_vagas INT
);

-- Table 3: CLIENTE (Empresa proprietária - Multi-tenancy)
CREATE TABLE IF NOT EXISTS CLIENTE (
    id SERIAL PRIMARY KEY,
    cpf_cnpj VARCHAR(20) UNIQUE,
    nome_razao_social VARCHAR(150)
);

-- Table 4: DISPOSITIVO (Microcontrolador / ESP32)
CREATE TABLE IF NOT EXISTS DISPOSITIVO (
    id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES CLIENTE(id), -- Associação ao cliente
    nome VARCHAR(100),                     -- Ex: 'ESP32 - Linha A'
    ip_address VARCHAR(50),                -- O IP pertence ao microcontrolador
    ativo BOOLEAN DEFAULT TRUE
);

-- Table 5: SENSOR (Antena RFID - vinculada a um dispositivo)
CREATE TABLE IF NOT EXISTS SENSOR (
    id SERIAL PRIMARY KEY,
    camara_id INT REFERENCES CAMARA(id),
    modelo VARCHAR(50) DEFAULT 'PN5180',
    dispositivo_id INT REFERENCES DISPOSITIVO(id),
    ativo BOOLEAN DEFAULT TRUE
);

-- Table 6: PRODUTO_TIPO (Catálogo de itens/SKU)
CREATE TABLE IF NOT EXISTS PRODUTO_TIPO (
    id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES CLIENTE(id),
    nome VARCHAR(100),
    sku VARCHAR(50),
    unidade_medida VARCHAR(20)
);

-- Table 7: LOTE_TAGGEADO (Instância física rastreada)
CREATE TABLE IF NOT EXISTS LOTE_TAGGEADO (
    epc_tag VARCHAR(50) PRIMARY KEY,
    produto_tipo_id INT REFERENCES PRODUTO_TIPO(id),
    quantidade_atual FLOAT,
    status VARCHAR(50)
);

-- Table 8: LEITURA_BRUTA (Telemetria)
CREATE TABLE IF NOT EXISTS LEITURA_BRUTA (
    id BIGSERIAL PRIMARY KEY,
    epc_tag VARCHAR(50), -- Em um cenário real, isso seria uma FK para LOTE_TAGGEADO, mas vamos manter flexível para leituras brutas.
    sensor_id INT REFERENCES SENSOR(id),
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rssi INT
);

-- Table 9: MOVIMENTACAO (Fatos consolidados)
CREATE TABLE IF NOT EXISTS MOVIMENTACAO (
    id BIGSERIAL PRIMARY KEY,
    epc_tag VARCHAR(50),
    camara_id INT REFERENCES CAMARA(id),
    posicao_vaga INT, -- Index of the starting slot (0 to capacity-1)
    data_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_saida TIMESTAMP,
    supervisor_id INT, -- A tabela USUARIO seria referenciada aqui
    desvio_processo BOOLEAN DEFAULT FALSE
);

-- Tabela 10 (novamente, listada como 10 na página 8 do PDF, mas é USUARIO)
CREATE TABLE IF NOT EXISTS USUARIO (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE,
    cliente_id INT REFERENCES CLIENTE(id)
);

-- Dados iniciais para teste
INSERT INTO PREDIO (nome, endereco) VALUES ('Prédio Central', 'Rua das Indústrias, 100') ON CONFLICT DO NOTHING;
INSERT INTO CAMARA (predio_id, nome, capacidade_vagas) VALUES (1, 'Câmara de Testes 1', 10) ON CONFLICT DO NOTHING;
INSERT INTO CLIENTE (cpf_cnpj, nome_razao_social) VALUES ('00000000000', 'Cliente Teste') ON CONFLICT DO NOTHING;
INSERT INTO DISPOSITIVO (cliente_id, nome, ip_address, ativo) VALUES (1, 'ESP32 - Linha A', '192.168.2.175', TRUE) ON CONFLICT DO NOTHING;
INSERT INTO SENSOR (camara_id, modelo, dispositivo_id, ativo) VALUES (1, 'PN5180', 1, TRUE) ON CONFLICT DO NOTHING;
