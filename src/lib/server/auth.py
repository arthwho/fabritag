import hashlib
import hmac
import json
import os
import secrets
import threading
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

import database_manager as db


auth_bp = Blueprint('auth', __name__)

# In-memory session registry for backend API authentication.
_ACTIVE_SESSIONS = {}
_SESSION_LOCK = threading.Lock()
_SESSION_DURATION_HOURS = 12
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '').strip()


def _utcnow():
    """Retorna o horário atual em UTC com timezone.

    Usada para calcular expiração de sessões e comparar datas de forma
    consistente no backend.
    """
    return datetime.now(timezone.utc)


def _hash_password(password):
    """Gera um hash PBKDF2 seguro para uma senha.

    Parâmetros:
        password: senha em texto puro, com no mínimo 6 caracteres.

    Retorna uma string com algoritmo, iterações, salt e digest para armazenar.
    """
    if not isinstance(password, str) or len(password) < 6:
        raise ValueError('Password must have at least 6 characters')

    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 120000)
    return f"pbkdf2_sha256$120000${salt}${digest.hex()}"


def _verify_password(password, password_hash):
    """Compara uma senha em texto puro com um hash armazenado.

    Parâmetros:
        password: senha enviada pelo usuário.
        password_hash: hash no formato produzido por _hash_password().

    Retorna True quando a senha confere e False para formato inválido ou erro.
    """
    try:
        algorithm, iterations_raw, salt, digest_hex = str(password_hash).split('$', 3)
        if algorithm != 'pbkdf2_sha256':
            return False
        iterations = int(iterations_raw)
    except Exception:
        return False

    digest = hashlib.pbkdf2_hmac(
        'sha256',
        str(password or '').encode('utf-8'),
        salt.encode('utf-8'),
        iterations,
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def _cleanup_expired_sessions():
    """Remove sessões expiradas do registro em memória.

    Usa _SESSION_LOCK para proteger o dicionário compartilhado entre requisições.
    """
    now = _utcnow()
    with _SESSION_LOCK:
        expired = [token for token, data in _ACTIVE_SESSIONS.items() if data['expires_at'] <= now]
        for token in expired:
            _ACTIVE_SESSIONS.pop(token, None)


def _build_user_payload(row):
    """Converte uma linha SQL de usuário no payload público da API.

    Parâmetros:
        row: tupla contendo id, nome, foto, email, cliente_id e cliente_nome.
    """
    return {
        'id': row[0],
        'nome_completo': row[1],
        'foto_perfil_url': row[2],
        'email': row[3],
        'cliente_id': row[4],
        'cliente_nome': row[5],
    }


def _extract_token():
    """Extrai o token de sessão da requisição Flask atual.

    Procura primeiro no header Authorization como Bearer token e, se ausente,
    usa X-Session-Token.
    """
    auth_header = request.headers.get('Authorization', '').strip()
    if auth_header.lower().startswith('bearer '):
        return auth_header[7:].strip()

    return request.headers.get('X-Session-Token', '').strip()


def _current_session_user(require_auth=True):
    """Valida a sessão da requisição atual.

    Parâmetros:
        require_auth: quando True, retorna resposta 401 se não houver sessão.

    Retorna uma tupla (session_user, error), em que error é uma resposta Flask
    pronta quando a autenticação falha.
    """
    _cleanup_expired_sessions()
    token = _extract_token()
    if not token:
        if require_auth:
            return None, (jsonify({'error': 'Authentication required'}), 401)
        return None, None

    with _SESSION_LOCK:
        session_data = _ACTIVE_SESSIONS.get(token)

    if not session_data:
        if require_auth:
            return None, (jsonify({'error': 'Invalid or expired session'}), 401)
        return None, None

    return {
        'token': token,
        'user_id': session_data['user_id'],
        'email': session_data['email'],
        'expires_at': session_data['expires_at'],
    }, None


def _ensure_cliente_exists(cur, cliente_id):
    """Valida se um cliente existe quando um id foi informado.

    Parâmetros:
        cur: cursor PostgreSQL da transação atual.
        cliente_id: id opcional do cliente.
    """
    if cliente_id is None:
        return

    cur.execute('SELECT 1 FROM CLIENTE WHERE id = %s', (cliente_id,))
    if not cur.fetchone():
        raise ValueError('Cliente not found')


def _only_digits(value):
    """Remove todos os caracteres não numéricos de um valor.

    Parâmetros:
        value: CPF/CNPJ ou qualquer texto a normalizar.
    """
    return ''.join(char for char in str(value or '') if char.isdigit())


def _is_repeated_digits(value):
    """Verifica se todos os dígitos de uma string são iguais.

    Usada para rejeitar CPF/CNPJ como 00000000000 ou 11111111111111.
    """
    return len(value) > 0 and all(char == value[0] for char in value)


def _validate_cpf(digits):
    """Valida um CPF já normalizado para apenas dígitos.

    Parâmetros:
        digits: string com 11 dígitos.

    Calcula os dois dígitos verificadores e retorna True quando o CPF é válido.
    """
    if len(digits) != 11 or _is_repeated_digits(digits):
        return False

    def calc_digit(base, factor):
        """Calcula um dígito verificador de CPF.

        Parâmetros:
            base: dígitos usados no cálculo.
            factor: multiplicador inicial decrementado a cada posição.
        """
        total = 0
        for char in base:
            total += int(char) * factor
            factor -= 1
        mod = total % 11
        return 0 if mod < 2 else 11 - mod

    first = calc_digit(digits[:9], 10)
    second = calc_digit(digits[:9] + str(first), 11)
    return digits == f"{digits[:9]}{first}{second}"


def _validate_cnpj(digits):
    """Valida um CNPJ já normalizado para apenas dígitos.

    Parâmetros:
        digits: string com 14 dígitos.

    Calcula os dois dígitos verificadores usando os pesos oficiais.
    """
    if len(digits) != 14 or _is_repeated_digits(digits):
        return False

    def calc_digit(base, factors):
        """Calcula um dígito verificador de CNPJ.

        Parâmetros:
            base: sequência base de dígitos.
            factors: lista de pesos aplicada por posição.
        """
        total = 0
        for idx, char in enumerate(base):
            total += int(char) * factors[idx]
        mod = total % 11
        return 0 if mod < 2 else 11 - mod

    first = calc_digit(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second = calc_digit(digits[:12] + str(first), [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return digits == f"{digits[:12]}{first}{second}"


def _normalize_validate_cpf_cnpj(raw_value):
    """Normaliza e valida CPF ou CNPJ.

    Parâmetros:
        raw_value: documento informado com ou sem pontuação.

    Retorna somente os dígitos válidos ou lança ValueError com mensagem de API.
    """
    digits = _only_digits(raw_value)
    if not digits:
        raise ValueError('CPF/CNPJ é obrigatório para criar cliente.')
    if len(digits) not in (11, 14):
        raise ValueError('Informe CPF (11 dígitos) ou CNPJ (14 dígitos) válido.')

    is_valid = _validate_cpf(digits) if len(digits) == 11 else _validate_cnpj(digits)
    if not is_valid:
        raise ValueError('CPF/CNPJ inválido. Verifique os dígitos informados.')

    return digits


def _create_cliente_for_usuario(cur, cpf_cnpj, fallback_nome):
    """Cria um cliente durante o cadastro de usuário.

    Parâmetros:
        cur: cursor PostgreSQL da transação atual.
        cpf_cnpj: documento do novo cliente.
        fallback_nome: nome usado quando não há razão social específica.

    Retorna o id do cliente criado.
    """
    normalized_cpf_cnpj = _normalize_validate_cpf_cnpj(cpf_cnpj)
    normalized_nome = (fallback_nome or '').strip() or 'Cliente sem nome'

    cur.execute(
        'INSERT INTO CLIENTE (cpf_cnpj, nome_razao_social) VALUES (%s, %s) RETURNING id',
        (normalized_cpf_cnpj, normalized_nome),
    )
    row = cur.fetchone()
    return row[0]


def _create_session_for_user(user_id, email):
    """Cria uma sessão em memória para um usuário autenticado.

    Parâmetros:
        user_id: id do usuário.
        email: email usado na sessão.

    Retorna o token gerado e a data/hora de expiração.
    """
    token = secrets.token_urlsafe(48)
    expires_at = _utcnow() + timedelta(hours=_SESSION_DURATION_HOURS)
    with _SESSION_LOCK:
        _ACTIVE_SESSIONS[token] = {
            'user_id': user_id,
            'email': email,
            'expires_at': expires_at,
        }
    return token, expires_at


def _verify_google_id_token(id_token):
    """Valida um Google ID token pelo endpoint tokeninfo.

    Parâmetros:
        id_token: token recebido do login Google no frontend.

    Retorna email, nome e foto normalizados quando o token é válido.
    """
    if not id_token:
        raise ValueError('Missing required field: id_token')

    query = urllib_parse.urlencode({'id_token': id_token})
    endpoint = f'https://oauth2.googleapis.com/tokeninfo?{query}'

    try:
        with urllib_request.urlopen(endpoint, timeout=8) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except urllib_error.HTTPError as exc:
        raise ValueError('Invalid Google token') from exc
    except Exception as exc:
        raise ValueError('Could not verify Google token') from exc

    aud = str(payload.get('aud') or '')
    email = str(payload.get('email') or '').strip().lower()
    email_verified = str(payload.get('email_verified') or '').lower() in ('true', '1')
    name = str(payload.get('name') or '').strip()
    picture = str(payload.get('picture') or '').strip()

    if not email or not email_verified:
        raise ValueError('Google account email is not verified')

    if GOOGLE_CLIENT_ID and aud != GOOGLE_CLIENT_ID:
        raise ValueError('Google token audience mismatch')

    return {
        'email': email,
        'nome_completo': name or email.split('@')[0],
        'foto_perfil_url': picture or None,
    }


def init_auth_schema():
    """Prepara colunas de autenticação e garante o usuário administrador.

    Deve ser chamada na inicialização do backend para adicionar colunas faltantes
    em USUARIO e criar/atualizar o admin padrão quando necessário.
    """
    conn = db.get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS nome_completo VARCHAR(150)')
        cur.execute('ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS foto_perfil_url TEXT')
        cur.execute('ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS senha_hash VARCHAR(255)')

        cur.execute('SELECT id, senha_hash FROM USUARIO WHERE email = %s LIMIT 1', ('admin@fabritag.com',))
        admin_row = cur.fetchone()
        default_password_hash = _hash_password('admin123')

        if admin_row:
            if not admin_row[1]:
                cur.execute('UPDATE USUARIO SET senha_hash = %s WHERE id = %s', (default_password_hash, admin_row[0]))
        else:
            cur.execute('SELECT id FROM CLIENTE ORDER BY id ASC LIMIT 1')
            cliente_row = cur.fetchone()
            cliente_id = cliente_row[0] if cliente_row else None
            cur.execute(
                'INSERT INTO USUARIO (nome_completo, email, cliente_id, senha_hash) VALUES (%s, %s, %s, %s)',
                ('Administrador', 'admin@fabritag.com', cliente_id, default_password_hash),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        db.release_db_connection(conn)


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Autentica usuário por email e senha.

    Espera JSON com email e password. Retorna token, expiração e dados do
    usuário quando as credenciais conferem.
    """
    payload = request.json or {}
    email = str(payload.get('email') or '').strip().lower()
    password = str(payload.get('password') or '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    conn = db.get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'SELECT u.id, u.nome_completo, u.foto_perfil_url, u.email, u.senha_hash, u.cliente_id, COALESCE(c.nome_razao_social, \'-\') '
            'FROM USUARIO u '
            'LEFT JOIN CLIENTE c ON c.id = u.cliente_id '
            'WHERE LOWER(u.email) = %s LIMIT 1',
            (email,),
        )
        row = cur.fetchone()
        if not row or not row[4] or not _verify_password(password, row[4]):
            return jsonify({'error': 'Invalid credentials'}), 401

        token, expires_at = _create_session_for_user(row[0], row[3])

        return jsonify(
            {
                'token': token,
                'expires_at': expires_at.isoformat(),
                'user': {
                    'id': row[0],
                    'nome_completo': row[1],
                    'foto_perfil_url': row[2],
                    'email': row[3],
                    'cliente_id': row[5],
                    'cliente_nome': row[6],
                },
            }
        )
    finally:
        cur.close()
        db.release_db_connection(conn)


@auth_bp.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Autentica ou cria usuário a partir de um Google ID token.

    Espera JSON com id_token. Valida o token, atualiza dados de perfil quando
    necessário e retorna uma sessão da API.
    """
    payload = request.json or {}
    id_token = str(payload.get('id_token') or '').strip()

    try:
        google_data = _verify_google_id_token(id_token)
    except ValueError as error_message:
        return jsonify({'error': str(error_message)}), 400

    conn = db.get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'SELECT id, nome_completo, foto_perfil_url, email, cliente_id FROM USUARIO WHERE LOWER(email) = %s LIMIT 1',
            (google_data['email'],),
        )
        existing_user = cur.fetchone()

        if existing_user:
            user_id = existing_user[0]
            nome_completo = existing_user[1] or google_data['nome_completo']
            foto_perfil_url = google_data['foto_perfil_url'] or existing_user[2]

            if not existing_user[1] and google_data['nome_completo']:
                cur.execute('UPDATE USUARIO SET nome_completo = %s WHERE id = %s', (google_data['nome_completo'], user_id))

            if google_data['foto_perfil_url'] and google_data['foto_perfil_url'] != existing_user[2]:
                cur.execute('UPDATE USUARIO SET foto_perfil_url = %s WHERE id = %s', (google_data['foto_perfil_url'], user_id))

            cur.execute(
                'SELECT u.id, u.nome_completo, u.foto_perfil_url, u.email, u.cliente_id, COALESCE(c.nome_razao_social, \'-\') '
                'FROM USUARIO u '
                'LEFT JOIN CLIENTE c ON c.id = u.cliente_id '
                'WHERE u.id = %s',
                (user_id,),
            )
            user_row = cur.fetchone()
        else:
            generated_password_hash = _hash_password(secrets.token_urlsafe(24))
            cur.execute(
                'INSERT INTO USUARIO (nome_completo, foto_perfil_url, email, cliente_id, senha_hash) '
                'VALUES (%s, %s, %s, %s, %s) '
                'RETURNING id',
                (
                    google_data['nome_completo'],
                    google_data['foto_perfil_url'],
                    google_data['email'],
                    None,
                    generated_password_hash,
                ),
            )
            user_id = cur.fetchone()[0]

            cur.execute(
                'SELECT u.id, u.nome_completo, u.foto_perfil_url, u.email, u.cliente_id, COALESCE(c.nome_razao_social, \'-\') '
                'FROM USUARIO u '
                'LEFT JOIN CLIENTE c ON c.id = u.cliente_id '
                'WHERE u.id = %s',
                (user_id,),
            )
            user_row = cur.fetchone()

        token, expires_at = _create_session_for_user(user_row[0], user_row[3])
        conn.commit()

        return jsonify(
            {
                'token': token,
                'expires_at': expires_at.isoformat(),
                'user': _build_user_payload(user_row),
            }
        )
    except Exception as exc:
        conn.rollback()
        message = str(exc).lower()
        if 'duplicate key' in message and 'email' in message:
            return jsonify({'error': 'Email already in use'}), 409
        return jsonify({'error': 'Não foi possível autenticar com Google no momento.'}), 500
    finally:
        cur.close()
        db.release_db_connection(conn)


@auth_bp.route('/api/auth/google-config', methods=['GET'])
def google_config():
    """Expõe o GOOGLE_CLIENT_ID configurado para o frontend.

    O retorno permite ao cliente inicializar o login Google com o client id
    usado pelo backend na validação.
    """
    return jsonify({'client_id': GOOGLE_CLIENT_ID})


@auth_bp.route('/api/auth/session', methods=['GET'])
def get_session():
    """Retorna os dados da sessão autenticada atual.

    Usa o token enviado nos headers, valida a sessão em memória e busca o
    usuário atualizado no banco.
    """
    session_user, error = _current_session_user(require_auth=True)
    if error:
        return error

    conn = db.get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'SELECT u.id, u.nome_completo, u.foto_perfil_url, u.email, u.cliente_id, COALESCE(c.nome_razao_social, \'-\') '
            'FROM USUARIO u '
            'LEFT JOIN CLIENTE c ON c.id = u.cliente_id '
            'WHERE u.id = %s',
            (session_user['user_id'],),
        )
        row = cur.fetchone()
        if not row:
            with _SESSION_LOCK:
                _ACTIVE_SESSIONS.pop(session_user['token'], None)
            return jsonify({'error': 'Session user not found'}), 401

        return jsonify(
            {
                'user': _build_user_payload(row),
                'expires_at': session_user['expires_at'].isoformat(),
            }
        )
    finally:
        cur.close()
        db.release_db_connection(conn)


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Encerra a sessão atual.

    Remove o token do registro em memória quando ele existe e sempre retorna
    sucesso para permitir logout idempotente.
    """
    session_user, _ = _current_session_user(require_auth=False)
    if session_user:
        with _SESSION_LOCK:
            _ACTIVE_SESSIONS.pop(session_user['token'], None)

    return jsonify({'success': True})


@auth_bp.route('/api/usuarios', methods=['GET'])
def list_usuarios():
    """Lista usuários cadastrados.

    Requer sessão autenticada e retorna os usuários com cliente associado e
    indicador de existência de senha.
    """
    _, error = _current_session_user(require_auth=True)
    if error:
        return error

    conn = db.get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'SELECT u.id, u.nome_completo, u.email, u.cliente_id, COALESCE(c.nome_razao_social, \'-\'), '
            'CASE WHEN u.senha_hash IS NOT NULL AND LENGTH(TRIM(u.senha_hash)) > 0 THEN TRUE ELSE FALSE END '
            'FROM USUARIO u '
            'LEFT JOIN CLIENTE c ON c.id = u.cliente_id '
            'ORDER BY u.id'
        )
        rows = cur.fetchall()
        return jsonify(
            [
                {
                    'id': row[0],
                    'nome_completo': row[1],
                    'email': row[2],
                    'cliente_id': row[3],
                    'cliente_nome': row[4],
                    'has_password': row[5],
                }
                for row in rows
            ]
        )
    finally:
        cur.close()
        db.release_db_connection(conn)


@auth_bp.route('/api/usuarios', methods=['POST'])
def create_usuario():
    """Cria um usuário administrativo via API autenticada.

    Espera JSON com nome_completo, email, password e opcionalmente cliente_id
    ou dados para criar cliente junto ao usuário.
    """
    _, error = _current_session_user(require_auth=True)
    if error:
        return error

    payload = request.json or {}
    nome_completo = str(payload.get('nome_completo') or '').strip()
    email = str(payload.get('email') or '').strip().lower()
    password = str(payload.get('password') or '')
    create_cliente = bool(payload.get('create_cliente'))
    cliente_cpf_cnpj = payload.get('cliente_cpf_cnpj')
    cliente_id_raw = payload.get('cliente_id')
    cliente_id = None if cliente_id_raw in ('', None) else cliente_id_raw

    if not nome_completo:
        return jsonify({'error': 'Missing required field: nome_completo'}), 400

    if not email:
        return jsonify({'error': 'Missing required field: email'}), 400

    if not password:
        return jsonify({'error': 'Missing required field: password'}), 400

    try:
        password_hash = _hash_password(password)
    except ValueError as error_message:
        return jsonify({'error': str(error_message)}), 400

    try:
        if cliente_id is not None:
            cliente_id = int(cliente_id)
            if cliente_id <= 0:
                raise ValueError('Invalid field: cliente_id')
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid field: cliente_id'}), 400

    if create_cliente and cliente_id is not None:
        return jsonify({'error': 'Não é permitido criar cliente quando já existe cliente associado.'}), 400

    conn = db.get_db_connection()
    cur = conn.cursor()
    try:
        if create_cliente:
            fallback_nome = nome_completo
            cliente_id = _create_cliente_for_usuario(cur, cliente_cpf_cnpj, fallback_nome)

        _ensure_cliente_exists(cur, cliente_id)

        cur.execute(
            'INSERT INTO USUARIO (nome_completo, email, cliente_id, senha_hash) '
            'VALUES (%s, %s, %s, %s) '
            'RETURNING id, nome_completo, email, cliente_id',
            (nome_completo, email, cliente_id, password_hash),
        )
        row = cur.fetchone()
        conn.commit()
        return jsonify({'id': row[0], 'nome_completo': row[1], 'email': row[2], 'cliente_id': row[3]}), 201
    except Exception as exc:
        conn.rollback()
        if 'duplicate key' in str(exc).lower() and 'email' in str(exc).lower():
            return jsonify({'error': 'Email already in use'}), 409
        if 'duplicate key' in str(exc).lower() and 'cpf_cnpj' in str(exc).lower():
            return jsonify({'error': 'CPF/CNPJ já cadastrado para outro cliente'}), 409
        if isinstance(exc, ValueError):
            return jsonify({'error': str(exc)}), 404
        raise
    finally:
        cur.close()
        db.release_db_connection(conn)


@auth_bp.route('/api/usuarios/<int:usuario_id>', methods=['PUT'])
def update_usuario(usuario_id):
    """Atualiza um usuário existente.

    Parâmetros:
        usuario_id: id recebido na rota.

    Permite alterar nome, email, cliente e opcionalmente senha; se o usuário
    editado for a sessão atual, sincroniza o email no registro em memória.
    """
    session_user, error = _current_session_user(require_auth=True)
    if error:
        return error

    payload = request.json or {}
    nome_completo = str(payload.get('nome_completo') or '').strip()
    email = str(payload.get('email') or '').strip().lower()
    password = str(payload.get('password') or '')
    create_cliente = bool(payload.get('create_cliente'))
    cliente_cpf_cnpj = payload.get('cliente_cpf_cnpj')
    cliente_id_raw = payload.get('cliente_id')

    if not nome_completo:
        return jsonify({'error': 'Missing required field: nome_completo'}), 400

    if not email:
        return jsonify({'error': 'Missing required field: email'}), 400

    cliente_id = None
    if cliente_id_raw not in ('', None):
        try:
            cliente_id = int(cliente_id_raw)
            if cliente_id <= 0:
                raise ValueError('Invalid field: cliente_id')
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid field: cliente_id'}), 400

    if create_cliente and cliente_id is not None:
        return jsonify({'error': 'Não é permitido criar cliente quando já existe cliente associado.'}), 400

    password_hash = None
    if password:
        try:
            password_hash = _hash_password(password)
        except ValueError as error_message:
            return jsonify({'error': str(error_message)}), 400

    conn = db.get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM USUARIO WHERE id = %s', (usuario_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Usuario not found'}), 404

        if create_cliente:
            fallback_nome = nome_completo
            cliente_id = _create_cliente_for_usuario(cur, cliente_cpf_cnpj, fallback_nome)

        _ensure_cliente_exists(cur, cliente_id)

        if password_hash:
            cur.execute(
                'UPDATE USUARIO SET nome_completo = %s, email = %s, cliente_id = %s, senha_hash = %s '
                'WHERE id = %s RETURNING id, nome_completo, email, cliente_id',
                (nome_completo, email, cliente_id, password_hash, usuario_id),
            )
        else:
            cur.execute(
                'UPDATE USUARIO SET nome_completo = %s, email = %s, cliente_id = %s '
                'WHERE id = %s RETURNING id, nome_completo, email, cliente_id',
                (nome_completo, email, cliente_id, usuario_id),
            )

        row = cur.fetchone()
        conn.commit()

        if session_user['user_id'] == usuario_id:
            with _SESSION_LOCK:
                token_data = _ACTIVE_SESSIONS.get(session_user['token'])
                if token_data:
                    token_data['email'] = row[2]

        return jsonify({'id': row[0], 'nome_completo': row[1], 'email': row[2], 'cliente_id': row[3]})
    except Exception as exc:
        conn.rollback()
        if 'duplicate key' in str(exc).lower() and 'email' in str(exc).lower():
            return jsonify({'error': 'Email already in use'}), 409
        if 'duplicate key' in str(exc).lower() and 'cpf_cnpj' in str(exc).lower():
            return jsonify({'error': 'CPF/CNPJ já cadastrado para outro cliente'}), 409
        if isinstance(exc, ValueError):
            return jsonify({'error': str(exc)}), 400
        raise
    finally:
        cur.close()
        db.release_db_connection(conn)


@auth_bp.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
def delete_usuario(usuario_id):
    """Exclui um usuário diferente do usuário logado.

    Parâmetros:
        usuario_id: id recebido na rota.

    Retorna conflito quando a requisição tenta remover a própria sessão.
    """
    session_user, error = _current_session_user(require_auth=True)
    if error:
        return error

    if session_user['user_id'] == usuario_id:
        return jsonify({'error': 'Cannot delete the current logged user'}), 409

    conn = db.get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM USUARIO WHERE id = %s RETURNING id', (usuario_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Usuario not found'}), 404

        conn.commit()
        return jsonify({'id': row[0]})
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        db.release_db_connection(conn)


@auth_bp.route('/api/auth/register', methods=['POST'])
def register_usuario():
    """Registra um novo usuário sem exigir sessão prévia.

    Espera JSON com nome_completo, email, password e vínculo de cliente opcional.
    Pode criar cliente durante o registro quando create_cliente estiver ativo.
    """
    payload = request.json or {}
    nome_completo = str(payload.get('nome_completo') or '').strip()
    email = str(payload.get('email') or '').strip().lower()
    password = str(payload.get('password') or '')
    create_cliente = bool(payload.get('create_cliente'))
    cliente_cpf_cnpj = payload.get('cliente_cpf_cnpj')
    cliente_id_raw = payload.get('cliente_id')
    cliente_id = None if cliente_id_raw in ('', None) else cliente_id_raw

    if not nome_completo:
        return jsonify({'error': 'Missing required field: nome_completo'}), 400

    if not email:
        return jsonify({'error': 'Missing required field: email'}), 400

    if not password:
        return jsonify({'error': 'Missing required field: password'}), 400

    try:
        password_hash = _hash_password(password)
    except ValueError as error_message:
        return jsonify({'error': str(error_message)}), 400

    try:
        if cliente_id is not None:
            cliente_id = int(cliente_id)
            if cliente_id <= 0:
                raise ValueError('Invalid field: cliente_id')
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid field: cliente_id'}), 400

    if create_cliente and cliente_id is not None:
        return jsonify({'error': 'Não é permitido criar cliente quando já existe cliente associado.'}), 400

    conn = db.get_db_connection()
    cur = conn.cursor()
    try:
        if create_cliente:
            fallback_nome = nome_completo
            cliente_id = _create_cliente_for_usuario(cur, cliente_cpf_cnpj, fallback_nome)

        _ensure_cliente_exists(cur, cliente_id)

        cur.execute(
            'INSERT INTO USUARIO (nome_completo, email, cliente_id, senha_hash) '
            'VALUES (%s, %s, %s, %s) '
            'RETURNING id, nome_completo, email, cliente_id',
            (nome_completo, email, cliente_id, password_hash),
        )
        row = cur.fetchone()
        conn.commit()
        return jsonify({'id': row[0], 'nome_completo': row[1], 'email': row[2], 'cliente_id': row[3]}), 201
    except Exception as exc:
        conn.rollback()
        if 'duplicate key' in str(exc).lower() and 'email' in str(exc).lower():
            return jsonify({'error': 'Email already in use'}), 409
        if 'duplicate key' in str(exc).lower() and 'cpf_cnpj' in str(exc).lower():
            return jsonify({'error': 'CPF/CNPJ já cadastrado para outro cliente'}), 409
        if isinstance(exc, ValueError):
            return jsonify({'error': str(exc)}), 400
        raise
    finally:
        cur.close()
        db.release_db_connection(conn)
