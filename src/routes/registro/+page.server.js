import { fail, redirect } from '@sveltejs/kit';
import { setAuthCookie } from '$lib/server/auth';

const GOOGLE_CONFIG_API_URL = 'http://127.0.0.1:5000/api/auth/google-config';
const GOOGLE_AUTH_API_URL = 'http://127.0.0.1:5000/api/auth/google';
const REGISTER_API_URL = 'http://127.0.0.1:5000/api/auth/register';

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

/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
    let googleClientId = (process.env.PUBLIC_GOOGLE_CLIENT_ID || '').trim();

    try {
        const response = await fetch(GOOGLE_CONFIG_API_URL);
        if (response.ok) {
            const data = await response.json().catch(() => null);
            if (data?.client_id) {
                googleClientId = String(data.client_id).trim();
            }
        }
    } catch {
        // Keep env fallback when backend is temporarily unavailable.
    }

    return {
        error: null,
        googleClientId
    };
}

/** @type {import('./$types').Actions} */
export const actions = {
    register: async ({ request, fetch }) => {
        const formData = await request.formData();
        const nomeCompleto = String(formData.get('nomeCompleto') || '').trim();
        const email = String(formData.get('email') || '').trim().toLowerCase();
        const password = String(formData.get('password') || '');
        const isAlsoCliente = String(formData.get('isAlsoCliente') || '') === 'on';
        const cpfCnpjRaw = String(formData.get('cpfCnpj') || '');

        if (!nomeCompleto) {
            return fail(400, {
                error: 'Informe nome e sobrenome.',
                fieldValues: { nomeCompleto, email, isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        if (!email || !password) {
            return fail(400, {
                error: 'Informe email e senha para registrar.',
                fieldValues: { nomeCompleto, email, isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        let cpfCnpj = null;
        if (isAlsoCliente) {
            try {
                cpfCnpj = getValidatedCpfCnpjOrNull(cpfCnpjRaw);
            } catch (error) {
                return fail(400, {
                    error: error instanceof Error ? error.message : 'CPF/CNPJ inválido.',
                    fieldValues: { nomeCompleto, email, isAlsoCliente, cpfCnpj: cpfCnpjRaw }
                });
            }

            if (!cpfCnpj) {
                return fail(400, {
                    error: 'Informe CPF/CNPJ para criar cliente.',
                    fieldValues: { nomeCompleto, email, isAlsoCliente, cpfCnpj: cpfCnpjRaw }
                });
            }
        }

        const response = await fetch(REGISTER_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                nome_completo: nomeCompleto,
                password,
                create_cliente: isAlsoCliente,
                cliente_cpf_cnpj: cpfCnpj
            })
        });

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            return fail(response.status || 400, {
                error: data?.error || 'Não foi possível concluir o registro.',
                fieldValues: { nomeCompleto, email, isAlsoCliente, cpfCnpj: cpfCnpjRaw }
            });
        }

        throw redirect(303, '/login');
    },

    google: async ({ request, fetch, cookies }) => {
        const formData = await request.formData();
        const idToken = String(formData.get('idToken') || '').trim();

        if (!idToken) {
            return fail(400, {
                error: 'Token do Google não informado.'
            });
        }

        const response = await fetch(GOOGLE_AUTH_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id_token: idToken })
        });

        const data = await response.json().catch(() => null);
        if (!response.ok || !data?.token) {
            return fail(response.status || 401, {
                error: data?.error || 'Não foi possível autenticar com Google.'
            });
        }

        setAuthCookie(cookies, data.token);
        throw redirect(303, '/dashboard');
    }
};
