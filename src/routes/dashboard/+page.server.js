/**
 * Normaliza texto para busca sem acentos e sem diferenciar maiúsculas.
 *
 * @param {unknown} str - Texto de origem.
 * @returns {string} Texto normalizado.
 */
const normalizeText = (str) =>
	String(str || '')
		.toLowerCase()
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '');

/**
 * Converte timestamp textual do backend em Date local.
 *
 * @param {unknown} value - Data no formato "YYYY-MM-DD HH:mm:ss".
 * @returns {Date|null} Data convertida ou null quando inválida.
 */
const parseMovimentacaoDate = (value) => {
	if (!value) return null;
	const [datePart, timePart = '00:00:00'] = String(value).split(' ');
	const [year, month, day] = datePart.split('-').map(Number);
	const [hour, minute, second] = timePart.split(':').map(Number);

	if (!year || !month || !day) return null;
	return new Date(year, month - 1, day, hour || 0, minute || 0, second || 0);
};

/**
 * Enriquece movimentações do dashboard com campos auxiliares de UI.
 *
 * @param {object|null} dashboardData - Payload retornado pela API Flask.
 * @returns {object} Payload com date_timestamp e search_index nas movimentações.
 */
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

/**
 * Carrega os dados do dashboard.
 *
 * @param {object} input - Contexto da rota.
 * @param {typeof fetch} input.fetch - Fetch server-side do SvelteKit.
 * @returns {Promise<{dashboard: object|null, error: string|null}>} Dados da página.
 * @type {import('./$types').PageServerLoad}
 */
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
