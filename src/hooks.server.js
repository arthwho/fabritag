import { redirect } from '@sveltejs/kit';
import { clearAuthCookie, fetchCurrentUser } from '$lib/server/auth';

/**
 * Verifica se uma rota pode ser acessada sem sessão autenticada.
 *
 * @param {string} pathname - Caminho da URL atual.
 * @returns {boolean} True para login e registro.
 */
function isPublicRoute(pathname) {
    return pathname.startsWith('/login') || pathname.startsWith('/registro');
}

/**
 * Intercepta todas as requisições SvelteKit para aplicar autenticação.
 *
 * @param {object} input - Objeto do hook do SvelteKit.
 * @param {import('@sveltejs/kit').RequestEvent} input.event - Evento da requisição.
 * @param {Function} input.resolve - Função que continua o processamento da rota.
 * @returns {Promise<Response>} Resposta da rota ou redirecionamento.
 * @type {import('@sveltejs/kit').Handle}
 */
export async function handle({ event, resolve }) {
    const { pathname } = event.url;
    const currentUser = await fetchCurrentUser(event);

    if (!currentUser) {
        clearAuthCookie(event.cookies);
    }

    event.locals.currentUser = currentUser;

    if (!currentUser && !isPublicRoute(pathname)) {
        throw redirect(303, '/login');
    }

    if (currentUser && (pathname === '/login' || pathname === '/registro')) {
        throw redirect(303, '/dashboard');
    }

    return resolve(event);
}
