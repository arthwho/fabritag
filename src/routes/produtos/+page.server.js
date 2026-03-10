/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
    try {
        const [produtosRes, batchesRes] = await Promise.all([
            fetch('http://127.0.0.1:5000/api/produtos'),
            fetch('http://127.0.0.1:5000/api/batches')
        ]);

        if (!produtosRes.ok || !batchesRes.ok) {
            const produtosText = !produtosRes.ok ? await produtosRes.text() : '';
            const batchesText = !batchesRes.ok ? await batchesRes.text() : '';
            console.error('Failed to fetch produtos page data:', {
                produtosStatus: produtosRes.status,
                produtosText,
                batchesStatus: batchesRes.status,
                batchesText
            });
            return {
                produtos: [],
                lotes: [],
                lotesSemProduto: [],
                error: 'Falha ao carregar os dados de produtos e lotes.'
            };
        }

        const produtosData = await produtosRes.json();
        const batchesData = await batchesRes.json();

        return {
            produtos: produtosData.produtos || [],
            lotes: batchesData || [],
            lotesSemProduto: produtosData.lotes_sem_produto || [],
            error: null
        };
    } catch (error) {
        console.error('Error fetching produtos page data:', error);
        return {
            produtos: [],
            lotes: [],
            lotesSemProduto: [],
            error: 'Não foi possível conectar ao backend. Verifique se o servidor está rodando.'
        };
    }
}
