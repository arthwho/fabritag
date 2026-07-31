const API_BASE_PATH = '/api';

/**
 * Monta um caminho same-origin para a API publicada pelo frontend.
 *
 * No navegador, as chamadas passam pelo gateway do SvelteKit. O endereço
 * interno do backend fica restrito ao ambiente de execução do servidor.
 *
 * @param {string} path Caminho da API sem o prefixo /api.
 * @returns {string} Caminho relativo no mesmo domínio da aplicação.
 */
export function apiPath(path = '') {
	const normalizedPath = path && !path.startsWith('/') ? `/${path}` : path;
	return `${API_BASE_PATH}${normalizedPath}`;
}
