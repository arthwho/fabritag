import os
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
    return db_pool.getconn()

def release_db_connection(conn):
    db_pool.putconn(conn)

def fetch_batch():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT l.epc_tag, l.produto_tipo_id, l.quantidade_atual, l.status, "
            "COALESCE(pt.nome, 'Lote sem produto'), COALESCE(c_atual.nome, 'Desconhecido'), "
            "m_atual.data_entrada "
            "FROM LOTE_TAGGEADO l "
            "LEFT JOIN PRODUTO_TIPO pt ON pt.id = l.produto_tipo_id "
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
            rows = [(row[0], None, None, None, 'Lote sem produto', row[1], row[2]) for row in cur.fetchall()]
        return [
            {
                "id": row[0],
                "nome": f"{row[4]} ({row[0]})",
                "epc_tag": row[0],
                "produto_tipo_id": row[1],
                "quantidade_atual": row[2],
                "status": row[3],
                "produto_nome": row[4],
                "local_atual": row[5],
                "local_desde": row[6].strftime("%Y-%m-%d %H:%M:%S") if row[6] else None
            }
            for row in rows
        ]
    finally:
        cur.close()
        release_db_connection(conn)

def fetch_produtos():
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
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nome FROM CAMARA")
        return [{"id": row[0], "nome": row[1]} for row in cur.fetchall()]
    finally:
        cur.close()
        release_db_connection(conn)

def create_predio(nome, endereco=None):
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

def create_sensor(camara_id, modelo='PN5180', ip_address=None, ativo=True):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM CAMARA WHERE id = %s", (camara_id,))
        if not cur.fetchone():
            raise ValueError("Camara not found")

        cur.execute(
            "INSERT INTO SENSOR (camara_id, modelo, ip_address, ativo) "
            "VALUES (%s, %s, %s, %s) RETURNING id, camara_id, modelo, ip_address, ativo",
            (camara_id, modelo, ip_address, ativo)
        )
        row = cur.fetchone()
        conn.commit()
        return {
            "id": row[0],
            "camara_id": row[1],
            "modelo": row[2],
            "ip_address": row[3],
            "ativo": row[4]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def update_predio(predio_id, nome, endereco=None):
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

def update_sensor(sensor_id, camara_id, modelo='PN5180', ip_address=None, ativo=True):
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
            "UPDATE SENSOR SET camara_id = %s, modelo = %s, ip_address = %s, ativo = %s "
            "WHERE id = %s RETURNING id, camara_id, modelo, ip_address, ativo",
            (camara_id, modelo, ip_address, ativo, sensor_id)
        )
        row = cur.fetchone()

        conn.commit()
        return {
            "id": row[0],
            "camara_id": row[1],
            "modelo": row[2],
            "ip_address": row[3],
            "ativo": row[4]
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)

def delete_sensor(sensor_id):
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
                cur.execute(
                    "INSERT INTO MOVIMENTACAO (epc_tag, camara_id, data_entrada) VALUES (%s, %s, NOW())",
                    (epc_tag, camara_id)
                )
        
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
            "SELECT s.id, s.camara_id, s.modelo, s.ip_address, c.nome, s.ativo "
            "FROM SENSOR s "
            "JOIN CAMARA c ON s.camara_id = c.id "
            "ORDER BY s.id DESC"
        )
        sensores = []
        for row in cur.fetchall():
            sensores.append({
                "id": row[0],
                "camara_id": row[1],
                "modelo": row[2],
                "ip": row[3],
                "camara": row[4],
                "status": "Ativo" if row[5] else "Inativo",
                "ativo": row[5]
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
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT pt.id, pt.cliente_id, pt.nome, pt.sku, pt.unidade_medida, COUNT(DISTINCT lt.epc_tag) "
            "FROM PRODUTO_TIPO pt "
            "LEFT JOIN LOTE_TAGGEADO lt ON lt.produto_tipo_id = pt.id "
            "GROUP BY pt.id, pt.cliente_id, pt.nome, pt.sku, pt.unidade_medida "
            "ORDER BY pt.nome"
        )
        produtos = []
        for row in cur.fetchall():
            produtos.append({
                "id": row[0],
                "cliente_id": row[1],
                "nome": row[2],
                "sku": row[3],
                "unidade_medida": row[4],
                "total_lotes": row[5]
            })

        cur.execute(
            "SELECT epc_tag FROM LOTE_TAGGEADO "
            "WHERE produto_tipo_id IS NULL OR produto_tipo_id NOT IN (SELECT id FROM PRODUTO_TIPO) "
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