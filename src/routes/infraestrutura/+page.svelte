<script lang="ts">
	import { onMount } from 'svelte';
	import { invalidateAll } from '$app/navigation';
	import InfoCard from '$lib/components/InfoCard.svelte';
	import { sensorStore } from '$lib/dispositivos.svelte.js';
	import {
		Badge,
		TableSearch,
		TableHead,
		TableHeadCell,
		TableBody,
		TableBodyRow,
		TableBodyCell
	} from '$lib/uicomponents.js';
	import InfraPrediosSection from './InfraPrediosSection.svelte';
	import InfraCamarasSection from './InfraCamarasSection.svelte';
	import InfraSensoresSection from './InfraSensoresSection.svelte';
	import InfraCreateModals from './InfraCreateModals.svelte';

	let { data } = $props();
	let infraestrutura = $derived(data.infraestrutura);
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

	let allTableRows = $derived(
		(infraestrutura?.lista_camaras || []).map((camara) => ({
			camara: camara.nome,
			predio: camara.predio,
			total_sensores: Number(camara.total_sensores || 0),
			status: camara.sensores_ativos > 0 ? 'Ativa' : 'Inativa'
		}))
	);

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

	onMount(() => {
		sensorStore.setInitial(data.liveStatuses || {});
		const stopPolling = sensorStore.startPolling();
		return () => stopPolling;
	});

	async function runInfraMutation(url: string, options: RequestInit, fallbackError: string) {
		resetFeedback();
		isSubmitting = true;

		try {
			const response = await fetch(url, options);
			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.error || fallbackError);
			}
			await invalidateAll();
			return true;
		} catch (error) {
			formError = error instanceof Error ? error.message : fallbackError;
			return false;
		} finally {
			isSubmitting = false;
		}
	}

	function handleEditPredio(predioId: number) {
		const predio = infraestrutura?.lista_predios?.find((item) => item.id === predioId);
		if (!predio) return;

		resetFeedback();
		editingPredioId = predioId;
		predioNome = predio.nome || '';
		predioEndereco = predio.endereco === '-' ? '' : (predio.endereco ?? '');
		isPredioModalOpen = true;
	}

	async function handleDeletePredio(predioId: number) {
		if (!window.confirm('Tem certeza que deseja excluir este prédio?')) return;

		await runInfraMutation(
			`http://127.0.0.1:5000/api/predios/${predioId}`,
			{ method: 'DELETE' },
			'Não foi possível excluir o prédio.'
		);
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

	async function handleDeleteCamara(camaraId: number) {
		if (!window.confirm('Tem certeza que deseja excluir esta câmara?')) return;

		await runInfraMutation(
			`http://127.0.0.1:5000/api/camaras/${camaraId}`,
			{ method: 'DELETE' },
			'Não foi possível excluir a câmara.'
		);
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

	async function handleDeleteSensor(sensorId: number) {
		if (!window.confirm('Tem certeza que deseja excluir este sensor?')) return;

		await runInfraMutation(
			`http://127.0.0.1:5000/api/sensores/${sensorId}`,
			{ method: 'DELETE' },
			'Não foi possível excluir o sensor.'
		);
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

	async function createPredio(event: SubmitEvent) {
		event.preventDefault();
		resetFeedback();
		isSubmitting = true;

		try {
			const response = await fetch('http://127.0.0.1:5000/api/predios', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					nome: predioNome,
					endereco: predioEndereco || null
				})
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.error || 'Não foi possível criar o prédio.');
			}

			isPredioModalOpen = false;
			await invalidateAll();
		} catch (error) {
			formError = error instanceof Error ? error.message : 'Erro ao criar prédio.';
		} finally {
			isSubmitting = false;
		}
	}

	async function updatePredio(event: SubmitEvent) {
		event.preventDefault();
		if (!editingPredioId) return;
		if (!predioNome.trim()) {
			formError = 'O nome do prédio é obrigatório.';
			return;
		}

		const success = await runInfraMutation(
			`http://127.0.0.1:5000/api/predios/${editingPredioId}`,
			{
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					nome: predioNome.trim(),
					endereco: predioEndereco.trim() ? predioEndereco.trim() : null
				})
			},
			'Não foi possível atualizar o prédio.'
		);

		if (success) {
			isPredioModalOpen = false;
			editingPredioId = null;
		}
	}

	async function createCamara(event: SubmitEvent) {
		event.preventDefault();
		resetFeedback();
		isSubmitting = true;

		try {
			const response = await fetch('http://127.0.0.1:5000/api/camaras', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					predio_id: Number(camaraPredioId),
					nome: camaraNome,
					capacidade_vagas: camaraCapacidade ? Number(camaraCapacidade) : null
				})
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.error || 'Não foi possível criar a câmara.');
			}

			isCamaraModalOpen = false;
			await invalidateAll();
		} catch (error) {
			formError = error instanceof Error ? error.message : 'Erro ao criar câmara.';
		} finally {
			isSubmitting = false;
		}
	}

	async function updateCamara(event: SubmitEvent) {
		event.preventDefault();
		if (!editingCamaraId) return;
		if (!camaraPredioId || !camaraNome.trim()) {
			formError = 'Preencha os campos obrigatórios da câmara.';
			return;
		}

		const capacidade = camaraCapacidade.trim() ? Number(camaraCapacidade) : null;
		if (camaraCapacidade.trim() && (!Number.isInteger(capacidade) || Number(capacidade) < 0)) {
			formError = 'Informe uma capacidade válida.';
			return;
		}

		const success = await runInfraMutation(
			`http://127.0.0.1:5000/api/camaras/${editingCamaraId}`,
			{
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					predio_id: Number(camaraPredioId),
					nome: camaraNome.trim(),
					capacidade_vagas: capacidade
				})
			},
			'Não foi possível atualizar a câmara.'
		);

		if (success) {
			isCamaraModalOpen = false;
			editingCamaraId = null;
		}
	}

	async function createSensor(event: SubmitEvent) {
		event.preventDefault();
		resetFeedback();
		isSubmitting = true;

		try {
			const response = await fetch('http://127.0.0.1:5000/api/sensores', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					camara_id: Number(sensorCamaraId),
					modelo: sensorModelo || 'PN5180',
					ativo: sensorAtivo
				})
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.error || 'Não foi possível criar o sensor.');
			}

			isSensorModalOpen = false;
			await invalidateAll();
		} catch (error) {
			formError = error instanceof Error ? error.message : 'Erro ao criar sensor.';
		} finally {
			isSubmitting = false;
		}
	}

	async function updateSensor(event: SubmitEvent) {
		event.preventDefault();
		if (!editingSensorId) return;
		if (!sensorCamaraId) {
			formError = 'Selecione a câmara do sensor.';
			return;
		}

		const success = await runInfraMutation(
			`http://127.0.0.1:5000/api/sensores/${editingSensorId}`,
			{
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					camara_id: Number(sensorCamaraId),
					modelo: sensorModelo.trim() || 'PN5180',
					ativo: sensorAtivo
				})
			},
			'Não foi possível atualizar o sensor.'
		);

		if (success) {
			isSensorModalOpen = false;
			editingSensorId = null;
		}
	}

	async function submitPredioForm(event: SubmitEvent) {
		if (editingPredioId) {
			await updatePredio(event);
			return;
		}
		await createPredio(event);
	}

	async function submitCamaraForm(event: SubmitEvent) {
		if (editingCamaraId) {
			await updateCamara(event);
			return;
		}
		await createCamara(event);
	}

	async function submitSensorForm(event: SubmitEvent) {
		if (editingSensorId) {
			await updateSensor(event);
			return;
		}
		await createSensor(event);
	}
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

	{#if infraestrutura}
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
							<TableBodyCell>{row.camara}</TableBodyCell>
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
			predios={infraestrutura.lista_predios}
			camaras={infraestrutura.lista_camaras}
			onSubmitPredio={submitPredioForm}
			onSubmitCamara={submitCamaraForm}
			onSubmitSensor={submitSensorForm}
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
