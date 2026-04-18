/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
    try {
        const [produtosRes, batchesRes, clientesRes, camarasRes] = await Promise.all([
            fetch('http://127.0.0.1:5000/api/produtos'),
            fetch('http://127.0.0.1:5000/api/batches'),
            fetch('http://127.0.0.1:5000/api/clientes'),
            fetch('http://127.0.0.1:5000/api/camaras')
        ]);

        if (!produtosRes.ok || !batchesRes.ok || !clientesRes.ok || !camarasRes.ok) {
            const produtosText = !produtosRes.ok ? await produtosRes.text() : '';
            const batchesText = !batchesRes.ok ? await batchesRes.text() : '';
            const clientesText = !clientesRes.ok ? await clientesRes.text() : '';
            const camarasText = !camarasRes.ok ? await camarasRes.text() : '';
            console.error('Failed to fetch produtos page data:', {
                produtosStatus: produtosRes.status,
                produtosText,
                batchesStatus: batchesRes.status,
                batchesText,
                clientesStatus: clientesRes.status,
                clientesText,
                camarasStatus: camarasRes.status,
                camarasText
            });
            return {
                produtos: [],
                lotes: [],
                lotesSemProduto: [],
                clientes: [],
                camaras: [],
                error: 'Falha ao carregar os dados de produtos e lotes.'
            };
        }

        const produtosData = await produtosRes.json();
        const batchesData = await batchesRes.json();
        const clientesData = await clientesRes.json();
        const camarasData = await camarasRes.json();

        return {
            produtos: produtosData.produtos || [],
            lotes: batchesData || [],
            lotesSemProduto: produtosData.lotes_sem_produto || [],
            clientes: clientesData || [],
            camaras: camarasData || [],
            error: null
        };
    } catch (error) {
        console.error('Error fetching produtos page data:', error);
        return {
            produtos: [],
            lotes: [],
            lotesSemProduto: [],
            clientes: [],
            camaras: [],
            error: 'Não foi possível conectar ao backend. Verifique se o servidor está rodando.'
        };
    }
}
