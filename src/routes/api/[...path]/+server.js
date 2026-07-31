import { backendUrl } from '$lib/server/backend-api';
import { AUTH_COOKIE_NAME } from '$lib/server/auth';

const BODYLESS_METHODS = new Set(['GET', 'HEAD']);
const HOP_BY_HOP_HEADERS = [
	'connection',
	'content-length',
	'host',
	'keep-alive',
	'proxy-authenticate',
	'proxy-authorization',
	'te',
	'trailer',
	'transfer-encoding',
	'upgrade'
];

/**
 * Encaminha chamadas same-origin do navegador para o backend privado.
 *
 * @param {import('./$types').RequestEvent} event Evento da rota SvelteKit.
 * @returns {Promise<Response>} Resposta fornecida pela API Flask.
 */
async function proxyBackendRequest({ request, params, url, fetch, cookies }) {
	const headers = new Headers(request.headers);
	for (const header of HOP_BY_HOP_HEADERS) {
		headers.delete(header);
	}

	const authToken = cookies.get(AUTH_COOKIE_NAME);
	if (authToken && !headers.has('authorization')) {
		headers.set('authorization', `Bearer ${authToken}`);
	}

	const path = params.path ? `/${params.path}` : '';
	const targetUrl = backendUrl(`/api${path}${url.search}`);
	const response = await fetch(targetUrl, {
		method: request.method,
		headers,
		body: BODYLESS_METHODS.has(request.method) ? undefined : await request.arrayBuffer(),
		redirect: 'manual'
	});

	const responseHeaders = new Headers(response.headers);
	for (const header of HOP_BY_HOP_HEADERS) {
		responseHeaders.delete(header);
	}

	return new Response(response.body, {
		status: response.status,
		statusText: response.statusText,
		headers: responseHeaders
	});
}

export const GET = proxyBackendRequest;
export const POST = proxyBackendRequest;
export const PUT = proxyBackendRequest;
export const PATCH = proxyBackendRequest;
export const DELETE = proxyBackendRequest;
export const OPTIONS = proxyBackendRequest;
