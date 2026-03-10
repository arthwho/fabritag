<script lang="ts">
	import { onMount } from 'svelte';
	import {
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Checkbox,
		TableSearch,
		Badge,
		Button,
		PlusOutline
	} from '$lib/uicomponents.js';
	import TableActions from '$lib/components/TableActions.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';

	import { sensorStore } from '$lib/sensors.svelte.js';

	type SensorRow = {
		id: number;
		modelo: string;
		ip: string | null;
		camara: string;
		status: string;
	};

	let {
		filteredItems = [],
		searchTerm = $bindable(''),
		liveStatuses: initialLiveStatuses = {},
		onOpenModal,
		onEditSensor,
		onDeleteSensor
	}: {
		filteredItems?: SensorRow[];
		searchTerm?: string;
		liveStatuses?: Record<string, { status: string; ip_address: string }>;
		onOpenModal: () => void;
		onEditSensor: (sensorId: number) => void | Promise<void>;
		onDeleteSensor: (sensorId: number) => void | Promise<void>;
	} = $props();

	onMount(() => {
		// Set initial state from server data to avoid "Offline" flicker
		sensorStore.setInitial(initialLiveStatuses);

		const stopPolling = sensorStore.startPolling();
		return () => stopPolling;
	});

	function getStatus(sensor: SensorRow) {
		const live = sensorStore.liveStatuses[sensor.id.toString()];
		if (live) return live.status;
		return 'Offline';
	}

	function getIP(sensor: SensorRow) {
		const live = sensorStore.liveStatuses[sensor.id.toString()];
		if (live && live.ip_address) return live.ip_address;
		return sensor.ip || '-';
	}
</script>

<div class="mb-4 flex items-center justify-between">
	<h2 class="h1 text-gray-900 dark:text-white">Sensores Cadastrados</h2>
	<Button color="orange" onclick={onOpenModal}>
		<PlusOutline class="mr-2 w-4" />
		Adicionar Sensor
	</Button>
</div>

<TableSearch
	placeholder="Buscar por ID, modelo, IP ou câmara..."
	hoverable={true}
	bind:inputValue={searchTerm}
	divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
	innerDivClass="flex flex-col md:flex-row md:flex-wrap items-start justify-between p-4 gap-4"
	searchClass="w-full md:w-1/2"
>
	{#snippet header()}
		<TableActions idPrefix="infra-sensores" filterOptions={['Todos', 'Ativos', 'Inativos']} />
	{/snippet}
	<TableHead>
		<TableHeadCell class="p-4!"><Checkbox /></TableHeadCell>
		<TableHeadCell>ID</TableHeadCell>
		<TableHeadCell>Modelo</TableHeadCell>
		<TableHeadCell>IP</TableHeadCell>
		<TableHeadCell>Câmara</TableHeadCell>
		<TableHeadCell>Status</TableHeadCell>
		<TableHeadCell>Ações</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each filteredItems as sensor}
			{@const currentStatus = getStatus(sensor)}
			<TableBodyRow>
				<TableBodyCell class="p-4!"><Checkbox /></TableBodyCell>
				<TableBodyCell>{sensor.id}</TableBodyCell>
				<TableBodyCell>{sensor.modelo}</TableBodyCell>
				<TableBodyCell>{getIP(sensor)}</TableBodyCell>
				<TableBodyCell>{sensor.camara}</TableBodyCell>
				<TableBodyCell>
					<Badge border large color={currentStatus === 'Online' ? 'green' : 'red'}>
						{currentStatus}
					</Badge>
				</TableBodyCell>
				<TableBodyCell class="flex gap-2">
					<RowActionsMenu
						menuId={`sensor-actions-button-${sensor.id}`}
						headerLabel="Ações do sensor"
						onEdit={() => onEditSensor(sensor.id)}
						onDelete={() => onDeleteSensor(sensor.id)}
					/>
				</TableBodyCell>
			</TableBodyRow>
		{:else}
			<TableBodyRow>
				<TableBodyCell colspan={7} class="text-center py-4 text-gray-500">
					Nenhum sensor encontrado para "{searchTerm}".
				</TableBodyCell>
			</TableBodyRow>
		{/each}
	</TableBody>
</TableSearch>

<style>
	.h1 {
		font-size: 24px;
		font-family: Inter;
		font-weight: 700;
		line-height: 34px;
		word-wrap: break-word;
	}
</style>
