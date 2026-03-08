/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/infraestrutura');
        if (response.ok) {
            const infraData = await response.json();
            return {
                infraestrutura: infraData,
                error: null
            };
        }
        // Se a resposta não for OK, repassa o erro para a página
        const errorText = await response.text();
        console.error('Failed to fetch infraestrutura data:', response.status, response.statusText, errorText);
        return {
            infraestrutura: null,
            error: `Falha ao carregar os dados da infraestrutura: ${response.statusText}`
        };
    } catch (error) {
        console.error('Error fetching infraestrutura data:', error);
        return {
            infraestrutura: null,
            error: 'Não foi possível conectar ao backend. Verifique se o servidor está rodando.'
        };
    }
}
