<script lang="ts">
	import { onMount } from 'svelte';
	import { enhance } from '$app/forms';
	import type { SubmitFunction } from '@sveltejs/kit';
	import InfoCard from '$lib/components/InfoCard.svelte';
	import { sensorStore } from '$lib/dispositivos.svelte.js';
	import {
		Badge,
		TableSearch,
		TableHead,
		TableHeadCell,
		TableBody,
		TableBodyRow,
		TableBodyCell,
		ChevronRightOutline
	} from '$lib/uicomponents.js';
	import InfraPrediosSection from './InfraPrediosSection.svelte';
	import InfraCamarasSection from './InfraCamarasSection.svelte';
	import InfraSensoresSection from './InfraSensoresSection.svelte';
	import InfraCreateModals from './InfraCreateModals.svelte';

	type InfraActionResult = {
		action?:
			| 'createPredio'
			| 'updatePredio'
			| 'deletePredio'
			| 'createCamara'
			| 'updateCamara'
			| 'deleteCamara'
			| 'createSensor'
			| 'updateSensor'
			| 'deleteSensor';
		success?: boolean;
		error?: string;
		fieldValues?: {
			predioNome?: string;
			predioEndereco?: string;
			camaraPredioId?: string;
			camaraNome?: string;
			camaraCapacidade?: string;
			sensorCamaraId?: string;
			sensorModelo?: string;
			sensorAtivo?: boolean;
		};
	};

	let { data, form } = $props();
	let infraestrutura = $derived(data.infraestrutura);
	let actionResult = $derived((form || null) as InfraActionResult | null);
	let deviceStatus = $derived(
		sensorStore.liveStatuses['1'] || { status: 'Offline', ip_address: 'N/A' }
	);
	let searchTermAll = $state('');
	let searchTermPredios = $state('');
	let searchTermCamaras = $state('');
	let searchTerm = $state('');
	let activeSection = $state<'todos' | 'predios' | 'camaras' | 'sensores'>('todos');

	let isPredioModalOpen = $state(false);
	let isCamaraModalOpen = $state(false);
	let isSensorModalOpen = $state(false);
	let editingPredioId = $state<number | null>(null);
	let editingCamaraId = $state<number | null>(null);
	let editingSensorId = $state<number | null>(null);
	let isSubmitting = $state(false);
	let formError = $state('');

	let predioNome = $state('');
	let predioEndereco = $state('');

	let camaraPredioId = $state('');
	let camaraNome = $state('');
	let camaraCapacidade = $state('');

	let sensorCamaraId = $state('');
	let sensorModelo = $state('PN5180');
	let sensorAtivo = $state(true);
	let deletePredioForms = $state<Record<number, HTMLFormElement | undefined>>({});
	let deleteCamaraForms = $state<Record<number, HTMLFormElement | undefined>>({});
	let deleteSensorForms = $state<Record<number, HTMLFormElement | undefined>>({});

	const normalize = (str: string) =>
		str
			.toString()
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '');

	let filteredItems = $derived(
		infraestrutura?.lista_sensores?.filter((item) => {
			const search = normalize(searchTerm);
			return Object.values(item).some((val) => normalize((val ?? '').toString()).includes(search));
		}) || []
	);

	let filteredPredios = $derived(
		infraestrutura?.lista_predios?.filter((item) => {
			const search = normalize(searchTermPredios);
			return Object.values(item).some((val) => normalize((val ?? '').toString()).includes(search));
		}) || []
	);

	let filteredCamaras = $derived(
		infraestrutura?.lista_camaras?.filter((item) => {
			const search = normalize(searchTermCamaras);
			return Object.values(item).some((val) => normalize((val ?? '').toString()).includes(search));
		}) || []
	);

	let allTableRows = $derived.by(() => {
		if (!infraestrutura?.lista_camaras) return [];
		return infraestrutura.lista_camaras.map((camara) => ({
			id: camara.id,
			camara: camara.nome,
			predio: camara.predio,
			total_sensores: Number(camara.total_sensores || 0),
			status: (camara.sensores_ativos || 0) > 0 ? 'Ativa' : 'Inativa'
		}));
	});

	let filteredAllTableRows = $derived(
		allTableRows.filter((item) => {
			const search = normalize(searchTermAll);
			return Object.values(item).some((val) => normalize((val ?? '').toString()).includes(search));
		})
	);

	let predioModalTitle = $derived(editingPredioId ? 'Editar Prédio' : 'Adicionar Prédio');
	let camaraModalTitle = $derived(editingCamaraId ? 'Editar Câmara' : 'Adicionar Câmara');
	let sensorModalTitle = $derived(editingSensorId ? 'Editar Sensor' : 'Adicionar Sensor');
	let predioSubmitLabel = $derived(editingPredioId ? 'Salvar alterações' : 'Salvar');
	let camaraSubmitLabel = $derived(editingCamaraId ? 'Salvar alterações' : 'Salvar');
	let sensorSubmitLabel = $derived(editingSensorId ? 'Salvar alterações' : 'Salvar');
	let predioFormAction = $derived(editingPredioId ? '?/updatePredio' : '?/createPredio');
	let camaraFormAction = $derived(editingCamaraId ? '?/updateCamara' : '?/createCamara');
	let sensorFormAction = $derived(editingSensorId ? '?/updateSensor' : '?/createSensor');

	onMount(() => {
		sensorStore.setInitial(data.liveStatuses || {});
		const stopPolling = sensorStore.startPolling();
		return () => stopPolling;
	});

	function handleEditPredio(predioId: number) {
		const predio = infraestrutura?.lista_predios?.find((item) => item.id === predioId);
		if (!predio) return;

		resetFeedback();
		editingPredioId = predioId;
		predioNome = predio.nome || '';
		predioEndereco = predio.endereco === '-' ? '' : (predio.endereco ?? '');
		isPredioModalOpen = true;
	}

	function handleDeletePredio(predioId: number) {
		if (!window.confirm('Tem certeza que deseja excluir este prédio?')) return;
		deletePredioForms[predioId]?.requestSubmit();
	}

	function handleEditCamara(camaraId: number) {
		const camara = infraestrutura?.lista_camaras?.find((item) => item.id === camaraId);
		if (!camara) return;

		resetFeedback();
		editingCamaraId = camaraId;
		camaraPredioId = camara.predio_id?.toString() || '';
		camaraNome = camara.nome || '';
		camaraCapacidade = camara.capacidade_vagas == null ? '' : String(camara.capacidade_vagas);
		isCamaraModalOpen = true;
	}

	function handleDeleteCamara(camaraId: number) {
		if (!window.confirm('Tem certeza que deseja excluir esta câmara?')) return;
		deleteCamaraForms[camaraId]?.requestSubmit();
	}

	function handleEdit(sensorId: number) {
		const sensor = infraestrutura?.lista_sensores?.find((item) => item.id === sensorId);
		if (!sensor) return;

		resetFeedback();
		editingSensorId = sensorId;
		sensorCamaraId = sensor.camara_id?.toString() || '';
		sensorModelo = sensor.modelo || 'PN5180';
		sensorAtivo = Boolean(sensor.ativo);
		isSensorModalOpen = true;
	}

	function handleDeleteSensor(sensorId: number) {
		if (!window.confirm('Tem certeza que deseja excluir este sensor?')) return;
		deleteSensorForms[sensorId]?.requestSubmit();
	}

	function resetFeedback() {
		formError = '';
	}

	function openPredioModal() {
		resetFeedback();
		editingPredioId = null;
		predioNome = '';
		predioEndereco = '';
		isPredioModalOpen = true;
	}

	function openCamaraModal() {
		resetFeedback();
		editingCamaraId = null;
		camaraPredioId = infraestrutura?.lista_predios?.[0]?.id?.toString() || '';
		camaraNome = '';
		camaraCapacidade = '';
		isCamaraModalOpen = true;
	}

	function openSensorModal() {
		resetFeedback();
		editingSensorId = null;
		sensorCamaraId = infraestrutura?.lista_camaras?.[0]?.id?.toString() || '';
		sensorModelo = 'PN5180';
		sensorAtivo = true;
		isSensorModalOpen = true;
	}

	const handleInfraSubmit: SubmitFunction = () => {
		isSubmitting = true;
		resetFeedback();

		return async ({ result, update }) => {
			isSubmitting = false;
			await update({ invalidateAll: result.type === 'success' });
			if (result.type === 'error') {
				formError = 'Não foi possível processar a solicitação.';
			}
		};
	};

	const handleDeleteSubmit: SubmitFunction = () => {
		isSubmitting = true;
		resetFeedback();

		return async ({ result, update }) => {
			isSubmitting = false;
			await update({ invalidateAll: result.type === 'success' });
			if (result.type === 'error') {
				formError = 'Não foi possível excluir o registro.';
			}
		};
	};

	$effect(() => {
		if (!actionResult) return;

		if (actionResult.action === 'createPredio' || actionResult.action === 'updatePredio') {
			if (actionResult.success) {
				isPredioModalOpen = false;
				editingPredioId = null;
				predioNome = '';
				predioEndereco = '';
				formError = '';
				return;
			}

			if (actionResult.error) formError = actionResult.error;
			if (actionResult.fieldValues) {
				if (typeof actionResult.fieldValues.predioNome === 'string') {
					predioNome = actionResult.fieldValues.predioNome;
				}
				if (typeof actionResult.fieldValues.predioEndereco === 'string') {
					predioEndereco = actionResult.fieldValues.predioEndereco;
				}
			}
			isPredioModalOpen = true;
			return;
		}

		if (actionResult.action === 'createCamara' || actionResult.action === 'updateCamara') {
			if (actionResult.success) {
				isCamaraModalOpen = false;
				editingCamaraId = null;
				camaraPredioId = '';
				camaraNome = '';
				camaraCapacidade = '';
				formError = '';
				return;
			}

			if (actionResult.error) formError = actionResult.error;
			if (actionResult.fieldValues) {
				if (typeof actionResult.fieldValues.camaraPredioId === 'string') {
					camaraPredioId = actionResult.fieldValues.camaraPredioId;
				}
				if (typeof actionResult.fieldValues.camaraNome === 'string') {
					camaraNome = actionResult.fieldValues.camaraNome;
				}
				if (typeof actionResult.fieldValues.camaraCapacidade === 'string') {
					camaraCapacidade = actionResult.fieldValues.camaraCapacidade;
				}
			}
			isCamaraModalOpen = true;
			return;
		}

		if (actionResult.action === 'createSensor' || actionResult.action === 'updateSensor') {
			if (actionResult.success) {
				isSensorModalOpen = false;
				editingSensorId = null;
				sensorCamaraId = '';
				sensorModelo = 'PN5180';
				sensorAtivo = true;
				formError = '';
				return;
			}

			if (actionResult.error) formError = actionResult.error;
			if (actionResult.fieldValues) {
				if (typeof actionResult.fieldValues.sensorCamaraId === 'string') {
					sensorCamaraId = actionResult.fieldValues.sensorCamaraId;
				}
				if (typeof actionResult.fieldValues.sensorModelo === 'string') {
					sensorModelo = actionResult.fieldValues.sensorModelo;
				}
				if (typeof actionResult.fieldValues.sensorAtivo === 'boolean') {
					sensorAtivo = actionResult.fieldValues.sensorAtivo;
				}
			}
			isSensorModalOpen = true;
			return;
		}

		if (actionResult.error) {
			formError = actionResult.error;
		}
	});
</script>

<div class="main-content p-8">
	<div class="header">
		<h1>Infraestrutura</h1>
		<p>Gestão de recursos físicos, câmaras e dispositivos de leitura.</p>
	</div>
	{#if data.error}
		<div class="mt-4 rounded-lg bg-red-100 p-4 text-center text-red-700">
			{data.error}
		</div>
	{/if}

	{#if formError && !isPredioModalOpen && !isCamaraModalOpen && !isSensorModalOpen}
		<div class="mt-4 rounded-lg bg-red-100 p-4 text-center text-red-700">
			{formError}
		</div>
	{/if}

	{#if infraestrutura}
		<div class="hidden">
			{#each infraestrutura.lista_predios || [] as predio}
				<form
					method="POST"
					action="?/deletePredio"
					bind:this={deletePredioForms[predio.id]}
					use:enhance={handleDeleteSubmit}
				>
					<input type="hidden" name="predioId" value={predio.id} />
				</form>
			{/each}
			{#each infraestrutura.lista_camaras || [] as camara}
				<form
					method="POST"
					action="?/deleteCamara"
					bind:this={deleteCamaraForms[camara.id]}
					use:enhance={handleDeleteSubmit}
				>
					<input type="hidden" name="camaraId" value={camara.id} />
				</form>
			{/each}
			{#each infraestrutura.lista_sensores || [] as sensor}
				<form
					method="POST"
					action="?/deleteSensor"
					bind:this={deleteSensorForms[sensor.id]}
					use:enhance={handleDeleteSubmit}
				>
					<input type="hidden" name="sensorId" value={sensor.id} />
				</form>
			{/each}
		</div>

		<div class="mt-8 mb-8 grid grid-cols-1 gap-8 md:grid-cols-4">
			<InfoCard
				title={deviceStatus.ip_address || 'N/A'}
				description="Status de conexão do microcontrolador"
				value="Dispositivo Fabritag"
			>
				{#snippet badge()}
					<Badge border large color={deviceStatus.status === 'Online' ? 'green' : 'red'}>
						{deviceStatus.status}
					</Badge>
				{/snippet}
			</InfoCard>
			<InfoCard
				data-variant="Up"
				title={infraestrutura.total_predios === 1 ? 'Prédio' : 'Prédios'}
				description="Unidades físicas cadastradas"
				value={infraestrutura.total_predios}
			/>
			<InfoCard
				data-variant="Up"
				title={infraestrutura.total_camaras === 1 ? 'Câmara' : 'Câmaras'}
				description="Setores de monitoramento"
				value={infraestrutura.total_camaras}
			/>
			<InfoCard
				data-variant="Up"
				title={infraestrutura.total_sensores === 1 ? 'Sensor' : 'Sensores'}
				description="Total de dispositivos RFID"
				value={infraestrutura.total_sensores}
			/>
		</div>

		<div class="mb-6 border-b border-gray-200" role="tablist" aria-label="Seções de infraestrutura">
			<div class="-mb-px flex flex-wrap gap-6">
				<button
					type="button"
					role="tab"
					aria-selected={activeSection === 'todos'}
					class={`border-b-2 px-1 pb-2 text-sm font-medium ${activeSection === 'todos' ? 'border-orange-700 text-orange-700' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
					onclick={() => (activeSection = 'todos')}
				>
					Todos
				</button>
				<button
					type="button"
					role="tab"
					aria-selected={activeSection === 'predios'}
					class={`border-b-2 px-1 pb-2 text-sm font-medium ${activeSection === 'predios' ? 'border-orange-700 text-orange-700' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
					onclick={() => (activeSection = 'predios')}
				>
					Prédios
				</button>
				<button
					type="button"
					role="tab"
					aria-selected={activeSection === 'camaras'}
					class={`border-b-2 px-1 pb-2 text-sm font-medium ${activeSection === 'camaras' ? 'border-orange-700 text-orange-700' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
					onclick={() => (activeSection = 'camaras')}
				>
					Câmaras
				</button>
				<button
					type="button"
					role="tab"
					aria-selected={activeSection === 'sensores'}
					class={`border-b-2 px-1 pb-2 text-sm font-medium ${activeSection === 'sensores' ? 'border-orange-700 text-orange-700' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
					onclick={() => (activeSection = 'sensores')}
				>
					Sensores
				</button>
			</div>
		</div>

		{#if activeSection === 'todos'}
			<div class="mb-4 flex items-center justify-between">
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white">Visão Geral por Câmara</h2>
			</div>

			<TableSearch
				placeholder="Buscar por câmara, prédio, sensores ou status..."
				hoverable={true}
				bind:inputValue={searchTermAll}
				divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
				innerDivClass="flex flex-col items-start justify-between gap-4 p-4 md:flex-row md:flex-wrap"
				searchClass="w-full md:w-1/2"
			>
				<TableHead>
					<TableHeadCell>Câmara</TableHeadCell>
					<TableHeadCell>Prédio</TableHeadCell>
					<TableHeadCell>Sensores</TableHeadCell>
				</TableHead>
				<TableBody>
					{#each filteredAllTableRows as row}
						<TableBodyRow>
							<TableBodyCell>
								<a
									href={`/infraestrutura/camaras/${row.id}`}
									class="flex items-center gap-2 font-medium hover:underline dark:text-white"
								>
									{row.camara}
									<ChevronRightOutline class="h-4 w-4 text-gray-400" />
								</a>
							</TableBodyCell>
							<TableBodyCell>{row.predio}</TableBodyCell>
							<TableBodyCell>{row.total_sensores}</TableBodyCell>
						</TableBodyRow>
					{:else}
						<TableBodyRow>
							<TableBodyCell colspan={4} class="py-4 text-center text-gray-500">
								Nenhuma câmara encontrada para "{searchTermAll}".
							</TableBodyCell>
						</TableBodyRow>
					{/each}
				</TableBody>
			</TableSearch>
		{:else if activeSection === 'predios'}
			<InfraPrediosSection
				bind:searchTermPredios
				{filteredPredios}
				onOpenModal={openPredioModal}
				onEditPredio={handleEditPredio}
				onDeletePredio={handleDeletePredio}
			/>
		{:else if activeSection === 'camaras'}
			<InfraCamarasSection
				bind:searchTermCamaras
				{filteredCamaras}
				onOpenModal={openCamaraModal}
				onEditCamara={handleEditCamara}
				onDeleteCamara={handleDeleteCamara}
			/>
		{:else}
			<InfraSensoresSection
				bind:searchTerm
				{filteredItems}
				onOpenModal={openSensorModal}
				onEditSensor={handleEdit}
				onDeleteSensor={handleDeleteSensor}
			/>
		{/if}

		<InfraCreateModals
			bind:isPredioModalOpen
			bind:isCamaraModalOpen
			bind:isSensorModalOpen
			{isSubmitting}
			{formError}
			{predioModalTitle}
			{camaraModalTitle}
			{sensorModalTitle}
			{predioSubmitLabel}
			{camaraSubmitLabel}
			{sensorSubmitLabel}
			bind:predioNome
			bind:predioEndereco
			bind:camaraPredioId
			bind:camaraNome
			bind:camaraCapacidade
			bind:sensorCamaraId
			bind:sensorModelo
			bind:sensorAtivo
			{editingPredioId}
			{editingCamaraId}
			{editingSensorId}
			predios={infraestrutura.lista_predios}
			camaras={infraestrutura.lista_camaras}
			{predioFormAction}
			{camaraFormAction}
			{sensorFormAction}
			onEnhancePredio={handleInfraSubmit}
			onEnhanceCamara={handleInfraSubmit}
			onEnhanceSensor={handleInfraSubmit}
		/>
	{/if}
</div>

<style>
	h1 {
		font-size: 24px;
		font-family: Inter;
		font-weight: 700;
		line-height: 34px;
		word-wrap: break-word;
	}
	p {
		color: var(--Text-Neutral-Neutral-900, #383e41);
		font-size: 12px;
		font-family: Inter;
		font-weight: 400;
		line-height: 18px;
		word-wrap: break-word;
	}

	.header {
		width: 100%;
		justify-content: center;
		display: flex;
		flex-direction: column;
	}

	:global(ul),
	:global(li) {
		list-style-type: none !important;
	}
</style>
