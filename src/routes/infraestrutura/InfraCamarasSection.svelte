<script lang="ts">
	import {
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Checkbox,
		TableSearch,
		Button,
		PlusOutline,
		ChevronRightOutline
	} from '$lib/uicomponents.js';
	import TableActions from '$lib/components/TableActions.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';

	type CamaraRow = {
		id: number;
		nome: string;
		predio: string;
		capacidade_vagas: number | null;
		total_sensores: number;
		sensores_ativos: number;
	};

	let {
		filteredCamaras = [],
		searchTermCamaras = $bindable(''),
		onOpenModal,
		onEditCamara,
		onDeleteCamara
	}: {
		filteredCamaras?: CamaraRow[];
		searchTermCamaras?: string;
		onOpenModal: () => void;
		onEditCamara: (camaraId: number) => void | Promise<void>;
		onDeleteCamara: (camaraId: number) => void | Promise<void>;
	} = $props();
</script>

<div class="mb-4 flex items-center justify-between">
	<h2 class="h1 text-gray-900 dark:text-white">Câmaras Cadastradas</h2>
	<Button color="orange" onclick={onOpenModal}>
		<PlusOutline class="mr-2 w-4" />
		Adicionar Câmara
	</Button>
</div>

<TableSearch
	placeholder="Buscar por ID, nome, prédio ou capacidade..."
	hoverable={true}
	bind:inputValue={searchTermCamaras}
	divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
	innerDivClass="flex flex-col md:flex-row md:flex-wrap items-start justify-between p-4 gap-4"
	searchClass="w-full md:w-1/2"
>
	{#snippet header()}
		<TableActions
			idPrefix="infra-camaras"
			filterOptions={['Todos', 'Com sensores ativos', 'Sem sensores ativos']}
		/>
	{/snippet}
	<TableHead>
		<TableHeadCell class="p-4!"><Checkbox /></TableHeadCell>
		<TableHeadCell>ID</TableHeadCell>
		<TableHeadCell>Nome</TableHeadCell>
		<TableHeadCell>Prédio</TableHeadCell>
		<TableHeadCell>Capacidade</TableHeadCell>
		<TableHeadCell>Sensores</TableHeadCell>
		<TableHeadCell>Ações</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each filteredCamaras as camara}
			<TableBodyRow>
				<TableBodyCell class="p-4!"><Checkbox /></TableBodyCell>
				<TableBodyCell>{camara.id}</TableBodyCell>
				<TableBodyCell>
					<a
						href={`/infraestrutura/camaras/${camara.id}`}
						class="flex items-center gap-2 font-medium hover:underline dark:text-white"
					>
						{camara.nome}
						<ChevronRightOutline class="h-4 w-4 text-gray-400" />
					</a>
				</TableBodyCell>
				<TableBodyCell>{camara.predio}</TableBodyCell>
				<TableBodyCell>{camara.capacidade_vagas}</TableBodyCell>
				<TableBodyCell>{camara.total_sensores}</TableBodyCell>
				<TableBodyCell class="flex gap-2">
					<RowActionsMenu
						menuId={`camara-actions-button-${camara.id}`}
						headerLabel="Ações da câmara"
						onEdit={() => onEditCamara(camara.id)}
						onDelete={() => onDeleteCamara(camara.id)}
					/>
				</TableBodyCell>
			</TableBodyRow>
		{:else}
			<TableBodyRow>
				<TableBodyCell colspan={8} class="text-center py-4 text-gray-500">
					Nenhuma câmara encontrada para "{searchTermCamaras}".
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
