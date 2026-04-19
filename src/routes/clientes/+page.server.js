import { fail } from '@sveltejs/kit';

const CLIENTES_API_URL = 'http://127.0.0.1:5000/api/clientes';

function onlyDigits(value) {
    return String(value || '').replace(/\D/g, '');
}

function isRepeatedDigits(value) {
    return /^(\d)\1+$/.test(value);
}

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

async function getApiError(response, fallbackError) {
    const errorData = await response.json().catch(() => null);
    if (errorData?.error) return errorData.error;

    const errorText = await response.text().catch(() => '');
    return errorText || fallbackError;
}

/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
    try {
        const clientesRes = await fetch('http://127.0.0.1:5000/api/clientes');

        if (!clientesRes.ok) {
            const clientesText = await clientesRes.text();
            console.error('Failed to fetch clientes page data:', {
                clientesStatus: clientesRes.status,
                clientesText
            });

            return {
                clientes: [],
                error: 'Falha ao carregar os dados de clientes.'
            };
        }

        const clientesData = await clientesRes.json();

        return {
            clientes: clientesData || [],
            error: null
        };
    } catch (error) {
        console.error('Error fetching clientes page data:', error);
        return {
            clientes: [],
            error: 'Não foi possível conectar ao backend. Verifique se o servidor está rodando.'
        };
    }
}

/** @type {import('./$types').Actions} */
export const actions = {
    create: async ({ request, fetch }) => {
        const formData = await request.formData();
        const nome = String(formData.get('nome') || '').trim();
        const cpfCnpjRaw = String(formData.get('cpfCnpj') || '');

        let cpfCnpj = null;
        try {
            cpfCnpj = getValidatedCpfCnpjOrNull(cpfCnpjRaw);
        } catch (error) {
            return fail(400, {
                action: 'create',
                error: error instanceof Error ? error.message : 'CPF/CNPJ inválido.',
                fieldValues: { nome, cpfCnpj: cpfCnpjRaw }
            });
        }

        const response = await fetch(CLIENTES_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nome_razao_social: nome || null,
                cpf_cnpj: cpfCnpj
            })
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'create',
                error: await getApiError(response, 'Não foi possível criar o cliente.'),
                fieldValues: { nome, cpfCnpj: cpfCnpjRaw }
            });
        }

        return { success: true, action: 'create' };
    },

    update: async ({ request, fetch }) => {
        const formData = await request.formData();
        const clienteId = Number(formData.get('clienteId'));
        const nome = String(formData.get('nome') || '').trim();
        const cpfCnpjRaw = String(formData.get('cpfCnpj') || '');

        if (!Number.isInteger(clienteId) || clienteId <= 0) {
            return fail(400, {
                action: 'update',
                error: 'Cliente inválido para atualização.',
                fieldValues: { nome, cpfCnpj: cpfCnpjRaw }
            });
        }

        let cpfCnpj = null;
        try {
            cpfCnpj = getValidatedCpfCnpjOrNull(cpfCnpjRaw);
        } catch (error) {
            return fail(400, {
                action: 'update',
                error: error instanceof Error ? error.message : 'CPF/CNPJ inválido.',
                fieldValues: { nome, cpfCnpj: cpfCnpjRaw }
            });
        }

        const response = await fetch(`${CLIENTES_API_URL}/${clienteId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nome_razao_social: nome || null,
                cpf_cnpj: cpfCnpj
            })
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'update',
                error: await getApiError(response, 'Não foi possível atualizar o cliente.'),
                fieldValues: { nome, cpfCnpj: cpfCnpjRaw }
            });
        }

        return { success: true, action: 'update' };
    },

    delete: async ({ request, fetch }) => {
        const formData = await request.formData();
        const clienteId = Number(formData.get('clienteId'));

        if (!Number.isInteger(clienteId) || clienteId <= 0) {
            return fail(400, {
                action: 'delete',
                error: 'Cliente inválido para exclusão.'
            });
        }

        const response = await fetch(`${CLIENTES_API_URL}/${clienteId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'delete',
                error: await getApiError(response, 'Não foi possível excluir o cliente.'),
                clienteId
            });
        }

        return { success: true, action: 'delete', clienteId };
    }
};
