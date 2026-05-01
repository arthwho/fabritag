import { fail, redirect } from '@sveltejs/kit';
import { setAuthCookie } from '$lib/server/auth';

const LOGIN_API_URL = 'http://127.0.0.1:5000/api/auth/login';
const GOOGLE_AUTH_API_URL = 'http://127.0.0.1:5000/api/auth/google';
const GOOGLE_CONFIG_API_URL = 'http://127.0.0.1:5000/api/auth/google-config';

/**
 * Carrega a configuração do Google Login para a página.
 *
 * @param {object} input - Contexto da rota.
 * @param {typeof fetch} input.fetch - Fetch server-side do SvelteKit.
 * @returns {Promise<{error: null, googleClientId: string}>} Configuração inicial.
 * @type {import('./$types').PageServerLoad}
 */
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
    login: async ({ request, fetch, cookies }) => {
        const formData = await request.formData();
        const email = String(formData.get('email') || '').trim().toLowerCase();
        const password = String(formData.get('password') || '');

        if (!email || !password) {
            return fail(400, {
                error: 'Informe email e senha para entrar.',
                fieldValues: {
                    email
                }
            });
        }

        const response = await fetch(LOGIN_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json().catch(() => null);

        if (!response.ok || !data?.token) {
            return fail(response.status || 401, {
                error: data?.error || 'Não foi possível autenticar com as credenciais informadas.',
                fieldValues: {
                    email
                }
            });
        }

        setAuthCookie(cookies, data.token);
        throw redirect(303, '/dashboard');
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
