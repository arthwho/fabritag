from flask import Flask, jsonify, request
from flask_cors import CORS
import database_manager as db

app = Flask(__name__)
CORS(app)

# --- ROUTES ---

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "Fabritag Backend Online (PostgreSQL Ready)", "version": "2.0.0"})

@app.route('/api/produtos', methods=['GET'])
def get_produtos():
    try:
        produtos = db.fetch_produtos()
        return jsonify(produtos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/camaras', methods=['GET'])
def get_camaras():
    try:
        camaras = db.fetch_camaras()
        return jsonify(camaras)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predios', methods=['POST'])
def create_predio():
    data = request.json or {}
    nome = data.get('nome')
    endereco = data.get('endereco')

    if not nome:
        return jsonify({"error": "Missing required field: nome"}), 400

    try:
        predio = db.create_predio(nome=nome, endereco=endereco)
        return jsonify(predio), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/camaras', methods=['POST'])
def create_camara():
    data = request.json or {}
    predio_id = data.get('predio_id')
    nome = data.get('nome')
    capacidade_vagas = data.get('capacidade_vagas')

    if predio_id is None or not nome:
        return jsonify({"error": "Missing required fields: predio_id and nome"}), 400

    try:
        camara = db.create_camara(
            predio_id=predio_id,
            nome=nome,
            capacidade_vagas=capacidade_vagas
        )
        return jsonify(camara), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sensores', methods=['POST'])
def create_sensor():
    data = request.json or {}
    camara_id = data.get('camara_id')
    modelo = data.get('modelo', 'PN5180')
    ip_address = data.get('ip_address')
    ativo = data.get('ativo', True)

    if camara_id is None:
        return jsonify({"error": "Missing required field: camara_id"}), 400

    try:
        sensor = db.create_sensor(
            camara_id=camara_id,
            modelo=modelo,
            ip_address=ip_address,
            ativo=ativo
        )
        return jsonify(sensor), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tag_event', methods=['POST'])
def handle_tag_event():
    data = request.json
    epc_tag = data.get('epc_tag')
    sensor_id = data.get('sensor_id')
    event = data.get('event')
    rssi = data.get('rssi', 0)

    if not epc_tag or not sensor_id or not event:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        success, message = db.process_tag_event(epc_tag, sensor_id, event, rssi)
        if not success:
            return jsonify({"error": message}), 404
        return jsonify({"message": message}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        dashboard_data = db.fetch_dashboard_data()
        return jsonify(dashboard_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/infraestrutura', methods=['GET'])
def get_infraestrutura():
    try:
        infra_data = db.fetch_infraestrutura_data()
        return jsonify(infra_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Fabritag Backend (Modularized)...")
    app.run(debug=True, host='0.0.0.0', port=5000)
