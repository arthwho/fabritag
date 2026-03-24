/** @type {import('./$types').PageServerLoad} */
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
			camara: camaraData,
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
