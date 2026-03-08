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

def fetch_produtos():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT epc_tag FROM LOTE_TAGGEADO")
        rows = cur.fetchall()
        if not rows:
            cur.execute("SELECT DISTINCT epc_tag FROM MOVIMENTACAO")
            rows = cur.fetchall()
        return [{"id": row[0], "nome": row[0]} for row in rows]
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
        total_produtos = cur.fetchone()[0]

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
            "total_produtos": total_produtos,
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
            "SELECT s.id, s.modelo, s.ip_address, c.nome, s.ativo "
            "FROM SENSOR s "
            "JOIN CAMARA c ON s.camara_id = c.id "
            "ORDER BY s.id DESC"
        )
        sensores = []
        for row in cur.fetchall():
            sensores.append({
                "id": row[0],
                "modelo": row[1],
                "ip": row[2],
                "camara": row[3],
                "status": "Ativo" if row[4] else "Inativo"
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
            "SELECT c.id, c.nome, p.nome, COALESCE(c.capacidade_vagas, 0), "
            "COUNT(s.id), COALESCE(SUM(CASE WHEN s.ativo THEN 1 ELSE 0 END), 0) "
            "FROM CAMARA c "
            "JOIN PREDIO p ON p.id = c.predio_id "
            "LEFT JOIN SENSOR s ON s.camara_id = c.id "
            "GROUP BY c.id, c.nome, p.nome, c.capacidade_vagas "
            "ORDER BY c.id DESC"
        )
        camaras = []
        for row in cur.fetchall():
            camaras.append({
                "id": row[0],
                "nome": row[1],
                "predio": row[2],
                "capacidade_vagas": row[3],
                "total_sensores": row[4],
                "sensores_ativos": row[5]
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
