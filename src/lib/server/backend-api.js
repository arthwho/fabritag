import { env } from '$env/dynamic/private';

const DEFAULT_BACKEND_URL = 'http://127.0.0.1:5000';

/**
 * Monta a URL interna do backend Flask.
 *
 * BACKEND_URL deve apontar para o DNS privado do serviço em ambientes
 * containerizados. O fallback mantém o desenvolvimento local compatível.
 *
 * @param {string} path Caminho iniciado por /.
 * @returns {string} URL absoluta do backend.
 */
export function backendUrl(path = '') {
	const baseUrl = (env.BACKEND_URL || DEFAULT_BACKEND_URL).replace(/\/+$/, '');
	const normalizedPath = path && !path.startsWith('/') ? `/${path}` : path;
	return `${baseUrl}${normalizedPath}`;
}
