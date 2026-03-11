/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
	try {
		const [infraRes, liveRes] = await Promise.all([
			fetch('http://127.0.0.1:5000/api/infraestrutura'),
			fetch('http://127.0.0.1:5000/api/dispositivos/status')
		]);

		let infraData = null;
		let liveStatuses = {};

		if (infraRes.ok) {
			infraData = await infraRes.json();
		}

		if (liveRes.ok) {
			liveStatuses = await liveRes.json();
		}

		if (!infraRes.ok) {
			const errorText = await infraRes.text();
			console.error('Failed to fetch infraestrutura data:', infraRes.status, errorText);
			return {
				infraestrutura: null,
				liveStatuses,
				error: `Falha ao carregar os dados da infraestrutura: ${infraRes.statusText}`
			};
		}

		return {
			infraestrutura: infraData,
			liveStatuses,
			error: null
		};
	} catch (error) {
		console.error('Error fetching infraestrutura data:', error);
		return {
			infraestrutura: null,
			liveStatuses: {},
			error: 'Não foi possível conectar ao backend. Verifique se o servidor está rodando.'
		};
	}
}
