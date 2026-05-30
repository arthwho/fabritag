-- Esquema do banco de dados Fabritag (PostgreSQL)

-- Table 1: PREDIO (Unidade física macro)
CREATE TABLE IF NOT EXISTS PREDIO (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    endereco TEXT
);

-- Table 1.1: ENDERECO (dados granulares de localizacao)
CREATE TABLE IF NOT EXISTS ENDERECO (
    id SERIAL PRIMARY KEY,
    cep VARCHAR(9),
    logradouro VARCHAR(150),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(100)
);

ALTER TABLE PREDIO ADD COLUMN IF NOT EXISTS endereco_id INT REFERENCES ENDERECO(id);
CREATE INDEX IF NOT EXISTS idx_predio_endereco ON PREDIO(endereco_id);

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
    produto_tipo_id INT REFERENCES PRODUTO_TIPO(id), -- Legado: compatibilidade temporária (primeiro produto associado)
    quantidade_atual FLOAT,
    status VARCHAR(50),
    camara_id INT REFERENCES CAMARA(id),
    posicao_vaga INT,
    data_entrada TIMESTAMP,
    data_saida TIMESTAMP,
    vezes_lidas INT NOT NULL DEFAULT 0
);

ALTER TABLE LOTE_TAGGEADO ADD COLUMN IF NOT EXISTS camara_id INT REFERENCES CAMARA(id);
ALTER TABLE LOTE_TAGGEADO ADD COLUMN IF NOT EXISTS posicao_vaga INT;
ALTER TABLE LOTE_TAGGEADO ADD COLUMN IF NOT EXISTS data_entrada TIMESTAMP;
ALTER TABLE LOTE_TAGGEADO ADD COLUMN IF NOT EXISTS data_saida TIMESTAMP;
ALTER TABLE LOTE_TAGGEADO ADD COLUMN IF NOT EXISTS vezes_lidas INT NOT NULL DEFAULT 0;
UPDATE LOTE_TAGGEADO SET vezes_lidas = 0 WHERE vezes_lidas IS NULL;
ALTER TABLE LOTE_TAGGEADO ALTER COLUMN vezes_lidas SET DEFAULT 0;
ALTER TABLE LOTE_TAGGEADO ALTER COLUMN vezes_lidas SET NOT NULL;
CREATE INDEX IF NOT EXISTS idx_lote_taggeado_camara ON LOTE_TAGGEADO(camara_id);

-- Table 7.1: LOTE_PRODUTO_ASSOC (Associação N:N entre lote e produto)
CREATE TABLE IF NOT EXISTS LOTE_PRODUTO_ASSOC (
    epc_tag VARCHAR(50) REFERENCES LOTE_TAGGEADO(epc_tag) ON DELETE CASCADE,
    produto_tipo_id INT REFERENCES PRODUTO_TIPO(id),
    quantidade FLOAT NOT NULL DEFAULT 1,
    PRIMARY KEY (epc_tag, produto_tipo_id)
);

ALTER TABLE LOTE_PRODUTO_ASSOC ADD COLUMN IF NOT EXISTS quantidade FLOAT;
UPDATE LOTE_PRODUTO_ASSOC SET quantidade = 1 WHERE quantidade IS NULL;
ALTER TABLE LOTE_PRODUTO_ASSOC ALTER COLUMN quantidade SET DEFAULT 1;
ALTER TABLE LOTE_PRODUTO_ASSOC ALTER COLUMN quantidade SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_lote_produto_assoc_produto ON LOTE_PRODUTO_ASSOC(produto_tipo_id);

-- Migração de compatibilidade: replica o vínculo legado para a associação N:N
INSERT INTO LOTE_PRODUTO_ASSOC (epc_tag, produto_tipo_id)
SELECT epc_tag, produto_tipo_id
FROM LOTE_TAGGEADO
WHERE produto_tipo_id IS NOT NULL
ON CONFLICT DO NOTHING;

UPDATE LOTE_PRODUTO_ASSOC lpa
SET quantidade = COALESCE(lt.quantidade_atual, 1)
FROM LOTE_TAGGEADO lt
WHERE lpa.epc_tag = lt.epc_tag
AND lpa.quantidade = 1;

-- Table 8: LEITURA_BRUTA (Telemetria)
CREATE TABLE IF NOT EXISTS LEITURA_BRUTA (
    id BIGSERIAL PRIMARY KEY,
    epc_tag VARCHAR(50), -- Em um cenário real, isso seria uma FK para LOTE_TAGGEADO, mas vamos manter flexível para leituras brutas.
    sensor_id INT REFERENCES SENSOR(id),
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rssi INT,
    movimentacao VARCHAR(20)
);

ALTER TABLE LEITURA_BRUTA ADD COLUMN IF NOT EXISTS movimentacao VARCHAR(20);

-- Table 8.1: MOVIMENTACAO_LOTE (Historico analitico de movimentacoes)
CREATE TABLE IF NOT EXISTS MOVIMENTACAO_LOTE (
    id BIGSERIAL PRIMARY KEY,
    epc_tag VARCHAR(50),
    tipo_movimentacao VARCHAR(20) NOT NULL,
    camara_origem_id INT REFERENCES CAMARA(id) ON DELETE SET NULL,
    camara_destino_id INT REFERENCES CAMARA(id) ON DELETE SET NULL,
    sensor_id INT REFERENCES SENSOR(id) ON DELETE SET NULL,
    leitura_bruta_id BIGINT REFERENCES LEITURA_BRUTA(id) ON DELETE SET NULL,
    posicao_vaga INT,
    quantidade_total_snapshot FLOAT NOT NULL DEFAULT 0,
    ocupacao_origem_snapshot INT,
    capacidade_origem_snapshot INT,
    ocupacao_destino_snapshot INT,
    capacidade_destino_snapshot INT,
    rssi INT,
    origem_evento VARCHAR(30),
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_movimentacao_lote_epc ON MOVIMENTACAO_LOTE(epc_tag);
CREATE INDEX IF NOT EXISTS idx_movimentacao_lote_data ON MOVIMENTACAO_LOTE(data_hora);
CREATE INDEX IF NOT EXISTS idx_movimentacao_lote_destino ON MOVIMENTACAO_LOTE(camara_destino_id, data_hora);
CREATE INDEX IF NOT EXISTS idx_movimentacao_lote_origem ON MOVIMENTACAO_LOTE(camara_origem_id, data_hora);

-- Table 8.2: MOVIMENTACAO_LOTE_PRODUTO (Snapshot dos produtos por movimentacao)
CREATE TABLE IF NOT EXISTS MOVIMENTACAO_LOTE_PRODUTO (
    id BIGSERIAL PRIMARY KEY,
    movimentacao_id BIGINT REFERENCES MOVIMENTACAO_LOTE(id) ON DELETE CASCADE,
    produto_tipo_id INT REFERENCES PRODUTO_TIPO(id) ON DELETE SET NULL,
    produto_nome_snapshot VARCHAR(100),
    sku_snapshot VARCHAR(50),
    unidade_medida_snapshot VARCHAR(20),
    quantidade_snapshot FLOAT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_movimentacao_lote_produto_mov ON MOVIMENTACAO_LOTE_PRODUTO(movimentacao_id);
CREATE INDEX IF NOT EXISTS idx_movimentacao_lote_produto_produto ON MOVIMENTACAO_LOTE_PRODUTO(produto_tipo_id, movimentacao_id);

DROP TABLE IF EXISTS MOVIMENTACAO;

-- Tabela 10 (novamente, listada como 10 na página 8 do PDF, mas é USUARIO)
CREATE TABLE IF NOT EXISTS USUARIO (
    id SERIAL PRIMARY KEY,
    nome_completo VARCHAR(150),
    foto_perfil_url TEXT,
    email VARCHAR(100) UNIQUE,
    cliente_id INT REFERENCES CLIENTE(id),
    senha_hash VARCHAR(255)
);

ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS nome_completo VARCHAR(150);
ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS foto_perfil_url TEXT;
ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS senha_hash VARCHAR(255);

-- Dados iniciais para teste
WITH endereco_inicial AS (
    INSERT INTO ENDERECO (logradouro, numero)
    SELECT 'Rua das Indústrias', '100'
    WHERE NOT EXISTS (
        SELECT 1 FROM PREDIO WHERE nome = 'Prédio Central'
    )
    RETURNING id
)
INSERT INTO PREDIO (nome, endereco, endereco_id)
SELECT 'Prédio Central', 'Rua das Indústrias, 100', id FROM endereco_inicial
ON CONFLICT DO NOTHING;
INSERT INTO CAMARA (predio_id, nome, capacidade_vagas) VALUES (1, 'Câmara de Testes 1', 10) ON CONFLICT DO NOTHING;
INSERT INTO CLIENTE (cpf_cnpj, nome_razao_social) VALUES ('00000000000', 'Cliente Teste') ON CONFLICT DO NOTHING;
INSERT INTO DISPOSITIVO (cliente_id, nome, ip_address, ativo) VALUES (1, 'ESP32 - Linha A', '192.168.2.175', TRUE) ON CONFLICT DO NOTHING;
INSERT INTO SENSOR (camara_id, modelo, dispositivo_id, ativo) VALUES (1, 'PN5180', 1, TRUE) ON CONFLICT DO NOTHING;
