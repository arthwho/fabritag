import os
import math
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

# Database Credentials
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "fabritag")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "1234")

# Initialize connection pool
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 10,
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    print("Database connection pool established.")
except Exception as e:
    print(f"Error creating connection pool: {e}")
    db_pool = None

def get_db_connection():
    """Retorna uma conexão disponível do pool PostgreSQL.

    Use esta função antes de executar consultas no banco. A conexão retornada
    deve ser liberada com release_db_connection(conn) no bloco finally.
    """
    return db_pool.getconn()

def release_db_connection(conn):
    """Devolve uma conexão usada ao pool PostgreSQL.

    Parâmetros:
        conn: conexão obtida com get_db_connection().
    """
    db_pool.putconn(conn)

def _batch_size_from_qty(qty):
    """Converte uma quantidade de lote em número inteiro de vagas ocupadas.

    Parâmetros:
        qty: quantidade numérica recebida do banco ou da API.

    Retorna pelo menos 1 vaga, arredondando quantidades fracionadas para cima.
    """
    try:
        value = float(qty or 1)
    except (TypeError, ValueError):
        value = 1
    return max(1, int(math.ceil(value)))

def _camera_capacity(cur, camara_id):
    """Busca a capacidade de vagas de uma câmara.

    Parâmetros:
        cur: cursor PostgreSQL já aberto.
        camara_id: identificador da câmara.

    Retorna 0 quando a câmara não existe e 100 quando a capacidade está vazia.
    """
    cur.execute("SELECT capacidade_vagas FROM CAMARA WHERE id = %s", (camara_id,))
    res = cur.fetchone()
    if not res:
        return 0
    return res[0] or 100

def _repack_open_movimentacoes(cur, camara_id, strict=True):
    """Reorganiza posições abertas de uma câmara em blocos contíguos.

    Parâmetros:
        cur: cursor PostgreSQL dentro de uma transação ativa.
        camara_id: câmara que terá suas movimentações abertas recalculadas.
        strict: quando True, lança ValueError se a ocupação exceder a capacidade.

    Atualiza posicao_vaga das movimentações abertas e retorna dados de ocupação.
    """
    capacity = _camera_capacity(cur, camara_id)

    cur.execute(
        "SELECT m.id, m.epc_tag, COALESCE(l.quantidade_atual, 1), m.posicao_vaga "
        "FROM MOVIMENTACAO m "
        "LEFT JOIN LOTE_TAGGEADO l ON l.epc_tag = m.epc_tag "
        "WHERE m.camara_id = %s AND m.data_saida IS NULL "
        "ORDER BY m.data_entrada ASC, m.id ASC",
        (camara_id,)
    )
    open_rows = cur.fetchall()

    total_required = sum(_batch_size_from_qty(row[2]) for row in open_rows)
    if strict and total_required > capacity:
        raise ValueError(
            f"Capacidade da câmara excedida: {total_required}/{capacity}. "
            "Reduza a quantidade total dos produtos deste lote para salvar."
        )

    next_pos = 0
    for mov_id, _, qty, current_pos in open_rows:
        size = _batch_size_from_qty(qty)
        if current_pos != next_pos:
            cur.execute(
                "UPDATE MOVIMENTACAO SET posicao_vaga = %s WHERE id = %s",
                (next_pos, mov_id),
            )
        next_pos += size

    return {
        "capacity": capacity,
        "total_required": total_required,
        "over_capacity": total_required > capacity,
    }

def _ensure_lote_produto_assoc_table(cur):
    """Garante a existência e o formato mínimo da tabela LOTE_PRODUTO_ASSOC.

    Parâmetros:
        cur: cursor PostgreSQL usado para executar DDL/DML na transação atual.

    Deve ser chamada antes de ler ou alterar associações de produtos por lote.
    """
    cur.execute(
        "CREATE TABLE IF NOT EXISTS LOTE_PRODUTO_ASSOC ("
        "epc_tag VARCHAR(50) REFERENCES LOTE_TAGGEADO(epc_tag) ON DELETE CASCADE, "
        "produto_tipo_id INT REFERENCES PRODUTO_TIPO(id), "
        "quantidade FLOAT NOT NULL DEFAULT 1, "
        "PRIMARY KEY (epc_tag, produto_tipo_id)"
        ")"
    )
    cur.execute("ALTER TABLE LOTE_PRODUTO_ASSOC ADD COLUMN IF NOT EXISTS quantidade FLOAT")
    cur.execute("UPDATE LOTE_PRODUTO_ASSOC SET quantidade = 1 WHERE quantidade IS NULL")
    cur.execute("ALTER TABLE LOTE_PRODUTO_ASSOC ALTER COLUMN quantidade SET DEFAULT 1")
    cur.execute("ALTER TABLE LOTE_PRODUTO_ASSOC ALTER COLUMN quantidade SET NOT NULL")

def fetch_batch():
    """Lista os lotes taggeados com produtos, quantidades e localização atual.

    Não recebe parâmetros. Usa uma conexão do pool, consulta lotes e
    movimentações, e retorna uma lista de dicionários pronta para a API.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        _ensure_lote_produto_assoc_table(cur)

        cur.execute(
            "SELECT l.epc_tag, l.produto_tipo_id, l.quantidade_atual, l.status, "
            "COALESCE(c_atual.nome, 'Desconhecido'), m_atual.data_entrada, "
            "COALESCE(prod_assoc.produto_ids, CASE WHEN l.produto_tipo_id IS NOT NULL THEN ARRAY[l.produto_tipo_id]::INT[] ELSE ARRAY[]::INT[] END), "
            "COALESCE(prod_assoc.produto_nomes, CASE WHEN pt_legacy.nome IS NOT NULL THEN ARRAY[pt_legacy.nome]::TEXT[] ELSE ARRAY[]::TEXT[] END), "
            "COALESCE(prod_assoc.produto_quantidades, CASE WHEN pt_legacy.nome IS NOT NULL THEN ARRAY[COALESCE(l.quantidade_atual, 1)]::FLOAT[] ELSE ARRAY[]::FLOAT[] END), "
            "COALESCE(prod_assoc.quantidade_total, COALESCE(l.quantidade_atual, 0)) "
            "FROM LOTE_TAGGEADO l "
            "LEFT JOIN PRODUTO_TIPO pt_legacy ON pt_legacy.id = l.produto_tipo_id "
            "LEFT JOIN LATERAL ("
            "  SELECT ARRAY_AGG(lp.produto_tipo_id ORDER BY lp.produto_tipo_id) AS produto_ids, "
            "  ARRAY_AGG(COALESCE(pt.nome, 'Produto sem nome') ORDER BY lp.produto_tipo_id) AS produto_nomes, "
            "  ARRAY_AGG(lp.quantidade ORDER BY lp.produto_tipo_id) AS produto_quantidades, "
            "  SUM(lp.quantidade) AS quantidade_total "
            "  FROM LOTE_PRODUTO_ASSOC lp "
            "  LEFT JOIN PRODUTO_TIPO pt ON pt.id = lp.produto_tipo_id "
            "  WHERE lp.epc_tag = l.epc_tag"
            ") prod_assoc ON TRUE "
            "LEFT JOIN LATERAL ("
            "  SELECT m.camara_id, m.data_entrada "
            "  FROM MOVIMENTACAO m "
            "  WHERE m.epc_tag = l.epc_tag "
            "  ORDER BY (m.data_saida IS NULL) DESC, m.data_entrada DESC "
            "  LIMIT 1"
            ") m_atual ON TRUE "
            "LEFT JOIN CAMARA c_atual ON c_atual.id = m_atual.camara_id "
            "ORDER BY l.epc_tag"
        )
        rows = cur.fetchall()
        if not rows:
            cur.execute(
                "SELECT DISTINCT m.epc_tag, COALESCE(c_atual.nome, 'Desconhecido'), m_atual.data_entrada "
                "FROM MOVIMENTACAO m "
                "LEFT JOIN LATERAL ("
                "  SELECT m2.camara_id, m2.data_entrada "
                "  FROM MOVIMENTACAO m2 "
                "  WHERE m2.epc_tag = m.epc_tag "
                "  ORDER BY (m2.data_saida IS NULL) DESC, m2.data_entrada DESC "
                "  LIMIT 1"
                ") m_atual ON TRUE "
                "LEFT JOIN CAMARA c_atual ON c_atual.id = m_atual.camara_id "
                "ORDER BY m.epc_tag"
            )
            rows = [(row[0], None, None, None, row[1], row[2], [], [], [], 0) for row in cur.fetchall()]
        return [
            {
                "id": row[0],
                "nome": f"{', '.join(row[7]) if row[7] else 'Lote sem produto'} ({row[0]})",
                "epc_tag": row[0],
                "produto_tipo_id": (row[6][0] if row[6] else row[1]),
                "produto_tipo_ids": row[6] or [],
                "quantidade_atual": row[9],
                "status": row[3],
                "produto_nome": ', '.join(row[7]) if row[7] else 'Lote sem produto',
                "produto_nomes": row[7] or [],
                "produto_assoc": [
                    {
                        "produto_tipo_id": produto_id,
                        "produto_nome": produto_nome,
                        "quantidade": quantidade
                    }
                    for produto_id, produto_nome, quantidade in zip(row[6] or [], row[7] or [], row[8] or [])
                ],
                "local_atual": row[4],
                "local_desde": row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else None
            }
            for row in rows
        ]
    finally:
        cur.close()
        release_db_connection(conn)

def fetch_produtos():
    """Busca tipos de produtos em formato simples para seletores.

    Retorna uma lista com id e nome, incluindo o SKU no texto quando existir.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, nome, sku FROM PRODUTO_TIPO ORDER BY nome"
        )
        return [
            {
                "id": row[0],
                "nome": row[1] if not row[2] else f"{row[1]} ({row[2]})"
            }
            for row in cur.fetchall()
        ]
    finally:
        cur.close()
        release_db_connection(conn)

def fetch_camaras():
    """Busca câmaras cadastradas para uso em listas e formulários.

    Retorna uma lista de dicionários com id e nome de cada câmara.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nome FROM CAMARA")
        return [{"id": row[0], "nome": row[1]} for row in cur.fetchall()]
    finally:
        cur.close()
        release_db_connection(conn)

def fetch_clientes():
    """Lista clientes cadastrados com nome e CPF/CNPJ.

    Retorna os registros ordenados por id, usando um nome padrão quando vazio.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, COALESCE(nome_razao_social, 'Cliente sem nome'), cpf_cnpj "
            "FROM CLIENTE ORDER BY id"
        )
        return [
            {
                "id": row[0],
                "nome": row[1],
                "cpf_cnpj": row[2]
            }
            for row in cur.fetchall()
        ]
    finally:
        cur.close()
        release_db_connection(conn)

def create_cliente(cpf_cnpj=None, nome_razao_social=None):
    """Cria um cliente.

    Parâmetros:
        cpf_cnpj: documento já validado ou opcional.
        nome_razao_social: nome exibido para o cliente.

    Retorna o cliente criado com id, documento e nome normalizado.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        normalized_cpf_cnpj = (cpf_cnpj or '').strip() or None
        normalized_nome = (nome_razao_social or '').strip() or None

        cur.execute(
            "INSERT INTO CLIENTE (cpf_cnpj, nome_razao_social) "
            "VALUES (%s, %s) RETURNING id, cpf_cnpj, nome_razao_social",
            (normalized_cpf_cnpj, normalized_nome)
        )
        row = cur.fetchone()
        conn.commit()
        return {
            "id": row[0],
            "cpf_cnpj": row[1],
            "nome_razao_social": row[2],
            "nome": row[2] or 'Cliente sem nome'
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def update_cliente(cliente_id, cpf_cnpj=None, nome_razao_social=None):
    """Atualiza os dados cadastrais de um cliente existente.

    Parâmetros:
        cliente_id: id do cliente a alterar.
        cpf_cnpj: novo documento ou None.
        nome_razao_social: novo nome/razão social ou None.

    Lança ValueError quando o cliente não existe.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        normalized_cpf_cnpj = (cpf_cnpj or '').strip() or None
        normalized_nome = (nome_razao_social or '').strip() or None

        cur.execute(
            "UPDATE CLIENTE SET cpf_cnpj = %s, nome_razao_social = %s "
            "WHERE id = %s RETURNING id, cpf_cnpj, nome_razao_social",
            (normalized_cpf_cnpj, normalized_nome, cliente_id)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Cliente not found")

        conn.commit()
        return {
            "id": row[0],
            "cpf_cnpj": row[1],
            "nome_razao_social": row[2],
            "nome": row[2] or 'Cliente sem nome'
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def delete_cliente(cliente_id):
    """Remove um cliente quando não há vínculos impeditivos.

    Parâmetros:
        cliente_id: id do cliente a excluir.

    Desvincula usuários ligados ao cliente e retorna o id removido.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM PRODUTO_TIPO WHERE cliente_id = %s", (cliente_id,))
        if cur.fetchone()[0] > 0:
            raise ValueError("Cannot delete cliente with existing produtos")

        cur.execute("SELECT COUNT(*) FROM DISPOSITIVO WHERE cliente_id = %s", (cliente_id,))
        if cur.fetchone()[0] > 0:
            raise ValueError("Cannot delete cliente with existing dispositivos")

        # Usuários não impedem a exclusão do cliente: apenas desvinculamos o relacionamento.
        cur.execute("UPDATE USUARIO SET cliente_id = NULL WHERE cliente_id = %s", (cliente_id,))
        usuarios_desvinculados = cur.rowcount

        cur.execute("DELETE FROM CLIENTE WHERE id = %s RETURNING id", (cliente_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Cliente not found")

        conn.commit()
        return {"id": row[0], "usuarios_desvinculados": usuarios_desvinculados}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def create_predio(nome, endereco=None):
    """Cria um prédio para agrupar câmaras.

    Parâmetros:
        nome: nome obrigatório do prédio.
        endereco: endereço opcional.

    Retorna o prédio criado.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO PREDIO (nome, endereco) VALUES (%s, %s) RETURNING id, nome, endereco",
            (nome, endereco)
        )
        row = cur.fetchone()
        conn.commit()
        return {
            "id": row[0],
            "nome": row[1],
            "endereco": row[2]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def create_camara(predio_id, nome, capacidade_vagas=None):
    """Cria uma câmara vinculada a um prédio existente.

    Parâmetros:
        predio_id: id do prédio pai.
        nome: nome da câmara.
        capacidade_vagas: limite opcional de vagas.

    Valida a existência do prédio antes da inserção.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM PREDIO WHERE id = %s", (predio_id,))
        if not cur.fetchone():
            raise ValueError("Predio not found")

        cur.execute(
            "INSERT INTO CAMARA (predio_id, nome, capacidade_vagas) "
            "VALUES (%s, %s, %s) RETURNING id, predio_id, nome, capacidade_vagas",
            (predio_id, nome, capacidade_vagas)
        )
        row = cur.fetchone()
        conn.commit()
        return {
            "id": row[0],
            "predio_id": row[1],
            "nome": row[2],
            "capacidade_vagas": row[3]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def create_sensor(camara_id, modelo='PN5180', ativo=True):
    """Cria um sensor em uma câmara.

    Parâmetros:
        camara_id: id da câmara onde o sensor será instalado.
        modelo: modelo do sensor, com padrão PN5180.
        ativo: indica se o sensor começa ativo.

    Associa automaticamente o primeiro dispositivo ativo, se houver.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM CAMARA WHERE id = %s", (camara_id,))
        if not cur.fetchone():
            raise ValueError("Camara not found")

        # Auto-assign to the first active dispositivo
        cur.execute("SELECT id FROM DISPOSITIVO WHERE ativo = TRUE ORDER BY id LIMIT 1")
        disp_row = cur.fetchone()
        dispositivo_id = disp_row[0] if disp_row else None

        cur.execute(
            "INSERT INTO SENSOR (camara_id, modelo, dispositivo_id, ativo) "
            "VALUES (%s, %s, %s, %s) RETURNING id, camara_id, modelo, dispositivo_id, ativo",
            (camara_id, modelo, dispositivo_id, ativo)
        )
        row = cur.fetchone()
        conn.commit()
        return {
            "id": row[0],
            "camara_id": row[1],
            "modelo": row[2],
            "dispositivo_id": row[3],
            "ativo": row[4]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def update_predio(predio_id, nome, endereco=None):
    """Atualiza nome e endereço de um prédio.

    Parâmetros:
        predio_id: id do prédio.
        nome: novo nome obrigatório.
        endereco: novo endereço opcional.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE PREDIO SET nome = %s, endereco = %s WHERE id = %s RETURNING id, nome, endereco",
            (nome, endereco, predio_id)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Predio not found")

        conn.commit()
        return {
            "id": row[0],
            "nome": row[1],
            "endereco": row[2]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def delete_predio(predio_id):
    """Exclui um prédio sem câmaras associadas.

    Parâmetros:
        predio_id: id do prédio.

    Lança ValueError se houver câmaras dependentes ou se o prédio não existir.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM CAMARA WHERE predio_id = %s", (predio_id,))
        if cur.fetchone()[0] > 0:
            raise ValueError("Cannot delete predio with existing camaras")

        cur.execute("DELETE FROM PREDIO WHERE id = %s RETURNING id", (predio_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Predio not found")

        conn.commit()
        return {"id": row[0]}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def update_camara(camara_id, predio_id, nome, capacidade_vagas=None):
    """Atualiza uma câmara e seu prédio de vínculo.

    Parâmetros:
        camara_id: id da câmara.
        predio_id: id do prédio válido.
        nome: novo nome da câmara.
        capacidade_vagas: nova capacidade opcional.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM CAMARA WHERE id = %s", (camara_id,))
        if not cur.fetchone():
            raise ValueError("Camara not found")

        cur.execute("SELECT 1 FROM PREDIO WHERE id = %s", (predio_id,))
        if not cur.fetchone():
            raise ValueError("Predio not found")

        cur.execute(
            "UPDATE CAMARA SET predio_id = %s, nome = %s, capacidade_vagas = %s "
            "WHERE id = %s RETURNING id, predio_id, nome, capacidade_vagas",
            (predio_id, nome, capacidade_vagas, camara_id)
        )
        row = cur.fetchone()

        conn.commit()
        return {
            "id": row[0],
            "predio_id": row[1],
            "nome": row[2],
            "capacidade_vagas": row[3]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def delete_camara(camara_id):
    """Exclui uma câmara quando não há sensores ou movimentações vinculadas.

    Parâmetros:
        camara_id: id da câmara.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM SENSOR WHERE camara_id = %s", (camara_id,))
        if cur.fetchone()[0] > 0:
            raise ValueError("Cannot delete camara with existing sensores")

        cur.execute("SELECT COUNT(*) FROM MOVIMENTACAO WHERE camara_id = %s", (camara_id,))
        if cur.fetchone()[0] > 0:
            raise ValueError("Cannot delete camara with existing movimentacoes")

        cur.execute("DELETE FROM CAMARA WHERE id = %s RETURNING id", (camara_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Camara not found")

        conn.commit()
        return {"id": row[0]}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def update_sensor(sensor_id, camara_id, modelo='PN5180', ativo=True):
    """Atualiza dados operacionais de um sensor.

    Parâmetros:
        sensor_id: id do sensor.
        camara_id: nova câmara vinculada.
        modelo: modelo do sensor.
        ativo: status ativo/inativo.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM SENSOR WHERE id = %s", (sensor_id,))
        if not cur.fetchone():
            raise ValueError("Sensor not found")

        cur.execute("SELECT 1 FROM CAMARA WHERE id = %s", (camara_id,))
        if not cur.fetchone():
            raise ValueError("Camara not found")

        cur.execute(
            "UPDATE SENSOR SET camara_id = %s, modelo = %s, ativo = %s "
            "WHERE id = %s RETURNING id, camara_id, modelo, dispositivo_id, ativo",
            (camara_id, modelo, ativo, sensor_id)
        )
        row = cur.fetchone()

        conn.commit()
        return {
            "id": row[0],
            "camara_id": row[1],
            "modelo": row[2],
            "dispositivo_id": row[3],
            "ativo": row[4]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def delete_sensor(sensor_id):
    """Remove um sensor sem leituras brutas associadas.

    Parâmetros:
        sensor_id: id do sensor.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM LEITURA_BRUTA WHERE sensor_id = %s", (sensor_id,))
        if cur.fetchone()[0] > 0:
            raise ValueError("Cannot delete sensor with existing leituras")

        cur.execute("DELETE FROM SENSOR WHERE id = %s RETURNING id", (sensor_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Sensor not found")

        conn.commit()
        return {"id": row[0]}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def process_tag_event(epc_tag, sensor_id, event, rssi):
    """Processa uma leitura RFID enviada por um sensor.

    Parâmetros:
        epc_tag: identificador EPC do lote.
        sensor_id: sensor que fez a leitura.
        event: tipo do evento, como ARRIVED ou REMOVED.
        rssi: intensidade do sinal registrada.

    Registra a leitura bruta, cria o lote se necessário e abre/fecha
    movimentações conforme o evento.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Register raw reading
        cur.execute(
            "INSERT INTO LEITURA_BRUTA (epc_tag, sensor_id, rssi) VALUES (%s, %s, %s)",
            (epc_tag, sensor_id, rssi)
        )

        # 2. Find associated camera
        cur.execute("SELECT camara_id FROM SENSOR WHERE id = %s", (sensor_id,))
        camara_res = cur.fetchone()
        if not camara_res:
            return False, "Sensor not found in DB"
        camara_id = camara_res[0]

        # 3. Ensure tag exists
        cur.execute("INSERT INTO LOTE_TAGGEADO (epc_tag, status) VALUES (%s, %s) ON CONFLICT (epc_tag) DO NOTHING", (epc_tag, 'ATIVO'))

        if event == "ARRIVED":
            cur.execute(
                "SELECT id FROM MOVIMENTACAO WHERE epc_tag = %s AND camara_id = %s AND data_saida IS NULL",
                (epc_tag, camara_id)
            )
            if not cur.fetchone():
                # Get batch size
                cur.execute("SELECT quantidade_atual FROM LOTE_TAGGEADO WHERE epc_tag = %s", (epc_tag,))
                qty_res = cur.fetchone()
                batch_size = _batch_size_from_qty(qty_res[0]) if qty_res else 1

                pos_vaga = _find_available_slot(cur, camara_id, batch_size)
                if pos_vaga is None:
                    conn.rollback()
                    return False, "No available slots in camara"

                cur.execute(
                    "INSERT INTO MOVIMENTACAO (epc_tag, camara_id, posicao_vaga, data_entrada) VALUES (%s, %s, %s, NOW())",
                    (epc_tag, camara_id, pos_vaga)
                )
                _repack_open_movimentacoes(cur, camara_id)
        
        elif event == "REMOVED":
            cur.execute(
                "UPDATE MOVIMENTACAO SET data_saida = NOW() "
                "WHERE epc_tag = %s AND camara_id = %s AND data_saida IS NULL",
                (epc_tag, camara_id)
            )

        conn.commit()
        return True, "Processed successfully"
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        release_db_connection(conn)

def fetch_dashboard_data():
    """Monta os indicadores usados pelo dashboard.

    Retorna totais de câmaras, sensores, lotes, movimentações do dia e as
    últimas movimentações formatadas para a interface.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM CAMARA")
        total_camaras = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM SENSOR")
        total_sensores = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT epc_tag) FROM LOTE_TAGGEADO")
        total_lotes = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM MOVIMENTACAO "
            "WHERE data_entrada::date = CURRENT_DATE"
        )
        movimentacoes_hoje = cur.fetchone()[0]
        
        cur.execute(
            "SELECT m.id, m.epc_tag, c.nome, m.data_entrada "
            "FROM MOVIMENTACAO m "
            "JOIN CAMARA c ON m.camara_id = c.id "
            "ORDER BY m.data_entrada DESC LIMIT 10"
        )
        movimentacoes = []
        for row in cur.fetchall():
            movimentacoes.append({
                "id": row[0],
                "produto": row[1],
                "origem": "Câmara de Testes",
                "destino": row[2],
                "data": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None
            })

        return {
            "total_camaras": total_camaras,
            "total_sensores": total_sensores,
            "total_lotes": total_lotes,
            "movimentacoes_hoje": movimentacoes_hoje,
            "ultimas_movimentacoes": movimentacoes
        }
    finally:
        cur.close()
        release_db_connection(conn)

def fetch_infraestrutura_data():
    """Monta dados consolidados da página de infraestrutura.

    Retorna contadores e listas de sensores, prédios e câmaras já agregadas
    com nomes e status para exibição.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM PREDIO")
        total_predios = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM CAMARA")
        total_camaras = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM SENSOR")
        total_sensores = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM SENSOR WHERE ativo = TRUE")
        sensores_ativos = cur.fetchone()[0]
        
        cur.execute(
            "SELECT s.id, s.camara_id, s.modelo, s.dispositivo_id, c.nome, s.ativo, "
            "COALESCE(d.nome, '-') "
            "FROM SENSOR s "
            "JOIN CAMARA c ON s.camara_id = c.id "
            "LEFT JOIN DISPOSITIVO d ON s.dispositivo_id = d.id "
            "ORDER BY s.id DESC"
        )
        sensores = []
        for row in cur.fetchall():
            sensores.append({
                "id": row[0],
                "camara_id": row[1],
                "modelo": row[2],
                "dispositivo_id": row[3],
                "camara": row[4],
                "status": "Ativo" if row[5] else "Inativo",
                "ativo": row[5],
                "dispositivo": row[6]
            })

        cur.execute(
            "SELECT p.id, p.nome, COALESCE(p.endereco, '-'), COUNT(c.id) "
            "FROM PREDIO p "
            "LEFT JOIN CAMARA c ON c.predio_id = p.id "
            "GROUP BY p.id, p.nome, p.endereco "
            "ORDER BY p.id DESC"
        )
        predios = []
        for row in cur.fetchall():
            predios.append({
                "id": row[0],
                "nome": row[1],
                "endereco": row[2],
                "total_camaras": row[3]
            })

        cur.execute(
            "SELECT c.id, c.predio_id, c.nome, p.nome, COALESCE(c.capacidade_vagas, 0), "
            "COUNT(s.id), COALESCE(SUM(CASE WHEN s.ativo THEN 1 ELSE 0 END), 0) "
            "FROM CAMARA c "
            "JOIN PREDIO p ON p.id = c.predio_id "
            "LEFT JOIN SENSOR s ON s.camara_id = c.id "
            "GROUP BY c.id, c.predio_id, c.nome, p.nome, c.capacidade_vagas "
            "ORDER BY c.id DESC"
        )
        camaras = []
        for row in cur.fetchall():
            camaras.append({
                "id": row[0],
                "predio_id": row[1],
                "nome": row[2],
                "predio": row[3],
                "capacidade_vagas": row[4],
                "total_sensores": row[5],
                "sensores_ativos": row[6]
            })

        return {
            "total_predios": total_predios,
            "total_camaras": total_camaras,
            "total_sensores": total_sensores,
            "sensores_ativos": sensores_ativos,
            "lista_sensores": sensores,
            "lista_predios": predios,
            "lista_camaras": camaras
        }
    finally:
        cur.close()
        release_db_connection(conn)

def fetch_pagina_produtos_data():
    """Monta dados da página de produtos e lotes sem produto.

    Retorna produtos com cliente, SKU, unidade e contagem de lotes, além de
    EPCs ainda não associados a produtos válidos.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        _ensure_lote_produto_assoc_table(cur)

        cur.execute(
            "SELECT pt.id, pt.cliente_id, COALESCE(c.nome_razao_social, '-'), pt.nome, pt.sku, pt.unidade_medida, COUNT(DISTINCT lt.epc_tag) "
            "FROM PRODUTO_TIPO pt "
            "LEFT JOIN CLIENTE c ON c.id = pt.cliente_id "
            "LEFT JOIN LOTE_TAGGEADO lt ON lt.produto_tipo_id = pt.id "
            "GROUP BY pt.id, pt.cliente_id, c.nome_razao_social, pt.nome, pt.sku, pt.unidade_medida "
            "ORDER BY pt.nome"
        )
        produtos = []
        for row in cur.fetchall():
            produtos.append({
                "id": row[0],
                "cliente_id": row[1],
                "cliente_nome": row[2],
                "nome": row[3],
                "sku": row[4],
                "unidade_medida": row[5],
                "total_lotes": row[6]
            })

        cur.execute(
            "SELECT epc_tag FROM LOTE_TAGGEADO "
            "WHERE NOT EXISTS (SELECT 1 FROM LOTE_PRODUTO_ASSOC lpa WHERE lpa.epc_tag = LOTE_TAGGEADO.epc_tag) "
            "AND (produto_tipo_id IS NULL OR produto_tipo_id NOT IN (SELECT id FROM PRODUTO_TIPO)) "
            "ORDER BY epc_tag"
        )
        lotes_sem_produto = [{"epc_tag": row[0]} for row in cur.fetchall()]

        return {
            "produtos": produtos,
            "lotes_sem_produto": lotes_sem_produto
        }
    finally:
        cur.close()
        release_db_connection(conn)

def create_produto_tipo(cliente_id=None, nome=None, sku=None, unidade_medida=None):
    """Cria um tipo de produto.

    Parâmetros:
        cliente_id: cliente dono do produto ou None.
        nome: nome do produto.
        sku: código SKU opcional.
        unidade_medida: unidade de controle, como un ou kg.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if cliente_id is not None:
            cur.execute("SELECT 1 FROM CLIENTE WHERE id = %s", (cliente_id,))
            if not cur.fetchone():
                raise ValueError("Cliente not found")

        cur.execute(
            "INSERT INTO PRODUTO_TIPO (cliente_id, nome, sku, unidade_medida) "
            "VALUES (%s, %s, %s, %s) RETURNING id, cliente_id, nome, sku, unidade_medida",
            (cliente_id, nome, sku, unidade_medida)
        )
        row = cur.fetchone()
        conn.commit()
        return {
            "id": row[0],
            "cliente_id": row[1],
            "nome": row[2],
            "sku": row[3],
            "unidade_medida": row[4]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def update_produto_tipo(produto_id, cliente_id=None, nome=None, sku=None, unidade_medida=None):
    """Atualiza um tipo de produto existente.

    Parâmetros:
        produto_id: id do produto.
        cliente_id: novo cliente associado ou None.
        nome: novo nome.
        sku: novo SKU opcional.
        unidade_medida: nova unidade de medida opcional.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM PRODUTO_TIPO WHERE id = %s", (produto_id,))
        if not cur.fetchone():
            raise ValueError("Produto not found")

        if cliente_id is not None:
            cur.execute("SELECT 1 FROM CLIENTE WHERE id = %s", (cliente_id,))
            if not cur.fetchone():
                raise ValueError("Cliente not found")

        cur.execute(
            "UPDATE PRODUTO_TIPO SET cliente_id = %s, nome = %s, sku = %s, unidade_medida = %s "
            "WHERE id = %s RETURNING id, cliente_id, nome, sku, unidade_medida",
            (cliente_id, nome, sku, unidade_medida, produto_id)
        )
        row = cur.fetchone()
        conn.commit()
        return {
            "id": row[0],
            "cliente_id": row[1],
            "nome": row[2],
            "sku": row[3],
            "unidade_medida": row[4]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def delete_produto_tipo(produto_id):
    """Exclui um tipo de produto sem lotes vinculados.

    Parâmetros:
        produto_id: id do tipo de produto.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM LOTE_TAGGEADO WHERE produto_tipo_id = %s", (produto_id,))
        if cur.fetchone()[0] > 0:
            raise ValueError("Cannot delete produto with existing lotes")

        cur.execute("DELETE FROM PRODUTO_TIPO WHERE id = %s RETURNING id", (produto_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Produto not found")

        conn.commit()
        return {"id": row[0]}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def update_lote_taggeado(epc_tag, produto_assoc=None):
    """Atualiza os produtos e quantidades associados a um lote taggeado.

    Parâmetros:
        epc_tag: identificador EPC do lote.
        produto_assoc: lista de itens com produto_tipo_id e quantidade.

    Normaliza duplicidades, valida quantidades e reorganiza ocupação da câmara
    se o lote estiver em uma movimentação aberta.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        _ensure_lote_produto_assoc_table(cur)

        cur.execute("SELECT 1 FROM LOTE_TAGGEADO WHERE epc_tag = %s", (epc_tag,))
        if not cur.fetchone():
            raise ValueError("Lote not found")

        produto_assoc = produto_assoc or []
        if not produto_assoc:
            raise ValueError("Lote must have at least one produto associado")

        normalized_assoc = {}
        for item in produto_assoc:
            produto_id = int(item.get('produto_tipo_id'))
            quantidade = float(item.get('quantidade'))

            if produto_id <= 0:
                raise ValueError("Produto not found")
            if quantidade <= 0:
                raise ValueError("Invalid quantidade for produto")

            normalized_assoc[produto_id] = normalized_assoc.get(produto_id, 0) + quantidade

        produto_tipo_ids = sorted(normalized_assoc.keys())

        cur.execute("SELECT id, unidade_medida FROM PRODUTO_TIPO WHERE id = ANY(%s)", (produto_tipo_ids,))
        produto_rows = cur.fetchall()
        found_ids = {row[0] for row in produto_rows}
        if len(found_ids) != len(produto_tipo_ids):
            raise ValueError("Produto not found")

        unidade_by_produto = {
            row[0]: ((row[1] or '').strip().lower())
            for row in produto_rows
        }

        for produto_id, quantidade in normalized_assoc.items():
            if unidade_by_produto.get(produto_id) in ('un', 'unidade') and not float(quantidade).is_integer():
                raise ValueError("Produtos em unidade (un) devem usar quantidade inteira")

        cur.execute("DELETE FROM LOTE_PRODUTO_ASSOC WHERE epc_tag = %s", (epc_tag,))
        for produto_id in produto_tipo_ids:
            cur.execute(
                "INSERT INTO LOTE_PRODUTO_ASSOC (epc_tag, produto_tipo_id, quantidade) VALUES (%s, %s, %s)",
                (epc_tag, produto_id, normalized_assoc[produto_id])
            )

        quantidade_total = sum(normalized_assoc.values())

        cur.execute(
            "UPDATE LOTE_TAGGEADO SET produto_tipo_id = %s, quantidade_atual = %s "
            "WHERE epc_tag = %s RETURNING epc_tag, produto_tipo_id, quantidade_atual, status",
            (produto_tipo_ids[0], quantidade_total, epc_tag)
        )
        row = cur.fetchone()

        cur.execute(
            "SELECT camara_id FROM MOVIMENTACAO "
            "WHERE epc_tag = %s AND data_saida IS NULL "
            "ORDER BY data_entrada DESC LIMIT 1",
            (epc_tag,)
        )
        open_camara = cur.fetchone()
        if open_camara:
            _repack_open_movimentacoes(cur, open_camara[0])

        cur.execute(
            "SELECT lp.produto_tipo_id, COALESCE(pt.nome, 'Produto sem nome'), lp.quantidade "
            "FROM LOTE_PRODUTO_ASSOC lp "
            "LEFT JOIN PRODUTO_TIPO pt ON pt.id = lp.produto_tipo_id "
            "WHERE lp.epc_tag = %s ORDER BY lp.produto_tipo_id",
            (epc_tag,)
        )
        produtos = cur.fetchall()

        conn.commit()
        return {
            "epc_tag": row[0],
            "produto_tipo_id": row[1],
            "produto_tipo_ids": [produto[0] for produto in produtos],
            "quantidade_atual": row[2],
            "status": row[3],
            "produto_nomes": [produto[1] for produto in produtos],
            "produto_assoc": [
                {
                    "produto_tipo_id": produto[0],
                    "produto_nome": produto[1],
                    "quantidade": produto[2]
                }
                for produto in produtos
            ]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def move_lote_to_camara(epc_tag, camara_id):
    """Move um lote para outra câmara.

    Parâmetros:
        epc_tag: identificador EPC do lote.
        camara_id: câmara de destino.

    Fecha a movimentação aberta anterior, encontra vaga disponível na câmara
    destino e cria uma nova movimentação.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT quantidade_atual FROM LOTE_TAGGEADO WHERE epc_tag = %s", (epc_tag,))
        lote_row = cur.fetchone()
        if not lote_row:
            raise ValueError("Lote not found")

        cur.execute("SELECT 1 FROM CAMARA WHERE id = %s", (camara_id,))
        if not cur.fetchone():
            raise ValueError("Camara not found")

        cur.execute(
            "SELECT id, camara_id FROM MOVIMENTACAO "
            "WHERE epc_tag = %s AND data_saida IS NULL "
            "ORDER BY data_entrada DESC, id DESC LIMIT 1",
            (epc_tag,)
        )
        open_mov = cur.fetchone()

        origem_camara_id = None
        if open_mov:
            origem_mov_id = open_mov[0]
            origem_camara_id = open_mov[1]

            if origem_camara_id == camara_id:
                raise ValueError("Lote already in destination camara")

            cur.execute("UPDATE MOVIMENTACAO SET data_saida = NOW() WHERE id = %s", (origem_mov_id,))
            _repack_open_movimentacoes(cur, origem_camara_id, strict=False)

        batch_size = _batch_size_from_qty(lote_row[0])
        pos_vaga = _find_available_slot(cur, camara_id, batch_size)
        if pos_vaga is None:
            raise ValueError("No available slots in camara")

        cur.execute(
            "INSERT INTO MOVIMENTACAO (epc_tag, camara_id, posicao_vaga, data_entrada) VALUES (%s, %s, %s, NOW()) "
            "RETURNING id, data_entrada",
            (epc_tag, camara_id, pos_vaga)
        )
        mov_row = cur.fetchone()

        _repack_open_movimentacoes(cur, camara_id)

        conn.commit()
        return {
            "movimentacao_id": mov_row[0],
            "epc_tag": epc_tag,
            "camara_origem_id": origem_camara_id,
            "camara_destino_id": camara_id,
            "posicao_vaga": pos_vaga,
            "data_entrada": mov_row[1].strftime("%Y-%m-%d %H:%M:%S") if mov_row[1] else None
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def fetch_camara_detalhes(camara_id):
    """Busca detalhes de ocupação de uma câmara.

    Parâmetros:
        camara_id: id da câmara.

    Retorna metadados da câmara, lotes atualmente dentro dela, ocupação total
    e aviso de capacidade quando aplicável.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Get camara info
        cur.execute(
            "SELECT c.id, c.nome, p.nome, c.capacidade_vagas "
            "FROM CAMARA c "
            "JOIN PREDIO p ON p.id = c.predio_id "
            "WHERE c.id = %s",
            (camara_id,)
        )
        camara_row = cur.fetchone()
        if not camara_row:
            return None

        camara_info = {
            "id": camara_row[0],
            "nome": camara_row[1],
            "predio": camara_row[2],
            "capacidade": camara_row[3]
        }

        pack_info = _repack_open_movimentacoes(cur, camara_id, strict=False)

        # Get batches currently in this camara
        cur.execute(
            "SELECT m.epc_tag, pt.nome, m.data_entrada, l.quantidade_atual, m.posicao_vaga "
            "FROM MOVIMENTACAO m "
            "LEFT JOIN LOTE_TAGGEADO l ON l.epc_tag = m.epc_tag "
            "LEFT JOIN PRODUTO_TIPO pt ON pt.id = l.produto_tipo_id "
            "WHERE m.camara_id = %s AND m.data_saida IS NULL "
            "ORDER BY m.posicao_vaga ASC",
            (camara_id,)
        )
        batches = []
        for row in cur.fetchall():
            batches.append({
                "epc_tag": row[0],
                "produto": row[1] or "Sem produto",
                "data_entrada": row[2].strftime("%Y-%m-%d %H:%M:%S") if row[2] else None,
                "quantidade": row[3] or 1,
                "posicao_vaga": row[4]
            })
        
        camara_info["lotes"] = batches
        camara_info["ocupacao_total"] = pack_info["total_required"]
        camara_info["over_capacity"] = pack_info["over_capacity"]
        if pack_info["over_capacity"]:
            camara_info["warning"] = f"Capacidade excedida: {pack_info['total_required']}/{pack_info['capacity']}"
        return camara_info
    finally:
        cur.close()
        release_db_connection(conn)

def _find_available_slot(cur, camara_id, batch_size):
    """Localiza o primeiro intervalo contíguo de vagas livres.

    Parâmetros:
        cur: cursor PostgreSQL da transação atual.
        camara_id: câmara onde a vaga será procurada.
        batch_size: quantidade de vagas contíguas necessárias.

    Retorna o índice inicial da vaga ou None quando não há espaço.
    """
    # 1. Get capacity
    capacity = _camera_capacity(cur, camara_id)

    # 2. Get current occupancy (open movimentacoes)
    cur.execute(
        "SELECT m.posicao_vaga, l.quantidade_atual "
        "FROM MOVIMENTACAO m "
        "LEFT JOIN LOTE_TAGGEADO l ON l.epc_tag = m.epc_tag "
        "WHERE m.camara_id = %s AND m.data_saida IS NULL AND m.posicao_vaga IS NOT NULL",
        (camara_id,)
    )
    
    occupied = [False] * capacity
    for pos_vaga, qty in cur.fetchall():
        q = _batch_size_from_qty(qty)
        for i in range(pos_vaga, min(pos_vaga + q, capacity)):
            occupied[i] = True

    # 3. Find contiguous space
    for i in range(capacity - batch_size + 1):
        if not any(occupied[i : i + batch_size]):
            return i
            
    return None # No space left
