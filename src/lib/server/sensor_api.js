const BACKEND_URL = 'http://127.0.0.1:5000';

/**
 * Fetches the live status of all sensors.
 * @param {typeof fetch} fetchFn - SvelteKit's fetch function.
 */
export async function getAllSensorStatuses(fetchFn) {
	try {
		const res = await fetchFn(`${BACKEND_URL}/api/sensors/status`);
		if (res.ok) return await res.json();
	} catch (e) {
		console.error('Error fetching sensor statuses:', e);
	}
	return {};
}

/**
 * Fetches the live status of a single sensor.
 * @param {typeof fetch} fetchFn 
 * @param {number|string} id 
 */
export async function getSensorStatus(fetchFn, id) {
	try {
		const res = await fetchFn(`${BACKEND_URL}/api/sensor/status/${id}`);
		if (res.ok) return await res.json();
	} catch (e) {
		console.error(`Error fetching status for sensor ${id}:`, e);
	}
	return { status: 'Offline', ip_address: 'N/A' };
}
