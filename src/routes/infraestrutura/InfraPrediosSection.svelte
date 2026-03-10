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
		PlusOutline
	} from '$lib/uicomponents.js';
	import TableActions from '$lib/components/TableActions.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';

	type PredioRow = {
		id: number;
		nome: string;
		endereco: string;
		total_camaras: number;
	};

	let {
		filteredPredios = [],
		searchTermPredios = $bindable(''),
		onOpenModal,
		onEditPredio,
		onDeletePredio
	}: {
		filteredPredios?: PredioRow[];
		searchTermPredios?: string;
		onOpenModal: () => void;
		onEditPredio: (predioId: number) => void | Promise<void>;
		onDeletePredio: (predioId: number) => void | Promise<void>;
	} = $props();
</script>

<div class="mb-4 flex items-center justify-between">
	<h2 class="h1 text-gray-900 dark:text-white">Prédios Cadastrados</h2>
	<Button color="orange" onclick={onOpenModal}>
		<PlusOutline class="mr-2 w-4" />
		Adicionar Prédio
	</Button>
</div>

<TableSearch
	placeholder="Buscar por ID, nome ou endereço..."
	hoverable={true}
	bind:inputValue={searchTermPredios}
	divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
	innerDivClass="flex flex-col md:flex-row md:flex-wrap items-start justify-between p-4 gap-4"
	searchClass="w-full md:w-1/2"
>
	{#snippet header()}
		<TableActions
			idPrefix="infra-predios"
			filterOptions={['Todos', 'Com câmaras', 'Sem câmaras']}
		/>
	{/snippet}
	<TableHead>
		<TableHeadCell class="p-4!"><Checkbox /></TableHeadCell>
		<TableHeadCell>ID</TableHeadCell>
		<TableHeadCell>Nome</TableHeadCell>
		<TableHeadCell>Endereço</TableHeadCell>
		<TableHeadCell>Câmaras</TableHeadCell>
		<TableHeadCell>Ações</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each filteredPredios as predio}
			<TableBodyRow>
				<TableBodyCell class="p-4!"><Checkbox /></TableBodyCell>
				<TableBodyCell>{predio.id}</TableBodyCell>
				<TableBodyCell>{predio.nome}</TableBodyCell>
				<TableBodyCell>{predio.endereco}</TableBodyCell>
				<TableBodyCell>{predio.total_camaras}</TableBodyCell>
				<TableBodyCell class="flex gap-2">
					<RowActionsMenu
						menuId={`predio-actions-button-${predio.id}`}
						headerLabel="Ações do prédio"
						onEdit={() => onEditPredio(predio.id)}
						onDelete={() => onDeletePredio(predio.id)}
					/>
				</TableBodyCell>
			</TableBodyRow>
		{:else}
			<TableBodyRow>
				<TableBodyCell colspan={6} class="text-center py-4 text-gray-500">
					Nenhum prédio encontrado para "{searchTermPredios}".
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
