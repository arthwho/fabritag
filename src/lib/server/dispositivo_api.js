const BACKEND_URL = 'http://127.0.0.1:5000';

/**
 * Fetches the live status of all dispositivos.
 * @param {typeof fetch} fetchFn - SvelteKit's fetch function.
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
 * Fetches the live status of a single dispositivo.
 * @param {typeof fetch} fetchFn 
 * @param {number|string} id 
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
