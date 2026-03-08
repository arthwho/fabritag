<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import InfoCard from '$lib/components/InfoCard.svelte';
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
	let searchTermAll = $state('');
	let searchTermPredios = $state('');
	let searchTermCamaras = $state('');
	let searchTerm = $state('');
	let activeSection = $state<'todos' | 'predios' | 'camaras' | 'sensores'>('todos');

	let isPredioModalOpen = $state(false);
	let isCamaraModalOpen = $state(false);
	let isSensorModalOpen = $state(false);
	let isSubmitting = $state(false);
	let formError = $state('');

	let predioNome = $state('');
	let predioEndereco = $state('');

	let camaraPredioId = $state('');
	let camaraNome = $state('');
	let camaraCapacidade = $state('');

	let sensorCamaraId = $state('');
	let sensorModelo = $state('PN5180');
	let sensorIpAddress = $state('');
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

	function handleEdit(sensorId: number) {
		console.log(`Editando sensor: ${sensorId}`);
		// Lógica de edição será implementada aqui
	}

	function handleEditPredio(predioId: number) {
		console.log(`Editando prédio: ${predioId}`);
		// Lógica de edição será implementada aqui
	}

	function handleEditCamara(camaraId: number) {
		console.log(`Editando câmara: ${camaraId}`);
		// Lógica de edição será implementada aqui
	}

	function resetFeedback() {
		formError = '';
	}

	function openPredioModal() {
		resetFeedback();
		predioNome = '';
		predioEndereco = '';
		isPredioModalOpen = true;
	}

	function openCamaraModal() {
		resetFeedback();
		camaraPredioId = infraestrutura?.lista_predios?.[0]?.id?.toString() || '';
		camaraNome = '';
		camaraCapacidade = '';
		isCamaraModalOpen = true;
	}

	function openSensorModal() {
		resetFeedback();
		sensorCamaraId = infraestrutura?.lista_camaras?.[0]?.id?.toString() || '';
		sensorModelo = 'PN5180';
		sensorIpAddress = '';
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
					ip_address: sensorIpAddress || null,
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
			<InfoCard
				data-variant="Up"
				title={infraestrutura.sensores_ativos === 1 ? 'Sensor Ativo' : 'Sensores Ativos'}
				description="Dispositivos em operação"
				value={infraestrutura.sensores_ativos}
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
					<TableHeadCell>Status</TableHeadCell>
				</TableHead>
				<TableBody>
					{#each filteredAllTableRows as row}
						<TableBodyRow>
							<TableBodyCell>{row.camara}</TableBodyCell>
							<TableBodyCell>{row.predio}</TableBodyCell>
							<TableBodyCell>{row.total_sensores}</TableBodyCell>
							<TableBodyCell>
								<Badge border large color={row.status === 'Ativa' ? 'green' : 'red'}>
									{row.status}
								</Badge>
							</TableBodyCell>
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
			/>
		{:else if activeSection === 'camaras'}
			<InfraCamarasSection
				bind:searchTermCamaras
				{filteredCamaras}
				onOpenModal={openCamaraModal}
				onEditCamara={handleEditCamara}
			/>
		{:else}
			<InfraSensoresSection
				bind:searchTerm
				{filteredItems}
				onOpenModal={openSensorModal}
				onEditSensor={handleEdit}
			/>
		{/if}

		<InfraCreateModals
			bind:isPredioModalOpen
			bind:isCamaraModalOpen
			bind:isSensorModalOpen
			{isSubmitting}
			{formError}
			bind:predioNome
			bind:predioEndereco
			bind:camaraPredioId
			bind:camaraNome
			bind:camaraCapacidade
			bind:sensorCamaraId
			bind:sensorModelo
			bind:sensorIpAddress
			bind:sensorAtivo
			predios={infraestrutura.lista_predios}
			camaras={infraestrutura.lista_camaras}
			onCreatePredio={createPredio}
			onCreateCamara={createCamara}
			onCreateSensor={createSensor}
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
