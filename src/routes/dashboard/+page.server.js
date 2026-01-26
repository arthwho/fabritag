/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
	try {
		const response = await fetch('http://127.0.0.1:5000/api/dashboard');
		if (response.ok) {
			const dashboardData = await response.json();
			return {
				dashboard: dashboardData,
				error: null
			};
		}
		// Se a resposta não for OK, repassa o erro para a página
		const errorText = await response.text();
		console.error('Failed to fetch dashboard data:', response.status, response.statusText, errorText);
		return {
			dashboard: null,
			error: `Falha ao carregar os dados do dashboard: ${response.statusText}`
		};
	} catch (error) {
		console.error('Error fetching dashboard data:', error);
		return {
			dashboard: null,
			error: 'Não foi possível conectar ao backend. Verifique se o servidor está rodando.'
		};
	}
}
