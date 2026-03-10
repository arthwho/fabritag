<script lang="ts">
	import {
		TableSearch,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Alert,
		InfoCircleSolid
	} from '$lib/uicomponents.js';
	import InfoCard from '$lib/components/InfoCard.svelte';
	import { fly } from 'svelte/transition';

	let { data } = $props();

	let produtos = $derived(data.produtos || []);
	let lotes = $derived(data.lotes || []);
	let lotesSemProduto = $derived(data.lotesSemProduto || []);
	let activeSection = $state<'produtos' | 'lotes'>('produtos');
	let searchProdutos = $state('');
	let searchLotes = $state('');

	const normalize = (str: string) =>
		str
			.toString()
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '');

	let filteredProdutos = $derived(
		produtos.filter((item) => {
			const search = normalize(searchProdutos);
			return Object.values(item).some((val) => normalize((val ?? '').toString()).includes(search));
		})
	);

	let filteredLotes = $derived(
		lotes.filter((item) => {
			const search = normalize(searchLotes);
			return Object.values(item).some((val) => normalize((val ?? '').toString()).includes(search));
		})
	);
</script>

<div class="main-content p-8">
	<div class="header">
		<h1>Produtos</h1>
		<p>Visão geral dos produtos e lotes cadastrados.</p>
	</div>
	{#if data.error}
		<Alert class="mt-8">
			{#snippet icon()}<InfoCircleSolid class="h-4 w-4" />{/snippet}
			{data.error}
		</Alert>
	{/if}

	{#if lotesSemProduto.length > 0}
		<Alert dismissable transition={fly} class="mt-8">
			{#snippet icon()}<InfoCircleSolid class="h-4 w-4" />{/snippet}
			<div class="font-medium">
				{lotesSemProduto.length} lote(s) encontrados sem vínculo com PRODUTO_TIPO.
			</div>
		</Alert>
	{/if}

	<div class="mt-8 mb-8 grid grid-cols-1 gap-8 md:grid-cols-2">
		<InfoCard
			data-variant="Up"
			title="Total de produtos"
			description="Total de produtos no banco de dados"
			value={produtos.length}
		/>
		<InfoCard
			data-variant="Up"
			title="Total de lotes"
			description="Total de lotes no banco de dados"
			value={lotes.length}
		/>
	</div>

	<div class="mb-6 border-b border-gray-200" role="tablist" aria-label="Seções de produtos">
		<div class="-mb-px flex flex-wrap gap-6">
			<button
				type="button"
				role="tab"
				aria-selected={activeSection === 'produtos'}
				class={`border-b-2 px-1 pb-2 text-sm font-medium ${activeSection === 'produtos' ? 'border-orange-700 text-orange-700' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
				onclick={() => (activeSection = 'produtos')}
			>
				Produtos
			</button>
			<button
				type="button"
				role="tab"
				aria-selected={activeSection === 'lotes'}
				class={`border-b-2 px-1 pb-2 text-sm font-medium ${activeSection === 'lotes' ? 'border-orange-700 text-orange-700' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
				onclick={() => (activeSection = 'lotes')}
			>
				Lotes
			</button>
		</div>
	</div>

	{#if activeSection === 'produtos'}
		<TableSearch
			placeholder="Buscar por ID, cliente, nome, SKU ou unidade..."
			hoverable={true}
			bind:inputValue={searchProdutos}
			divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
			innerDivClass="flex flex-col md:flex-row md:flex-wrap items-start justify-between p-4 gap-4"
			searchClass="w-full md:w-1/2"
		>
			<TableHead>
				<TableHeadCell>ID</TableHeadCell>
				<TableHeadCell>Cliente ID</TableHeadCell>
				<TableHeadCell>Nome</TableHeadCell>
				<TableHeadCell>SKU</TableHeadCell>
				<TableHeadCell>Unidade</TableHeadCell>
				<TableHeadCell>Total de Lotes</TableHeadCell>
			</TableHead>
			<TableBody>
				{#each filteredProdutos as produto}
					<TableBodyRow>
						<TableBodyCell>{produto.id}</TableBodyCell>
						<TableBodyCell>{produto.cliente_id ?? '-'}</TableBodyCell>
						<TableBodyCell>{produto.nome}</TableBodyCell>
						<TableBodyCell>{produto.sku || '-'}</TableBodyCell>
						<TableBodyCell>{produto.unidade_medida || '-'}</TableBodyCell>
						<TableBodyCell>{produto.total_lotes ?? 0}</TableBodyCell>
					</TableBodyRow>
				{:else}
					<TableBodyRow>
						<TableBodyCell colspan={6} class="py-4 text-center text-gray-500">
							Nenhum produto encontrado para "{searchProdutos}".
						</TableBodyCell>
					</TableBodyRow>
				{/each}
			</TableBody>
		</TableSearch>
	{:else}
		<TableSearch
			placeholder="Buscar por EPC tag, produto, status ou quantidade..."
			hoverable={true}
			bind:inputValue={searchLotes}
			divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
			innerDivClass="flex flex-col md:flex-row md:flex-wrap items-start justify-between p-4 gap-4"
			searchClass="w-full md:w-1/2"
		>
			<TableHead>
				<TableHeadCell>EPC Tag</TableHeadCell>
				<TableHeadCell>Produto Tipo ID</TableHeadCell>
				<TableHeadCell>Produto</TableHeadCell>
				<TableHeadCell>Quantidade</TableHeadCell>
				<TableHeadCell>Local atual</TableHeadCell>
				<TableHeadCell>Desde</TableHeadCell>
			</TableHead>
			<TableBody>
				{#each filteredLotes as lote}
					<TableBodyRow>
						<TableBodyCell>{lote.epc_tag || lote.id}</TableBodyCell>
						<TableBodyCell>{lote.produto_tipo_id ?? '-'}</TableBodyCell>
						<TableBodyCell>{lote.produto_nome || lote.nome || '-'}</TableBodyCell>
						<TableBodyCell>{lote.quantidade_atual ?? '-'}</TableBodyCell>
						<TableBodyCell>{lote.local_atual || '-'}</TableBodyCell>
						<TableBodyCell>{lote.local_desde || '-'}</TableBodyCell>
					</TableBodyRow>
				{:else}
					<TableBodyRow>
						<TableBodyCell colspan={6} class="py-4 text-center text-gray-500">
							Nenhum lote encontrado para "{searchLotes}".
						</TableBodyCell>
					</TableBodyRow>
				{/each}
			</TableBody>
		</TableSearch>
	{/if}
</div>
