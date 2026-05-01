import { redirect } from '@sveltejs/kit';
import { clearAuthCookie, logoutBackendSession } from '$lib/server/auth';

/**
 * Encerra a sessão por requisição GET e redireciona para login.
 *
 * @param {import('@sveltejs/kit').RequestEvent} event - Evento da requisição.
 * @returns {Promise<never>} Sempre lança redirect.
 * @type {import('./$types').RequestHandler}
 */
export async function GET(event) {
    await logoutBackendSession(event);
    clearAuthCookie(event.cookies);
    throw redirect(303, '/login');
}

/**
 * Encerra a sessão por requisição POST e redireciona para login.
 *
 * @param {import('@sveltejs/kit').RequestEvent} event - Evento da requisição.
 * @returns {Promise<never>} Sempre lança redirect.
 * @type {import('./$types').RequestHandler}
 */
export async function POST(event) {
    await logoutBackendSession(event);
    clearAuthCookie(event.cookies);
    throw redirect(303, '/login');
}
