const normalizeText = (str) =>
	String(str || '')
		.toLowerCase()
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '');

const parseMovimentacaoDate = (value) => {
	if (!value) return null;
	const [datePart, timePart = '00:00:00'] = String(value).split(' ');
	const [year, month, day] = datePart.split('-').map(Number);
	const [hour, minute, second] = timePart.split(':').map(Number);

	if (!year || !month || !day) return null;
	return new Date(year, month - 1, day, hour || 0, minute || 0, second || 0);
};

function enrichMovimentacoes(dashboardData) {
	const baseMovimentacoes = Array.isArray(dashboardData?.ultimas_movimentacoes)
		? dashboardData.ultimas_movimentacoes
		: [];

	const ultimasMovimentacoes = baseMovimentacoes.map((item) => {
		const date = parseMovimentacaoDate(item?.data);
		const searchIndex = normalizeText(
			[item?.produto, item?.origem, item?.destino, item?.data].filter(Boolean).join(' ')
		);

		return {
			...item,
			date_timestamp: date ? date.getTime() : null,
			search_index: searchIndex
		};
	});

	return {
		...dashboardData,
		ultimas_movimentacoes: ultimasMovimentacoes
	};
}

/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
	try {
		const response = await fetch('http://127.0.0.1:5000/api/dashboard');
		if (response.ok) {
			const dashboardData = await response.json();
			return {
				dashboard: enrichMovimentacoes(dashboardData),
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
