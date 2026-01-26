import json
import os
from flask import Flask, jsonify, request
from datetime import datetime

# --- CONFIGURAÇÃO ---
app = Flask(__name__)
# Aponta para o 'fabritag_db.json' na raiz do projeto
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
DB_FILE = os.path.join(PROJECT_ROOT, 'fabritag_db.json')

# --- FUNÇÕES AUXILIARES DE BANCO DE DADOS (JSON) ---

def load_db():
    """Carrega o banco de dados do arquivo JSON ou cria um padrão se não existir."""
    if not os.path.exists(DB_FILE):
        initial_data = {
            "produtos": [],
            "camaras": [
                {"id": 1, "nome": "Câmara Fria 01", "predio": "Bloco A"},
                {"id": 2, "nome": "Câmara Seca 02", "predio": "Bloco B"}
            ],
            "sensores": [],
            "movimentacoes": []
        }
        save_db(initial_data)
        return initial_data
    
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    """Salva os dados no arquivo JSON."""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- ROTAS DA API ---

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "Fabritag Backend Online", "version": "1.0.0"})

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    db = load_db()
    stats = {
        "total_produtos": len(db['produtos']),
        "total_camaras": len(db['camaras']),
        "total_sensores": len(db['sensores']),
        "ultimas_movimentacoes": db['movimentacoes'][-5:] # Pega as 5 últimas
    }
    return jsonify(stats)

# --- PRODUTOS ---

@app.route('/api/produtos', methods=['GET', 'POST'])
def manage_products():
    db = load_db()
    
    if request.method == 'POST':
        novo_produto = request.json
        novo_produto['id'] = len(db['produtos']) + 1
        novo_produto['status'] = 'Cadastrado'
        novo_produto['local_atual'] = 'Recebimento'
        
        db['produtos'].append(novo_produto)
        save_db(db)
        return jsonify({"message": "Produto criado com sucesso", "produto": novo_produto}), 201
        
    return jsonify(db['produtos'])

@app.route('/api/camaras', methods=['GET'])
def get_camaras():
    db = load_db()
    return jsonify(db['camaras'])

# --- SENSORES & INFRA ---

@app.route('/api/sensores', methods=['GET', 'POST'])
def manage_sensors():
    db = load_db()
    
    if request.method == 'POST':
        novo_sensor = request.json
        novo_sensor['id'] = len(db['sensores']) + 1
        novo_sensor['status'] = 'Ativo'
        
        db['sensores'].append(novo_sensor)
        save_db(db)
        return jsonify({"message": "Sensor adicionado", "sensor": novo_sensor}), 201
        
    return jsonify(db['sensores'])

# --- MOVIMENTAÇÃO ---

@app.route('/api/movimentar', methods=['POST'])
def move_product():
    """
    Recebe { "produto_id": 1, "destino_id": 2 }
    """
    data = request.json
    db = load_db()
    
    # Busca Produto e Câmara
    produto = next((p for p in db['produtos'] if p['id'] == data['produto_id']), None)
    destino = next((c for c in db['camaras'] if c['id'] == data['destino_id']), None)
    
    if not produto or not destino:
        return jsonify({"error": "Produto ou Destino não encontrados"}), 404
    
    # Atualiza Produto
    origem_antiga = produto['local_atual']
    produto['local_atual'] = destino['nome']
    
    # Registra Movimentação
    nova_movimentacao = {
        "id": len(db['movimentacoes']) + 1,
        "produto": produto['nome'],
        "origem": origem_antiga,
        "destino": destino['nome'],
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    db['movimentacoes'].append(nova_movimentacao)
    save_db(db)
    
    return jsonify({"message": "Movimentação registrada", "detalhes": nova_movimentacao})

if __name__ == '__main__':
    # Roda o servidor na porta 5000
    print("Iniciando Fabritag Backend...")
    app.run(debug=True, port=5000)