import { fail } from '@sveltejs/kit';

// Helper refatorado para não usar dados mocados e lidar com erros
async function fetchFromBackend(fetch, endpoint) {
	try {
		const response = await fetch(`http://127.0.0.1:5000/api/${endpoint}`);
		if (response.ok) {
			return { data: await response.json(), error: null };
		}
		const errorText = await response.text();
		console.error(`Failed to fetch ${endpoint}:`, response.status, response.statusText, errorText);
		return { data: [], error: `Falha ao carregar ${endpoint}.` };
	} catch (error) {
		console.error(`Error fetching ${endpoint}:`, error);
		return { data: [], error: `Não foi possível conectar ao backend para carregar ${endpoint}.` };
	}
}

/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
	const [produtosResponse, camarasResponse] = await Promise.all([
		fetchFromBackend(fetch, 'batches'),
		fetchFromBackend(fetch, 'camaras')
	]);

	// Coleta todos os erros
	const errors = [produtosResponse.error, camarasResponse.error].filter(Boolean);

	return {
		produtos: produtosResponse.data,
		camaras: camarasResponse.data,
		error: errors.length > 0 ? errors.join(' ') : null
	};
}

/** @type {import('./$types').Actions} */
export const actions = {
	default: async ({ request, fetch }) => {
		const formData = await request.formData();
		const produtoId = formData.get('produto');
		const destinoId = formData.get('destino');

		if (!produtoId || !destinoId) {
			return fail(400, {
				error: 'Produto e Destino são obrigatórios.'
			});
		}

		try {
			const response = await fetch('http://127.0.0.1:5000/api/movimentar', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					produto_id: parseInt(produtoId, 10),
					destino_id: parseInt(destinoId, 10)
				})
			});

			if (response.ok) {
				const result = await response.json();
				return {
					success: true,
					message: result.message
				};
			}
			const errorData = await response.json();
			return fail(response.status, {
				error: errorData.error || 'Falha ao registrar a movimentação.'
			});
		} catch (error) {
			console.error('Error moving product:', error);
			return fail(500, {
				error: 'Não foi possível conectar ao backend para registrar a movimentação.'
			});
		}
	}
};
