const BACKEND_URL = 'http://127.0.0.1:5000';

/**
 * Busca o status ao vivo de todos os dispositivos conhecidos pelo backend.
 *
 * @param {typeof fetch} fetchFn - Função fetch do SvelteKit.
 * @returns {Promise<Record<string, {status: string, ip_address: string}>>} Status por id.
 */
export async function getAllDispositivoStatuses(fetchFn) {
	try {
		const res = await fetchFn(`${BACKEND_URL}/api/dispositivos/status`);
		if (res.ok) return await res.json();
	} catch (e) {
		console.error('Error fetching dispositivo statuses:', e);
	}
	return {};
}

/**
 * Busca o status ao vivo de um dispositivo específico.
 *
 * @param {typeof fetch} fetchFn - Função fetch do SvelteKit.
 * @param {number|string} id - Identificador do dispositivo.
 * @returns {Promise<{status: string, ip_address: string}>} Status encontrado ou fallback offline.
 */
export async function getDispositivoStatus(fetchFn, id) {
	try {
		const res = await fetchFn(`${BACKEND_URL}/api/dispositivos/status/${id}`);
		if (res.ok) return await res.json();
	} catch (e) {
		console.error(`Error fetching status for dispositivo ${id}:`, e);
	}
	return { status: 'Offline', ip_address: 'N/A' };
}
