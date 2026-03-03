import os
import psycopg2
from psycopg2 import pool
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIGURAÇÃO ---
load_dotenv()
app = Flask(__name__)
CORS(app)

# Credenciais do banco de dados (coloque-os em um .env)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "fabritag")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "1234")

# Inicializa o pool de conexões com PostgreSQL
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

# --- ROTAS DA API ---

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "Fabritag Backend Online (PostgreSQL Ready)", "version": "2.0.0"})

@app.route('/api/produtos', methods=['GET'])
def get_produtos():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Vamos retornar tags EPC como "produtos" caso PRODUTO_TIPO ainda não esteja populada
        cur.execute("SELECT epc_tag FROM LOTE_TAGGEADO")
        rows = cur.fetchall()
        if not rows:
            # Contingência: obter tags distintas de movimentações se LOTE_TAGGEADO estiver vazia
            cur.execute("SELECT DISTINCT epc_tag FROM MOVIMENTACAO")
            rows = cur.fetchall()
            
        produtos = [{"id": row[0], "nome": row[0]} for row in rows]
        return jsonify(produtos)
    finally:
        cur.close()
        release_db_connection(conn)

@app.route('/api/camaras', methods=['GET'])
def get_camaras():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nome FROM CAMARA")
        camaras = [{"id": row[0], "nome": row[1]} for row in cur.fetchall()]
        return jsonify(camaras)
    finally:
        cur.close()
        release_db_connection(conn)

@app.route('/api/tag_event', methods=['POST'])
def handle_tag_event():
    """
    Recebe eventos do ESP32:
    { "epc_tag": "A1B2C3D4", "sensor_id": 1, "event": "ARRIVED" or "REMOVED", "rssi": -60 }
    """
    data = request.json
    epc_tag = data.get('epc_tag')
    sensor_id = data.get('sensor_id')
    event = data.get('event')
    rssi = data.get('rssi', 0)

    if not epc_tag or not sensor_id or not event:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. Registrar leitura bruta
        cur.execute(
            "INSERT INTO LEITURA_BRUTA (epc_tag, sensor_id, rssi) VALUES (%s, %s, %s)",
            (epc_tag, sensor_id, rssi)
        )

        # 2. Buscar câmara associada ao sensor
        cur.execute("SELECT camara_id FROM SENSOR WHERE id = %s", (sensor_id,))
        camara_res = cur.fetchone()
        if not camara_res:
            return jsonify({"error": "Sensor not found in DB"}), 404
        camara_id = camara_res[0]

        # 3. Garantir que LOTE_TAGGEADO exista (auto-cadastro por enquanto)
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
        return jsonify({"message": f"Event {event} processed successfully"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        release_db_connection(conn)

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM CAMARA")
        total_camaras = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM SENSOR")
        total_sensores = cur.fetchone()[0]

        # Contar o total de tags identificadas
        cur.execute("SELECT COUNT(DISTINCT epc_tag) FROM LOTE_TAGGEADO")
        total_produtos = cur.fetchone()[0]
        
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
                "origem": "Câmara de Testes", # Simplificado para MVP
                "destino": row[2],
                "data": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None
            })

        return jsonify({
            "total_camaras": total_camaras,
            "total_sensores": total_sensores,
            "total_produtos": total_produtos,
            "ultimas_movimentacoes": movimentacoes
        })
    finally:
        cur.close()
        release_db_connection(conn)

if __name__ == '__main__':
    print("Starting Fabritag PostgreSQL Backend...")
    app.run(debug=True, host='0.0.0.0', port=5000)
