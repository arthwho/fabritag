/**
 * Converte índice de coluna em letras no padrão A, B, ..., AA.
 *
 * @param {number} n - Número da coluna começando em 1.
 * @returns {string} Letra da coluna.
 */
function getColumnLetter(n) {
	let letter = '';
	while (n > 0) {
		const temp = (n - 1) % 26;
		letter = String.fromCharCode(temp + 65) + letter;
		n = (n - temp - 1) / 26;
	}
	return letter;
}

/**
 * Enriquece detalhes da câmara com grade visual e posições dos lotes.
 *
 * @param {object|null} camaraData - Dados retornados pela API Flask.
 * @returns {object} Câmara com capacidade, linhas, colunas e lotes posicionados.
 */
function enrichCamara(camaraData) {
	const capacity = Number(camaraData?.capacidade || 0);
	const cols = Math.ceil(Math.sqrt(capacity * 1.5)) || 1;
	const rows = Math.ceil(capacity / cols) || 0;

	const lotesBase = Array.isArray(camaraData?.lotes) ? camaraData.lotes : [];
	const lotes = lotesBase.map((lote) => {
		const startPos = lote.posicao_vaga ?? 0;
		const quantity = Math.max(1, Math.ceil(Number(lote.quantidade || 1)));
		const endPos = startPos + quantity - 1;

		const getPosStr = (idx) => {
			const r = Math.floor(idx / cols) + 1;
			const c = (idx % cols) + 1;
			return `${getColumnLetter(c)}${r}`;
		};

		return {
			...lote,
			quantity,
			startPos,
			endPos,
			posicao: quantity > 1 ? `${getPosStr(startPos)} - ${getPosStr(endPos)}` : getPosStr(startPos)
		};
	});

	const ocupacaoCalculada = lotes.reduce((acc, lote) => acc + lote.quantity, 0);

	return {
		...camaraData,
		capacity,
		cols,
		rows,
		lotes,
		ocupacao_calculada: ocupacaoCalculada
	};
}

/**
 * Carrega os detalhes de uma câmara específica.
 *
 * @param {object} input - Contexto da rota.
 * @param {{id: string}} input.params - Parâmetros da URL.
 * @param {typeof fetch} input.fetch - Fetch server-side do SvelteKit.
 * @returns {Promise<{camara: object|null, error: string|null}>} Dados da página.
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ params, fetch }) {
	const { id } = params;
	try {
		const res = await fetch(`http://127.0.0.1:5000/api/camaras/${id}`);

		if (!res.ok) {
			const errorText = await res.text();
			console.error(`Failed to fetch camara ${id} details:`, res.status, errorText);
			return {
				camara: null,
				error: `Falha ao carregar os detalhes da câmara: ${res.statusText}`
			};
		}

		const camaraData = await res.json();

		return {
			camara: enrichCamara(camaraData),
			error: null
		};
	} catch (error) {
		console.error(`Error fetching camara ${id} data:`, error);
		return {
			camara: null,
			error: 'Não foi possível conectar ao backend. Verifique se o servidor está rodando.'
		};
	}
}
