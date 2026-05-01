import { fail } from '@sveltejs/kit';

const API_BASE_URL = 'http://127.0.0.1:5000/api';

/**
 * Converte valores de formulário em string aparada.
 *
 * @param {unknown} value - Valor recebido de FormData ou API.
 * @returns {string} Texto normalizado.
 */
const toStringValue = (value) => String(value ?? '').trim();

/**
 * Lê um inteiro positivo obrigatório.
 *
 * @param {unknown} rawValue - Valor bruto do formulário.
 * @param {string} errorMessage - Mensagem para valor inválido.
 * @returns {number} Inteiro positivo.
 */
function parseRequiredPositiveInteger(rawValue, errorMessage) {
	const numberValue = Number(rawValue);
	if (!Number.isInteger(numberValue) || numberValue <= 0) {
		throw new Error(errorMessage);
	}

	return numberValue;
}

/**
 * Lê um inteiro não negativo opcional.
 *
 * @param {unknown} rawValue - Valor bruto do formulário.
 * @param {string} errorMessage - Mensagem para valor inválido.
 * @returns {number|null} Inteiro não negativo ou null quando vazio.
 */
function parseOptionalNonNegativeInteger(rawValue, errorMessage) {
	const value = toStringValue(rawValue);
	if (!value) return null;

	const numberValue = Number(value);
	if (!Number.isInteger(numberValue) || numberValue < 0) {
		throw new Error(errorMessage);
	}

	return numberValue;
}

/**
 * Interpreta valor de formulário como booleano.
 *
 * @param {unknown} rawValue - Valor bruto do checkbox/campo.
 * @returns {boolean} True para true, 1 ou on.
 */
function parseBooleanFromFormData(rawValue) {
	const value = toStringValue(rawValue).toLowerCase();
	return value === 'true' || value === '1' || value === 'on';
}

/**
 * Extrai mensagem de erro de uma resposta HTTP da API.
 *
 * @param {Response} response - Resposta fetch com erro.
 * @param {string} fallbackError - Mensagem padrão.
 * @returns {Promise<string>} Mensagem final.
 */
async function getApiError(response, fallbackError) {
	const errorData = await response.json().catch(() => null);
	if (errorData?.error) return errorData.error;

	const errorText = await response.text().catch(() => '');
	return errorText || fallbackError;
}

/**
 * Carrega infraestrutura e status ao vivo dos dispositivos.
 *
 * @param {object} input - Contexto da rota.
 * @param {typeof fetch} input.fetch - Fetch server-side do SvelteKit.
 * @returns {Promise<object>} Dados da infraestrutura, status e erro opcional.
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ fetch }) {
	try {
		const [infraRes, liveRes] = await Promise.all([
			fetch('http://127.0.0.1:5000/api/infraestrutura'),
			fetch('http://127.0.0.1:5000/api/dispositivos/status')
		]);

		let infraData = null;
		let liveStatuses = {};

		if (infraRes.ok) {
			infraData = await infraRes.json();
		}

		if (liveRes.ok) {
			liveStatuses = await liveRes.json();
		}

		if (!infraRes.ok) {
			const errorText = await infraRes.text();
			console.error('Failed to fetch infraestrutura data:', infraRes.status, errorText);
			return {
				infraestrutura: null,
				liveStatuses,
				error: `Falha ao carregar os dados da infraestrutura: ${infraRes.statusText}`
			};
		}

		return {
			infraestrutura: infraData,
			liveStatuses,
			error: null
		};
	} catch (error) {
		console.error('Error fetching infraestrutura data:', error);
		return {
			infraestrutura: null,
			liveStatuses: {},
			error: 'Não foi possível conectar ao backend. Verifique se o servidor está rodando.'
		};
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	createPredio: async ({ request, fetch }) => {
		const formData = await request.formData();
		const nome = toStringValue(formData.get('predioNome'));
		const endereco = toStringValue(formData.get('predioEndereco'));

		if (!nome) {
			return fail(400, {
				action: 'createPredio',
				error: 'O nome do prédio é obrigatório.',
				fieldValues: { predioNome: nome, predioEndereco: endereco }
			});
		}

		const response = await fetch(`${API_BASE_URL}/predios`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				nome,
				endereco: endereco || null
			})
		});

		if (!response.ok) {
			return fail(response.status, {
				action: 'createPredio',
				error: await getApiError(response, 'Não foi possível criar o prédio.'),
				fieldValues: { predioNome: nome, predioEndereco: endereco }
			});
		}

		return { success: true, action: 'createPredio' };
	},

	updatePredio: async ({ request, fetch }) => {
		const formData = await request.formData();
		const predioIdRaw = formData.get('predioId');
		const nome = toStringValue(formData.get('predioNome'));
		const endereco = toStringValue(formData.get('predioEndereco'));

		let predioId = 0;
		try {
			predioId = parseRequiredPositiveInteger(predioIdRaw, 'Prédio inválido para atualização.');
		} catch (error) {
			return fail(400, {
				action: 'updatePredio',
				error: error instanceof Error ? error.message : 'Prédio inválido para atualização.',
				fieldValues: { predioNome: nome, predioEndereco: endereco }
			});
		}

		if (!nome) {
			return fail(400, {
				action: 'updatePredio',
				error: 'O nome do prédio é obrigatório.',
				fieldValues: { predioNome: nome, predioEndereco: endereco }
			});
		}

		const response = await fetch(`${API_BASE_URL}/predios/${predioId}`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				nome,
				endereco: endereco || null
			})
		});

		if (!response.ok) {
			return fail(response.status, {
				action: 'updatePredio',
				error: await getApiError(response, 'Não foi possível atualizar o prédio.'),
				fieldValues: { predioNome: nome, predioEndereco: endereco }
			});
		}

		return { success: true, action: 'updatePredio' };
	},

	deletePredio: async ({ request, fetch }) => {
		const formData = await request.formData();
		const predioIdRaw = formData.get('predioId');

		let predioId = 0;
		try {
			predioId = parseRequiredPositiveInteger(predioIdRaw, 'Prédio inválido para exclusão.');
		} catch (error) {
			return fail(400, {
				action: 'deletePredio',
				error: error instanceof Error ? error.message : 'Prédio inválido para exclusão.'
			});
		}

		const response = await fetch(`${API_BASE_URL}/predios/${predioId}`, {
			method: 'DELETE'
		});

		if (!response.ok) {
			return fail(response.status, {
				action: 'deletePredio',
				error: await getApiError(response, 'Não foi possível excluir o prédio.')
			});
		}

		return { success: true, action: 'deletePredio' };
	},

	createCamara: async ({ request, fetch }) => {
		const formData = await request.formData();
		const camaraPredioIdRaw = formData.get('camaraPredioId');
		const camaraNome = toStringValue(formData.get('camaraNome'));
		const camaraCapacidadeRaw = formData.get('camaraCapacidade');

		let predioId = 0;
		try {
			predioId = parseRequiredPositiveInteger(
				camaraPredioIdRaw,
				'Selecione um prédio válido para a câmara.'
			);
		} catch (error) {
			return fail(400, {
				action: 'createCamara',
				error:
					error instanceof Error
						? error.message
						: 'Selecione um prédio válido para a câmara.',
				fieldValues: {
					camaraPredioId: toStringValue(camaraPredioIdRaw),
					camaraNome,
					camaraCapacidade: toStringValue(camaraCapacidadeRaw)
				}
			});
		}

		if (!camaraNome) {
			return fail(400, {
				action: 'createCamara',
				error: 'O nome da câmara é obrigatório.',
				fieldValues: {
					camaraPredioId: String(predioId),
					camaraNome,
					camaraCapacidade: toStringValue(camaraCapacidadeRaw)
				}
			});
		}

		let capacidadeVagas = null;
		try {
			capacidadeVagas = parseOptionalNonNegativeInteger(
				camaraCapacidadeRaw,
				'Informe uma capacidade válida.'
			);
		} catch (error) {
			return fail(400, {
				action: 'createCamara',
				error: error instanceof Error ? error.message : 'Informe uma capacidade válida.',
				fieldValues: {
					camaraPredioId: String(predioId),
					camaraNome,
					camaraCapacidade: toStringValue(camaraCapacidadeRaw)
				}
			});
		}

		const response = await fetch(`${API_BASE_URL}/camaras`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				predio_id: predioId,
				nome: camaraNome,
				capacidade_vagas: capacidadeVagas
			})
		});

		if (!response.ok) {
			return fail(response.status, {
				action: 'createCamara',
				error: await getApiError(response, 'Não foi possível criar a câmara.'),
				fieldValues: {
					camaraPredioId: String(predioId),
					camaraNome,
					camaraCapacidade: toStringValue(camaraCapacidadeRaw)
				}
			});
		}

		return { success: true, action: 'createCamara' };
	},

	updateCamara: async ({ request, fetch }) => {
		const formData = await request.formData();
		const camaraIdRaw = formData.get('camaraId');
		const camaraPredioIdRaw = formData.get('camaraPredioId');
		const camaraNome = toStringValue(formData.get('camaraNome'));
		const camaraCapacidadeRaw = formData.get('camaraCapacidade');

		let camaraId = 0;
		let predioId = 0;
		try {
			camaraId = parseRequiredPositiveInteger(camaraIdRaw, 'Câmara inválida para atualização.');
			predioId = parseRequiredPositiveInteger(
				camaraPredioIdRaw,
				'Selecione um prédio válido para a câmara.'
			);
		} catch (error) {
			return fail(400, {
				action: 'updateCamara',
				error:
					error instanceof Error
						? error.message
						: 'Dados inválidos para atualizar a câmara.',
				fieldValues: {
					camaraPredioId: toStringValue(camaraPredioIdRaw),
					camaraNome,
					camaraCapacidade: toStringValue(camaraCapacidadeRaw)
				}
			});
		}

		if (!camaraNome) {
			return fail(400, {
				action: 'updateCamara',
				error: 'O nome da câmara é obrigatório.',
				fieldValues: {
					camaraPredioId: String(predioId),
					camaraNome,
					camaraCapacidade: toStringValue(camaraCapacidadeRaw)
				}
			});
		}

		let capacidadeVagas = null;
		try {
			capacidadeVagas = parseOptionalNonNegativeInteger(
				camaraCapacidadeRaw,
				'Informe uma capacidade válida.'
			);
		} catch (error) {
			return fail(400, {
				action: 'updateCamara',
				error: error instanceof Error ? error.message : 'Informe uma capacidade válida.',
				fieldValues: {
					camaraPredioId: String(predioId),
					camaraNome,
					camaraCapacidade: toStringValue(camaraCapacidadeRaw)
				}
			});
		}

		const response = await fetch(`${API_BASE_URL}/camaras/${camaraId}`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				predio_id: predioId,
				nome: camaraNome,
				capacidade_vagas: capacidadeVagas
			})
		});

		if (!response.ok) {
			return fail(response.status, {
				action: 'updateCamara',
				error: await getApiError(response, 'Não foi possível atualizar a câmara.'),
				fieldValues: {
					camaraPredioId: String(predioId),
					camaraNome,
					camaraCapacidade: toStringValue(camaraCapacidadeRaw)
				}
			});
		}

		return { success: true, action: 'updateCamara' };
	},

	deleteCamara: async ({ request, fetch }) => {
		const formData = await request.formData();
		const camaraIdRaw = formData.get('camaraId');

		let camaraId = 0;
		try {
			camaraId = parseRequiredPositiveInteger(camaraIdRaw, 'Câmara inválida para exclusão.');
		} catch (error) {
			return fail(400, {
				action: 'deleteCamara',
				error: error instanceof Error ? error.message : 'Câmara inválida para exclusão.'
			});
		}

		const response = await fetch(`${API_BASE_URL}/camaras/${camaraId}`, {
			method: 'DELETE'
		});

		if (!response.ok) {
			return fail(response.status, {
				action: 'deleteCamara',
				error: await getApiError(response, 'Não foi possível excluir a câmara.')
			});
		}

		return { success: true, action: 'deleteCamara' };
	},

	createSensor: async ({ request, fetch }) => {
		const formData = await request.formData();
		const sensorCamaraIdRaw = formData.get('sensorCamaraId');
		const sensorModelo = toStringValue(formData.get('sensorModelo')) || 'PN5180';
		const sensorAtivo = parseBooleanFromFormData(formData.get('sensorAtivo'));

		let camaraId = 0;
		try {
			camaraId = parseRequiredPositiveInteger(
				sensorCamaraIdRaw,
				'Selecione a câmara do sensor.'
			);
		} catch (error) {
			return fail(400, {
				action: 'createSensor',
				error: error instanceof Error ? error.message : 'Selecione a câmara do sensor.',
				fieldValues: {
					sensorCamaraId: toStringValue(sensorCamaraIdRaw),
					sensorModelo,
					sensorAtivo
				}
			});
		}

		const response = await fetch(`${API_BASE_URL}/sensores`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				camara_id: camaraId,
				modelo: sensorModelo,
				ativo: sensorAtivo
			})
		});

		if (!response.ok) {
			return fail(response.status, {
				action: 'createSensor',
				error: await getApiError(response, 'Não foi possível criar o sensor.'),
				fieldValues: {
					sensorCamaraId: String(camaraId),
					sensorModelo,
					sensorAtivo
				}
			});
		}

		return { success: true, action: 'createSensor' };
	},

	updateSensor: async ({ request, fetch }) => {
		const formData = await request.formData();
		const sensorIdRaw = formData.get('sensorId');
		const sensorCamaraIdRaw = formData.get('sensorCamaraId');
		const sensorModelo = toStringValue(formData.get('sensorModelo')) || 'PN5180';
		const sensorAtivo = parseBooleanFromFormData(formData.get('sensorAtivo'));

		let sensorId = 0;
		let camaraId = 0;
		try {
			sensorId = parseRequiredPositiveInteger(sensorIdRaw, 'Sensor inválido para atualização.');
			camaraId = parseRequiredPositiveInteger(
				sensorCamaraIdRaw,
				'Selecione a câmara do sensor.'
			);
		} catch (error) {
			return fail(400, {
				action: 'updateSensor',
				error:
					error instanceof Error ? error.message : 'Dados inválidos para atualizar o sensor.',
				fieldValues: {
					sensorCamaraId: toStringValue(sensorCamaraIdRaw),
					sensorModelo,
					sensorAtivo
				}
			});
		}

		const response = await fetch(`${API_BASE_URL}/sensores/${sensorId}`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				camara_id: camaraId,
				modelo: sensorModelo,
				ativo: sensorAtivo
			})
		});

		if (!response.ok) {
			return fail(response.status, {
				action: 'updateSensor',
				error: await getApiError(response, 'Não foi possível atualizar o sensor.'),
				fieldValues: {
					sensorCamaraId: String(camaraId),
					sensorModelo,
					sensorAtivo
				}
			});
		}

		return { success: true, action: 'updateSensor' };
	},

	deleteSensor: async ({ request, fetch }) => {
		const formData = await request.formData();
		const sensorIdRaw = formData.get('sensorId');

		let sensorId = 0;
		try {
			sensorId = parseRequiredPositiveInteger(sensorIdRaw, 'Sensor inválido para exclusão.');
		} catch (error) {
			return fail(400, {
				action: 'deleteSensor',
				error: error instanceof Error ? error.message : 'Sensor inválido para exclusão.'
			});
		}

		const response = await fetch(`${API_BASE_URL}/sensores/${sensorId}`, {
			method: 'DELETE'
		});

		if (!response.ok) {
			return fail(response.status, {
				action: 'deleteSensor',
				error: await getApiError(response, 'Não foi possível excluir o sensor.')
			});
		}

		return { success: true, action: 'deleteSensor' };
	}
};
