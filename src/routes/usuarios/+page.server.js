import { fail } from '@sveltejs/kit';
import { getAuthToken } from '$lib/server/auth';

const USUARIOS_API_URL = 'http://127.0.0.1:5000/api/usuarios';
const CLIENTES_API_URL = 'http://127.0.0.1:5000/api/clientes';

/**
 * Monta headers de autenticação para chamadas protegidas.
 *
 * @param {string} token - Token salvo no cookie.
 * @returns {Record<string, string>} Headers com Authorization ou objeto vazio.
 */
function authHeaders(token) {
    if (!token) return {};
    return {
        Authorization: `Bearer ${token}`
    };
}

/**
 * Converte valores de formulário em texto aparado.
 *
 * @param {unknown} value - Valor bruto.
 * @returns {string} Texto normalizado.
 */
function toStringValue(value) {
    return String(value ?? '').trim();
}

/**
 * Lê um inteiro positivo opcional.
 *
 * @param {unknown} rawValue - Valor bruto do formulário.
 * @returns {number|null} Inteiro positivo ou null quando vazio.
 */
function parseOptionalPositiveInteger(rawValue) {
    const value = toStringValue(rawValue);
    if (!value) return null;

    const numberValue = Number(value);
    if (!Number.isInteger(numberValue) || numberValue < 1) {
        throw new Error('Informe um cliente válido.');
    }

    return numberValue;
}

/**
 * Remove caracteres não numéricos de um valor.
 *
 * @param {unknown} value - CPF/CNPJ com ou sem pontuação.
 * @returns {string} Apenas dígitos.
 */
function onlyDigits(value) {
    return String(value || '').replace(/\D/g, '');
}

/**
 * Verifica se todos os dígitos são iguais.
 *
 * @param {string} value - Documento normalizado.
 * @returns {boolean} True quando todos os dígitos repetem.
 */
function isRepeatedDigits(value) {
    return /^(\d)\1+$/.test(value);
}

/**
 * Valida CPF sem pontuação.
 *
 * @param {string} digits - String com 11 dígitos.
 * @returns {boolean} True quando válido.
 */
function validateCpf(digits) {
    if (digits.length !== 11 || isRepeatedDigits(digits)) return false;

    const calcDigit = (base, factor) => {
        let total = 0;
        for (const char of base) {
            total += Number(char) * factor;
            factor -= 1;
        }
        const mod = total % 11;
        return mod < 2 ? 0 : 11 - mod;
    };

    const first = calcDigit(digits.slice(0, 9), 10);
    const second = calcDigit(digits.slice(0, 9) + String(first), 11);

    return digits === `${digits.slice(0, 9)}${first}${second}`;
}

/**
 * Valida CNPJ sem pontuação.
 *
 * @param {string} digits - String com 14 dígitos.
 * @returns {boolean} True quando válido.
 */
function validateCnpj(digits) {
    if (digits.length !== 14 || isRepeatedDigits(digits)) return false;

    const calcDigit = (base, factors) => {
        let total = 0;
        for (let i = 0; i < base.length; i += 1) {
            total += Number(base[i]) * factors[i];
        }
        const mod = total % 11;
        return mod < 2 ? 0 : 11 - mod;
    };

    const first = calcDigit(digits.slice(0, 12), [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
    const second = calcDigit(
        digits.slice(0, 12) + String(first),
        [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    );

    return digits === `${digits.slice(0, 12)}${first}${second}`;
}

/**
 * Normaliza e valida CPF/CNPJ opcional.
 *
 * @param {unknown} rawValue - Valor bruto do formulário.
 * @returns {string|null} Documento sem pontuação ou null quando vazio.
 */
function getValidatedCpfCnpjOrNull(rawValue) {
    const digits = onlyDigits(rawValue);
    if (!digits) return null;
    if (digits.length !== 11 && digits.length !== 14) {
        throw new Error('Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido.');
    }

    const isValid = digits.length === 11 ? validateCpf(digits) : validateCnpj(digits);
    if (!isValid) {
        throw new Error('CPF/CNPJ inválido. Verifique os dígitos informados.');
    }

    return digits;
}

/**
 * Extrai a mensagem de erro retornada pela API.
 *
 * @param {Response} response - Resposta fetch.
 * @param {string} fallbackError - Mensagem padrão.
 * @returns {Promise<string>} Mensagem final.
 */
async function getApiError(response, fallbackError) {
    const errorData = await response.json().catch(() => null);
    if (errorData?.error) return errorData.error;

    const errorText = await response.text().catch(() => '');
    return errorText || fallbackError;
}

/**
 * Carrega usuários e clientes para a página administrativa.
 *
 * @param {import('@sveltejs/kit').RequestEvent} event - Evento com fetch e cookies.
 * @returns {Promise<object>} Dados da página.
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
    const token = getAuthToken(event);

    try {
        const [usuariosRes, clientesRes] = await Promise.all([
            event.fetch(USUARIOS_API_URL, { headers: authHeaders(token) }),
            event.fetch(CLIENTES_API_URL)
        ]);

        if (!usuariosRes.ok || !clientesRes.ok) {
            const usuariosText = !usuariosRes.ok ? await usuariosRes.text() : '';
            const clientesText = !clientesRes.ok ? await clientesRes.text() : '';
            console.error('Failed to fetch usuarios page data:', {
                usuariosStatus: usuariosRes.status,
                usuariosText,
                clientesStatus: clientesRes.status,
                clientesText
            });

            return {
                usuarios: [],
                clientes: [],
                error: 'Falha ao carregar os dados de usuários.'
            };
        }

        const usuariosData = await usuariosRes.json();
        const clientesData = await clientesRes.json();

        return {
            usuarios: usuariosData || [],
            clientes: clientesData || [],
            error: null
        };
    } catch (error) {
        console.error('Error fetching usuarios page data:', error);
        return {
            usuarios: [],
            clientes: [],
            error: 'Não foi possível conectar ao backend. Verifique se o servidor está rodando.'
        };
    }
}

/** @type {import('./$types').Actions} */
export const actions = {
    create: async (event) => {
        const token = getAuthToken(event);
        const formData = await event.request.formData();

        const email = toStringValue(formData.get('email')).toLowerCase();
        const nomeCompleto = toStringValue(formData.get('nomeCompleto'));
        const password = toStringValue(formData.get('password'));
        const isAlsoCliente = String(formData.get('isAlsoCliente') || '') === 'on';
        const cpfCnpjRaw = toStringValue(formData.get('cpfCnpj'));
        const clienteIdRaw = formData.get('clienteId');

        if (!email) {
            return fail(400, {
                action: 'create',
                error: 'Email é obrigatório.',
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        if (!nomeCompleto) {
            return fail(400, {
                action: 'create',
                error: 'Nome completo é obrigatório.',
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        if (!password) {
            return fail(400, {
                action: 'create',
                error: 'Senha é obrigatória para criar um usuário.',
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        let cpfCnpj = null;
        if (isAlsoCliente) {
            try {
                cpfCnpj = getValidatedCpfCnpjOrNull(cpfCnpjRaw);
            } catch (error) {
                return fail(400, {
                    action: 'create',
                    error: error instanceof Error ? error.message : 'CPF/CNPJ inválido.',
                    fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
                });
            }

            if (!cpfCnpj) {
                return fail(400, {
                    action: 'create',
                    error: 'Informe CPF/CNPJ para criar cliente.',
                    fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
                });
            }
        }

        let clienteId = null;
        try {
            clienteId = parseOptionalPositiveInteger(clienteIdRaw);
        } catch (error) {
            return fail(400, {
                action: 'create',
                error: error instanceof Error ? error.message : 'Cliente inválido.',
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        if (isAlsoCliente && clienteId !== null) {
            return fail(400, {
                action: 'create',
                error: 'Não é permitido marcar também será cliente quando já existe cliente associado.',
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        const response = await event.fetch(USUARIOS_API_URL, {
            method: 'POST',
            headers: {
                ...authHeaders(token),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                nome_completo: nomeCompleto,
                password,
                cliente_id: isAlsoCliente ? null : clienteId,
                create_cliente: isAlsoCliente,
                cliente_cpf_cnpj: cpfCnpj
            })
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'create',
                error: await getApiError(response, 'Não foi possível criar o usuário.'),
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        return { success: true, action: 'create' };
    },

    update: async (event) => {
        const token = getAuthToken(event);
        const formData = await event.request.formData();

        const usuarioId = Number(formData.get('usuarioId'));
        const email = toStringValue(formData.get('email')).toLowerCase();
        const nomeCompleto = toStringValue(formData.get('nomeCompleto'));
        const password = toStringValue(formData.get('password'));
        const isAlsoCliente = String(formData.get('isAlsoCliente') || '') === 'on';
        const cpfCnpjRaw = toStringValue(formData.get('cpfCnpj'));
        const clienteIdRaw = formData.get('clienteId');

        if (!Number.isInteger(usuarioId) || usuarioId <= 0) {
            return fail(400, {
                action: 'update',
                error: 'Usuário inválido para atualização.',
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        if (!email) {
            return fail(400, {
                action: 'update',
                error: 'Email é obrigatório.',
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        if (!nomeCompleto) {
            return fail(400, {
                action: 'update',
                error: 'Nome completo é obrigatório.',
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        let cpfCnpj = null;
        if (isAlsoCliente) {
            try {
                cpfCnpj = getValidatedCpfCnpjOrNull(cpfCnpjRaw);
            } catch (error) {
                return fail(400, {
                    action: 'update',
                    error: error instanceof Error ? error.message : 'CPF/CNPJ inválido.',
                    fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
                });
            }

            if (!cpfCnpj) {
                return fail(400, {
                    action: 'update',
                    error: 'Informe CPF/CNPJ para criar cliente.',
                    fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
                });
            }
        }

        let clienteId = null;
        try {
            clienteId = parseOptionalPositiveInteger(clienteIdRaw);
        } catch (error) {
            return fail(400, {
                action: 'update',
                error: error instanceof Error ? error.message : 'Cliente inválido.',
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        if (isAlsoCliente && clienteId !== null) {
            return fail(400, {
                action: 'update',
                error: 'Não é permitido marcar também será cliente quando já existe cliente associado.',
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        const payload = {
            email,
            nome_completo: nomeCompleto,
            cliente_id: isAlsoCliente ? null : clienteId,
            create_cliente: isAlsoCliente,
            cliente_cpf_cnpj: cpfCnpj
        };

        if (password) {
            payload.password = password;
        }

        const response = await event.fetch(`${USUARIOS_API_URL}/${usuarioId}`, {
            method: 'PUT',
            headers: {
                ...authHeaders(token),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'update',
                error: await getApiError(response, 'Não foi possível atualizar o usuário.'),
                fieldValues: { nomeCompleto, email, clienteId: toStringValue(clienteIdRaw), isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        return { success: true, action: 'update' };
    },

    delete: async (event) => {
        const token = getAuthToken(event);
        const formData = await event.request.formData();
        const usuarioId = Number(formData.get('usuarioId'));

        if (!Number.isInteger(usuarioId) || usuarioId <= 0) {
            return fail(400, {
                action: 'delete',
                error: 'Usuário inválido para exclusão.'
            });
        }

        const response = await event.fetch(`${USUARIOS_API_URL}/${usuarioId}`, {
            method: 'DELETE',
            headers: authHeaders(token)
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'delete',
                error: await getApiError(response, 'Não foi possível excluir o usuário.')
            });
        }

        return { success: true, action: 'delete' };
    }
};
