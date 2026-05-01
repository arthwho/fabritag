import { redirect } from '@sveltejs/kit';

/**
 * Redireciona a rota raiz para o dashboard.
 *
 * @returns {never} Sempre lança redirect do SvelteKit.
 */
export function load() {
	throw redirect(307, '/dashboard');
}
