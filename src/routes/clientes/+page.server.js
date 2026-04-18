/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
    try {
        const clientesRes = await fetch('http://127.0.0.1:5000/api/clientes');

        if (!clientesRes.ok) {
            const clientesText = await clientesRes.text();
            console.error('Failed to fetch clientes page data:', {
                clientesStatus: clientesRes.status,
                clientesText
            });

            return {
                clientes: [],
                error: 'Falha ao carregar os dados de clientes.'
            };
        }

        const clientesData = await clientesRes.json();

        return {
            clientes: clientesData || [],
            error: null
        };
    } catch (error) {
        console.error('Error fetching clientes page data:', error);
        return {
            clientes: [],
            error: 'Não foi possível conectar ao backend. Verifique se o servidor está rodando.'
        };
    }
}
