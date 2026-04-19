import { fail } from '@sveltejs/kit';

const PRODUTOS_API_URL = 'http://127.0.0.1:5000/api/produtos';
const LOTES_API_URL = 'http://127.0.0.1:5000/api/lotes';

const toStringValue = (value) => String(value ?? '').trim();

function parseOptionalPositiveInteger(rawValue) {
    const value = toStringValue(rawValue);
    if (!value) return null;

    const numberValue = Number(value);
    if (!Number.isInteger(numberValue) || numberValue < 1) {
        throw new Error('Informe um valor inteiro positivo.');
    }

    return numberValue;
}

function parseRequiredPositiveInteger(rawValue, errorMessage) {
    const numberValue = Number(rawValue);
    if (!Number.isInteger(numberValue) || numberValue < 1) {
        throw new Error(errorMessage);
    }

    return numberValue;
}

function parseProdutoAssoc(rawValue) {
    let parsed = [];
    try {
        parsed = JSON.parse(String(rawValue ?? '[]'));
    } catch {
        throw new Error('Dados de produtos do lote inválidos.');
    }

    if (!Array.isArray(parsed) || parsed.length === 0) {
        throw new Error('Selecione ao menos um produto.');
    }

    return parsed.map((item) => {
        const produtoTipoId = Number(item?.produto_tipo_id);
        const quantidade = Number(item?.quantidade);

        if (!Number.isInteger(produtoTipoId) || produtoTipoId < 1) {
            throw new Error('Produto associado inválido.');
        }

        if (!Number.isFinite(quantidade) || quantidade <= 0) {
            throw new Error('Informe uma quantidade válida para os produtos selecionados.');
        }

        return {
            produto_tipo_id: produtoTipoId,
            quantidade
        };
    });
}

async function getApiError(response, fallbackError) {
    const errorData = await response.json().catch(() => null);
    if (errorData?.error) return errorData.error;

    const errorText = await response.text().catch(() => '');
    return errorText || fallbackError;
}

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

/** @type {import('./$types').Actions} */
export const actions = {
    createProduto: async ({ request, fetch }) => {
        const formData = await request.formData();
        const nome = toStringValue(formData.get('nome'));
        const sku = toStringValue(formData.get('sku'));
        const unidadeMedida = toStringValue(formData.get('unidadeMedida'));
        const clienteIdRaw = formData.get('clienteId');

        if (!nome) {
            return fail(400, {
                action: 'createProduto',
                error: 'O nome do produto é obrigatório.',
                fieldValues: { nome, sku, unidadeMedida, clienteId: toStringValue(clienteIdRaw) }
            });
        }

        let clienteId = null;
        try {
            clienteId = parseOptionalPositiveInteger(clienteIdRaw);
        } catch {
            return fail(400, {
                action: 'createProduto',
                error: 'Informe um cliente válido.',
                fieldValues: { nome, sku, unidadeMedida, clienteId: toStringValue(clienteIdRaw) }
            });
        }

        const response = await fetch(PRODUTOS_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cliente_id: clienteId,
                nome,
                sku: sku || null,
                unidade_medida: unidadeMedida || null
            })
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'createProduto',
                error: await getApiError(response, 'Não foi possível criar o produto.'),
                fieldValues: { nome, sku, unidadeMedida, clienteId: toStringValue(clienteIdRaw) }
            });
        }

        return { success: true, action: 'createProduto' };
    },

    updateProduto: async ({ request, fetch }) => {
        const formData = await request.formData();
        const produtoIdRaw = formData.get('produtoId');
        const nome = toStringValue(formData.get('nome'));
        const sku = toStringValue(formData.get('sku'));
        const unidadeMedida = toStringValue(formData.get('unidadeMedida'));
        const clienteIdRaw = formData.get('clienteId');

        let produtoId = 0;
        try {
            produtoId = parseRequiredPositiveInteger(produtoIdRaw, 'Produto inválido para atualização.');
        } catch (error) {
            return fail(400, {
                action: 'updateProduto',
                error: error instanceof Error ? error.message : 'Produto inválido para atualização.',
                fieldValues: { nome, sku, unidadeMedida, clienteId: toStringValue(clienteIdRaw) }
            });
        }

        if (!nome) {
            return fail(400, {
                action: 'updateProduto',
                error: 'O nome do produto é obrigatório.',
                fieldValues: { nome, sku, unidadeMedida, clienteId: toStringValue(clienteIdRaw) }
            });
        }

        let clienteId = null;
        try {
            clienteId = parseOptionalPositiveInteger(clienteIdRaw);
        } catch {
            return fail(400, {
                action: 'updateProduto',
                error: 'Informe um cliente válido.',
                fieldValues: { nome, sku, unidadeMedida, clienteId: toStringValue(clienteIdRaw) }
            });
        }

        const response = await fetch(`${PRODUTOS_API_URL}/${produtoId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cliente_id: clienteId,
                nome,
                sku: sku || null,
                unidade_medida: unidadeMedida || null
            })
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'updateProduto',
                error: await getApiError(response, 'Não foi possível atualizar o produto.'),
                fieldValues: { nome, sku, unidadeMedida, clienteId: toStringValue(clienteIdRaw) }
            });
        }

        return { success: true, action: 'updateProduto' };
    },

    deleteProduto: async ({ request, fetch }) => {
        const formData = await request.formData();
        const produtoIdRaw = formData.get('produtoId');

        let produtoId = 0;
        try {
            produtoId = parseRequiredPositiveInteger(produtoIdRaw, 'Produto inválido para exclusão.');
        } catch (error) {
            return fail(400, {
                action: 'deleteProduto',
                error: error instanceof Error ? error.message : 'Produto inválido para exclusão.'
            });
        }

        const response = await fetch(`${PRODUTOS_API_URL}/${produtoId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'deleteProduto',
                error: await getApiError(response, 'Não foi possível excluir o produto.')
            });
        }

        return { success: true, action: 'deleteProduto' };
    },

    updateLote: async ({ request, fetch }) => {
        const formData = await request.formData();
        const epcTag = toStringValue(formData.get('epcTag'));
        const produtoAssocRaw = formData.get('produtoAssocJson');

        if (!epcTag) {
            return fail(400, {
                action: 'updateLote',
                error: 'Lote inválido para atualização.'
            });
        }

        let produtoAssoc = [];
        try {
            produtoAssoc = parseProdutoAssoc(produtoAssocRaw);
        } catch (error) {
            return fail(400, {
                action: 'updateLote',
                error:
                    error instanceof Error
                        ? error.message
                        : 'Dados de produtos do lote inválidos.',
                fieldValues: {
                    loteProdutoTipoIds: produtoAssocRaw,
                    editingLoteEpcTag: epcTag
                }
            });
        }

        const response = await fetch(`${LOTES_API_URL}/${epcTag}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                produto_assoc: produtoAssoc
            })
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'updateLote',
                error: await getApiError(response, 'Não foi possível atualizar o lote.')
            });
        }

        return { success: true, action: 'updateLote' };
    },

    moveLote: async ({ request, fetch }) => {
        const formData = await request.formData();
        const epcTag = toStringValue(formData.get('epcTag'));
        const camaraIdRaw = formData.get('camaraId');

        if (!epcTag) {
            return fail(400, {
                action: 'moveLote',
                error: 'Lote inválido para movimentação.'
            });
        }

        let camaraId = 0;
        try {
            camaraId = parseRequiredPositiveInteger(camaraIdRaw, 'Selecione uma câmara de destino válida.');
        } catch (error) {
            return fail(400, {
                action: 'moveLote',
                error:
                    error instanceof Error
                        ? error.message
                        : 'Selecione uma câmara de destino válida.'
            });
        }

        const response = await fetch(`${LOTES_API_URL}/${epcTag}/movimentar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                camara_id: camaraId
            })
        });

        if (!response.ok) {
            return fail(response.status, {
                action: 'moveLote',
                error: await getApiError(response, 'Não foi possível movimentar o lote.')
            });
        }

        return { success: true, action: 'moveLote' };
    }
};
