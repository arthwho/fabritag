<script lang="ts">
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
		PlusOutline,
		ChevronDownOutline,
		TrashBinOutline,
		Dropdown,
		DropdownItem,
		DropdownDivider,
		DropdownHeader,
		EditOutline
	} from '$lib/uicomponents.js';
	import TableActions from '$lib/components/TableActions.svelte';

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
		onOpenModal,
		onEditSensor
	}: {
		filteredItems?: SensorRow[];
		searchTerm?: string;
		onOpenModal: () => void;
		onEditSensor: (sensorId: number) => void;
	} = $props();
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
			<TableBodyRow>
				<TableBodyCell class="p-4!"><Checkbox /></TableBodyCell>
				<TableBodyCell>{sensor.id}</TableBodyCell>
				<TableBodyCell>{sensor.modelo}</TableBodyCell>
				<TableBodyCell>{sensor.ip}</TableBodyCell>
				<TableBodyCell>{sensor.camara}</TableBodyCell>
				<TableBodyCell>
					<Badge border large color={sensor.status === 'Ativo' ? 'green' : 'red'}
						>{sensor.status}</Badge
					>
				</TableBodyCell>
				<TableBodyCell class="flex gap-2">
					<Button id={`sensor-actions-button-${sensor.id}`} outline color="dark" size="xs"
						>Ações <ChevronDownOutline class="ml-1 h-4 w-4" /></Button
					>
					<Dropdown triggeredBy={`#sensor-actions-button-${sensor.id}`}>
						<DropdownHeader>Ações do sensor</DropdownHeader>
						<DropdownItem onclick={() => onEditSensor(sensor.id)}>
							<EditOutline class="mr-2 h-4 w-4" />Editar
						</DropdownItem>
						<DropdownDivider />
						<DropdownItem class="text-red-600">
							<TrashBinOutline class="mr-2 h-4 w-4" />Excluir
						</DropdownItem>
					</Dropdown>
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
