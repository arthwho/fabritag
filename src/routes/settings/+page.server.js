/**
 * Carrega o status do dispositivo principal para a tela de configurações.
 *
 * @param {object} input - Contexto da rota.
 * @param {typeof fetch} input.fetch - Fetch server-side do SvelteKit.
 * @returns {Promise<{sensorStatus: {status: string, ip_address: string}}>} Status do sensor.
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ fetch }) {
	try {
		const dispositivoId = 1;
		const response = await fetch(`http://127.0.0.1:5000/api/dispositivos/status/${dispositivoId}`);

		if (response.ok) {
			const sensorStatus = await response.json();
			return {
				pageTitle: 'Configurações',
				pageDescription: 'Gerencie suas preferências e configurações de conta.',
				sensorStatus
			};
		}

		return {
			pageTitle: 'Configurações',
			pageDescription: 'Gerencie suas preferências e configurações de conta.',
			sensorStatus: { status: 'Offline', ip_address: 'N/A' }
		};
	} catch (error) {
		console.error('Error fetching dispositivo status:', error);
		return {
			pageTitle: 'Configurações',
			pageDescription: 'Gerencie suas preferências e configurações de conta.',
			sensorStatus: { status: 'Offline', ip_address: 'N/A' }
		};
	}
}
