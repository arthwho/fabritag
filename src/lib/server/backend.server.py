from flask import Flask, jsonify, request
from flask_cors import CORS
import database_manager as db
from auth import auth_bp, init_auth_schema

app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)


def value_error_status(message):
    """Converte mensagens de ValueError em status HTTP apropriado.

    Parâmetros:
        message: texto da exceção levantada pela camada de banco.

    Retorna 400 para entrada inválida, 409 para conflitos de regra e 404 para
    recursos inexistentes.
    """
    normalized = (message or "").lower()
    if normalized.startswith("cannot delete"):
        return 409
    if "capacity exceeded" in normalized or ("capacidade" in normalized and "excedida" in normalized):
        return 409
    if "no available slots" in normalized or "already in destination" in normalized:
        return 409
    if "missing required field" in normalized or "invalid" in normalized:
        return 400
    if "devem usar quantidade inteira" in normalized:
        return 400
    return 404

# --- ROUTES ---

@app.route('/api/status', methods=['GET'])
def get_status():
    """Retorna o status básico do backend.

    Usada por health checks ou telas que precisam confirmar que a API Flask
    está online e conectada ao PostgreSQL.
    """
    return jsonify({"status": "Fabritag Backend Online (PostgreSQL Ready)", "version": "2.0.0"})

@app.route('/api/produto-tipos', methods=['GET'])
def get_produto_tipos():
    """Lista tipos de produtos em formato compacto.

    Chama db.fetch_produtos() e retorna JSON para preenchimento de seletores.
    """
    try:
        produtos = db.fetch_produtos()
        return jsonify(produtos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/clientes', methods=['GET'])
def get_clientes():
    """Lista clientes cadastrados.

    Encapsula db.fetch_clientes() e converte falhas inesperadas em HTTP 500.
    """
    try:
        clientes = db.fetch_clientes()
        return jsonify(clientes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/clientes', methods=['POST'])
def create_cliente():
    """Cria um cliente a partir do JSON da requisição.

    Campos esperados:
        cpf_cnpj: documento opcional.
        nome_razao_social: nome ou razão social opcional.
    """
    data = request.json or {}
    cpf_cnpj = data.get('cpf_cnpj')
    nome_razao_social = data.get('nome_razao_social')

    try:
        cliente = db.create_cliente(
            cpf_cnpj=cpf_cnpj,
            nome_razao_social=nome_razao_social
        )
        return jsonify(cliente), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/clientes/<int:cliente_id>', methods=['PUT'])
def update_cliente(cliente_id):
    """Atualiza um cliente pelo id da rota.

    Parâmetros:
        cliente_id: identificador do cliente no caminho da URL.
    """
    data = request.json or {}
    cpf_cnpj = data.get('cpf_cnpj')
    nome_razao_social = data.get('nome_razao_social')

    try:
        cliente = db.update_cliente(
            cliente_id=cliente_id,
            cpf_cnpj=cpf_cnpj,
            nome_razao_social=nome_razao_social
        )
        return jsonify(cliente), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/clientes/<int:cliente_id>', methods=['DELETE'])
def delete_cliente(cliente_id):
    """Exclui um cliente pelo id da rota.

    Parâmetros:
        cliente_id: identificador do cliente no caminho da URL.
    """
    try:
        result = db.delete_cliente(cliente_id=cliente_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/produtos', methods=['POST'])
def create_produto():
    """Cria um tipo de produto.

    Espera JSON com nome obrigatório e cliente_id, sku, unidade_medida opcionais.
    Normaliza cliente_id vazio para None antes de chamar a camada de banco.
    """
    data = request.json or {}
    nome = data.get('nome')
    cliente_id = data.get('cliente_id')
    sku = data.get('sku')
    unidade_medida = data.get('unidade_medida')

    if cliente_id in ('', None):
        cliente_id = None

    if not nome:
        return jsonify({"error": "Missing required field: nome"}), 400

    try:
        produto = db.create_produto_tipo(
            cliente_id=cliente_id,
            nome=nome,
            sku=sku,
            unidade_medida=unidade_medida
        )
        return jsonify(produto), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/produtos/<int:produto_id>', methods=['PUT'])
def update_produto(produto_id):
    """Atualiza um tipo de produto existente.

    Parâmetros:
        produto_id: id do produto recebido na rota.

    Usa os mesmos campos de create_produto().
    """
    data = request.json or {}
    nome = data.get('nome')
    cliente_id = data.get('cliente_id')
    sku = data.get('sku')
    unidade_medida = data.get('unidade_medida')

    if cliente_id in ('', None):
        cliente_id = None

    if not nome:
        return jsonify({"error": "Missing required field: nome"}), 400

    try:
        produto = db.update_produto_tipo(
            produto_id=produto_id,
            cliente_id=cliente_id,
            nome=nome,
            sku=sku,
            unidade_medida=unidade_medida
        )
        return jsonify(produto), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/produtos/<int:produto_id>', methods=['DELETE'])
def delete_produto(produto_id):
    """Exclui um tipo de produto.

    Parâmetros:
        produto_id: id do produto recebido na rota.
    """
    try:
        result = db.delete_produto_tipo(produto_id=produto_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/batches', methods=['GET'])
@app.route('/api/lotes', methods=['GET'])
def get_batches():
    """Lista lotes taggeados.

    Atende tanto /api/batches quanto /api/lotes e retorna a estrutura preparada
    por db.fetch_batch().
    """
    try:
        batches = db.fetch_batch()
        return jsonify(batches)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/lotes/<string:epc_tag>', methods=['PUT'])
def update_lote(epc_tag):
    """Atualiza produtos e quantidades associados a um lote.

    Parâmetros:
        epc_tag: identificador EPC recebido na rota.

    Aceita o formato novo produto_assoc ou monta esse formato a partir dos
    campos legados produto_tipo_ids/produto_tipo_id e quantidade_atual.
    """
    data = request.json or {}
    produto_assoc = data.get('produto_assoc')
    produto_tipo_ids = data.get('produto_tipo_ids')
    produto_tipo_id = data.get('produto_tipo_id')
    quantidade_atual = data.get('quantidade_atual')

    if produto_assoc is None:
        if produto_tipo_ids is None:
            produto_tipo_ids = [produto_tipo_id] if produto_tipo_id not in ('', None) else []

        if quantidade_atual is None:
            return jsonify({"error": "Missing required field: quantidade_atual"}), 400

        if not isinstance(produto_tipo_ids, list) or len(produto_tipo_ids) == 0:
            return jsonify({"error": "Missing required field: produto_tipo_ids"}), 400

        try:
            quantidade_atual = float(quantidade_atual)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid field: quantidade_atual"}), 400

        if quantidade_atual <= 0:
            return jsonify({"error": "Invalid field: quantidade_atual"}), 400

        try:
            produto_tipo_ids = [int(produto_id) for produto_id in produto_tipo_ids]
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid field: produto_tipo_ids"}), 400

        produto_assoc = [
            {
                "produto_tipo_id": produto_id,
                "quantidade": quantidade_atual
            }
            for produto_id in produto_tipo_ids
        ]
    elif not isinstance(produto_assoc, list) or len(produto_assoc) == 0:
        return jsonify({"error": "Missing required field: produto_assoc"}), 400

    try:
        lote = db.update_lote_taggeado(
            epc_tag=epc_tag,
            produto_assoc=produto_assoc
        )
        return jsonify(lote), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/lotes/<string:epc_tag>/movimentar', methods=['POST'])
def move_lote(epc_tag):
    """Move um lote para uma câmara.

    Parâmetros:
        epc_tag: identificador EPC recebido na rota.

    Espera JSON com camara_id válido e retorna a movimentação criada.
    """
    data = request.json or {}
    camara_id = data.get('camara_id')

    if camara_id in ('', None):
        return jsonify({"error": "Missing required field: camara_id"}), 400

    try:
        camara_id = int(camara_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid field: camara_id"}), 400

    if camara_id <= 0:
        return jsonify({"error": "Invalid field: camara_id"}), 400

    try:
        movimentacao = db.move_lote_to_camara(epc_tag=epc_tag, camara_id=camara_id)
        return jsonify(movimentacao), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/camaras', methods=['GET'])
def get_camaras():
    """Lista câmaras em formato simples.

    Retorna id e nome para uso em formulários e seletores.
    """
    try:
        camaras = db.fetch_camaras()
        return jsonify(camaras)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predios', methods=['POST'])
def create_predio():
    """Cria um prédio.

    Espera JSON com nome obrigatório e endereço opcional.
    """
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


@app.route('/api/predios/<int:predio_id>', methods=['PUT'])
def update_predio(predio_id):
    """Atualiza um prédio.

    Parâmetros:
        predio_id: id do prédio recebido na rota.
    """
    data = request.json or {}
    nome = data.get('nome')
    endereco = data.get('endereco')

    if not nome:
        return jsonify({"error": "Missing required field: nome"}), 400

    try:
        predio = db.update_predio(predio_id=predio_id, nome=nome, endereco=endereco)
        return jsonify(predio), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/predios/<int:predio_id>', methods=['DELETE'])
def delete_predio(predio_id):
    """Exclui um prédio.

    Parâmetros:
        predio_id: id do prédio recebido na rota.
    """
    try:
        result = db.delete_predio(predio_id=predio_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/camaras/<int:camara_id>', methods=['GET'])
def get_camara_detalhes(camara_id):
    """Retorna detalhes e ocupação de uma câmara.

    Parâmetros:
        camara_id: id da câmara recebido na rota.
    """
    try:
        camara = db.fetch_camara_detalhes(camara_id)
        if not camara:
            return jsonify({"error": "Camara not found"}), 404
        return jsonify(camara), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/camaras', methods=['POST'])
def create_camara():
    """Cria uma câmara.

    Espera JSON com predio_id e nome obrigatórios, além de capacidade_vagas
    opcional.
    """
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
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/camaras/<int:camara_id>', methods=['PUT'])
def update_camara(camara_id):
    """Atualiza uma câmara.

    Parâmetros:
        camara_id: id da câmara recebido na rota.
    """
    data = request.json or {}
    predio_id = data.get('predio_id')
    nome = data.get('nome')
    capacidade_vagas = data.get('capacidade_vagas')

    if predio_id is None or not nome:
        return jsonify({"error": "Missing required fields: predio_id and nome"}), 400

    try:
        camara = db.update_camara(
            camara_id=camara_id,
            predio_id=predio_id,
            nome=nome,
            capacidade_vagas=capacidade_vagas
        )
        return jsonify(camara), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/camaras/<int:camara_id>', methods=['DELETE'])
def delete_camara(camara_id):
    """Exclui uma câmara.

    Parâmetros:
        camara_id: id da câmara recebido na rota.
    """
    try:
        result = db.delete_camara(camara_id=camara_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sensores', methods=['POST'])
def create_sensor():
    """Cria um sensor.

    Espera JSON com camara_id obrigatório e modelo/ativo opcionais.
    """
    data = request.json or {}
    camara_id = data.get('camara_id')
    modelo = data.get('modelo', 'PN5180')
    ativo = data.get('ativo', True)

    if camara_id is None:
        return jsonify({"error": "Missing required field: camara_id"}), 400

    try:
        sensor = db.create_sensor(
            camara_id=camara_id,
            modelo=modelo,
            ativo=ativo
        )
        return jsonify(sensor), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sensores/<int:sensor_id>', methods=['PUT'])
def update_sensor(sensor_id):
    """Atualiza um sensor.

    Parâmetros:
        sensor_id: id do sensor recebido na rota.
    """
    data = request.json or {}
    camara_id = data.get('camara_id')
    modelo = data.get('modelo', 'PN5180')
    ativo = data.get('ativo', True)

    if camara_id is None:
        return jsonify({"error": "Missing required field: camara_id"}), 400

    try:
        sensor = db.update_sensor(
            sensor_id=sensor_id,
            camara_id=camara_id,
            modelo=modelo,
            ativo=ativo
        )
        return jsonify(sensor), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sensores/<int:sensor_id>', methods=['DELETE'])
def delete_sensor(sensor_id):
    """Exclui um sensor.

    Parâmetros:
        sensor_id: id do sensor recebido na rota.
    """
    try:
        result = db.delete_sensor(sensor_id=sensor_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), value_error_status(str(e))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tag_event', methods=['POST'])
def handle_tag_event():
    """Recebe eventos RFID de sensores.

    Espera JSON com epc_tag, sensor_id e rssi opcional. Encaminha o
    processamento para db.process_tag_event().
    """
    data = request.json
    epc_tag = data.get('epc_tag')
    sensor_id = data.get('sensor_id')
    event = data.get('event', 'READ')
    rssi = data.get('rssi', 0)

    if not epc_tag or not sensor_id:
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
    """Retorna dados consolidados para o dashboard.

    A resposta inclui contadores e últimas movimentações calculadas no banco.
    """
    try:
        dashboard_data = db.fetch_dashboard_data()
        return jsonify(dashboard_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/infraestrutura', methods=['GET'])
def get_infraestrutura():
    """Retorna dados consolidados da infraestrutura.

    Inclui prédios, câmaras, sensores e contadores para a tela administrativa.
    """
    try:
        infra_data = db.fetch_infraestrutura_data()
        return jsonify(infra_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/produtos', methods=['GET'])
def get_produtos():
    """Retorna dados completos da página de produtos.

    Inclui produtos cadastrados e lotes ainda sem associação válida.
    """
    try:
        produtos_data = db.fetch_pagina_produtos_data()
        return jsonify(produtos_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


import time

# Temporary dictionary to store live device statuses
# In the future, this can be moved into your PostgreSQL db.
live_devices = {}

@app.route('/api/dispositivos/ping', methods=['POST'])
def dispositivo_ping():
    """Registra heartbeat de um dispositivo.

    Espera JSON com dispositivo_id. Atualiza o status em memória usando o IP
    remoto e o timestamp atual.
    """
    data = request.json or {}
    dispositivo_id = data.get('dispositivo_id')
    
    # Flask automatically grabs the IP of whatever device sent the request!
    ip_address = request.remote_addr 
    
    if not dispositivo_id:
        return jsonify({"error": "Missing dispositivo_id"}), 400

    # Record the heartbeat timestamp and IP
    live_devices[str(dispositivo_id)] = {
        "last_seen": time.time(),
        "ip_address": ip_address,
        "status": "Online"
    }
    return jsonify({"message": "Heartbeat acknowledged"}), 200

@app.route('/api/dispositivos/status/<dispositivo_id>', methods=['GET'])
def get_dispositivo_status(dispositivo_id):
    """Consulta o status em memória de um dispositivo.

    Parâmetros:
        dispositivo_id: id recebido na rota.

    Considera o dispositivo offline quando o último ping passou de 15 segundos.
    """
    dispositivo = live_devices.get(str(dispositivo_id))

    if dispositivo:
        # If we haven't heard from the ESP32 in over 15 seconds, consider it offline
        if time.time() - dispositivo["last_seen"] > 15:
            dispositivo["status"] = "Offline"
        return jsonify(dispositivo), 200
        
    # If the sensor has never pinged the server since the server booted
    return jsonify({"status": "Unknown", "ip_address": "N/A"}), 404

@app.route('/api/dispositivos/status', methods=['GET'])
def get_all_dispositivo_statuses():
    """Lista o status de todos os dispositivos que já enviaram ping.

    Recalcula o estado offline com base no tempo desde last_seen e retorna um
    objeto indexado pelo id do dispositivo.
    """
    current_time = time.time()
    results = {}
    for sid, info in live_devices.items():
        status = info["status"]
        if current_time - info["last_seen"] > 15:
            status = "Offline"
        results[sid] = {
            "status": status,
            "ip_address": info["ip_address"]
        }
    return jsonify(results), 200

if __name__ == '__main__':
    print("Starting Fabritag Backend (Modularized)...")
    init_auth_schema()
    app.run(debug=True, host='0.0.0.0', port=5000)
