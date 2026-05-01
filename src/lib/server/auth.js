const AUTH_API_BASE = 'http://127.0.0.1:5000/api/auth';
export const AUTH_COOKIE_NAME = 'fabritag_auth_token';

/**
 * Grava o token de autenticação no cookie HTTP-only da aplicação.
 *
 * @param {import('@sveltejs/kit').Cookies} cookies - Gerenciador de cookies do SvelteKit.
 * @param {string} token - Token de sessão retornado pelo backend Flask.
 */
export function setAuthCookie(cookies, token) {
    cookies.set(AUTH_COOKIE_NAME, token, {
        path: '/',
        httpOnly: true,
        sameSite: 'lax',
        secure: false,
        maxAge: 60 * 60 * 12
    });
}

/**
 * Remove o cookie de autenticação do navegador.
 *
 * @param {import('@sveltejs/kit').Cookies} cookies - Gerenciador de cookies do SvelteKit.
 */
export function clearAuthCookie(cookies) {
    cookies.delete(AUTH_COOKIE_NAME, {
        path: '/'
    });
}

/**
 * Lê o token de autenticação salvo no evento atual.
 *
 * @param {import('@sveltejs/kit').RequestEvent} event - Evento server-side do SvelteKit.
 * @returns {string} Token salvo ou string vazia.
 */
export function getAuthToken(event) {
    return event.cookies.get(AUTH_COOKIE_NAME) || '';
}

/**
 * Monta headers de autenticação para chamadas ao backend.
 *
 * @param {string} token - Token de sessão.
 * @returns {Record<string, string>} Headers com Bearer token ou objeto vazio.
 */
function getAuthHeaders(token) {
    if (!token) return {};
    return {
        Authorization: `Bearer ${token}`
    };
}

/**
 * Busca o usuário da sessão atual no backend Flask.
 *
 * @param {import('@sveltejs/kit').RequestEvent} event - Evento com fetch e cookies.
 * @returns {Promise<object|null>} Dados públicos do usuário ou null quando inválido.
 */
export async function fetchCurrentUser(event) {
    const token = getAuthToken(event);
    if (!token) return null;

    const response = await event.fetch(`${AUTH_API_BASE}/session`, {
        headers: getAuthHeaders(token)
    });

    if (!response.ok) {
        return null;
    }

    const data = await response.json().catch(() => null);
    return data?.user || null;
}

/**
 * Encerra a sessão também no backend Flask.
 *
 * @param {import('@sveltejs/kit').RequestEvent} event - Evento com fetch e cookies.
 * @returns {Promise<void>}
 */
export async function logoutBackendSession(event) {
    const token = getAuthToken(event);
    if (!token) return;

    await event.fetch(`${AUTH_API_BASE}/logout`, {
        method: 'POST',
        headers: getAuthHeaders(token)
    });
}
