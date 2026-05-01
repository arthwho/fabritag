<script lang="ts">
	import { enhance } from '$app/forms';
	import {
		Button,
		Input,
		Label,
		Modal,
		Select,
		TableSearch,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Alert,
		InfoCircleSolid,
		PlusOutline
	} from '$lib/uicomponents.js';
	import InfoCard from '$lib/components/InfoCard.svelte';
	import TableActions from '$lib/components/TableActions.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';
	import type { SubmitFunction } from '@sveltejs/kit';
	import { fly } from 'svelte/transition';

	let { data, form } = $props();

	type ProdutoRow = {
		id: number;
		cliente_id: number | null;
		cliente_nome?: string;
		nome: string;
		sku: string | null;
		unidade_medida: string | null;
		total_lotes: number;
	};

	type ClienteOption = {
		id: number;
		nome: string;
		cpf_cnpj?: string | null;
	};

	type CamaraOption = {
		id: number;
		nome: string;
	};

	type LoteRow = {
		id?: string;
		epc_tag: string;
		produto_tipo_id: number | null;
		produto_tipo_ids?: number[];
		produto_nome: string | null;
		produto_nomes?: string[];
		produto_assoc?: Array<{
			produto_tipo_id: number;
			produto_nome: string;
			quantidade: number;
		}>;
		nome?: string;
		quantidade_atual: number | null;
		local_atual: string | null;
		local_desde: string | null;
	};

	type ActionResultPayload = {
		action?: 'createProduto' | 'updateProduto' | 'deleteProduto' | 'updateLote' | 'moveLote';
		success?: boolean;
		error?: string;
		fieldValues?: {
			clienteId?: string;
			nome?: string;
			sku?: string;
			unidadeMedida?: string;
			loteProdutoTipoIds?: string[];
			loteQuantidades?: Record<string, string>;
		};
	};

	let produtos = $derived((data.produtos || []) as ProdutoRow[]);
	let clientes = $derived((data.clientes || []) as ClienteOption[]);
	let camaras = $derived((data.camaras || []) as CamaraOption[]);
	let lotes = $derived((data.lotes || []) as LoteRow[]);
	let lotesSemProduto = $derived(data.lotesSemProduto || []);
	let activeSection = $state<'produtos' | 'lotes'>('produtos');
	let searchProdutos = $state('');
	let searchLotes = $state('');
	let isProdutoModalOpen = $state(false);
	let isLoteModalOpen = $state(false);
	let isMoveLoteModalOpen = $state(false);
	let editingProdutoId = $state<number | null>(null);
	let editingLoteEpcTag = $state('');
	let movingLoteEpcTag = $state('');
	let moveDestinoCamaraId = $state('');
	let isSubmitting = $state(false);
	let formError = $state('');
	let produtoClienteId = $state('');
	let produtoNome = $state('');
	let produtoSku = $state('');
	let produtoUnidadeMedida = $state('');
	let loteProdutoTipoIds = $state<string[]>([]);
	let loteProdutoSearch = $state('');
	let loteQuantidades = $state<Record<string, string>>({});
	let deleteProdutoForms = $state<Record<number, HTMLFormElement | undefined>>({});

	let actionResult = $derived((form || null) as ActionResultPayload | null);

	let produtoModalTitle = $derived(editingProdutoId ? 'Editar Produto' : 'Adicionar Produto');
	let produtoSubmitLabel = $derived(editingProdutoId ? 'Salvar alterações' : 'Salvar');
	let loteModalTitle = $derived('Editar Lote');
	let loteSubmitLabel = $derived('Salvar alterações');
	let moveLoteModalTitle = $derived('Movimentar lote');

	/** Normaliza texto para filtros sem acento e sem diferenciar maiúsculas. */
	const normalize = (str: string) =>
		str
			.toString()
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '');

	const unidadeMedidaOptions = [
		{ value: 'un', label: 'Unidade (un)' },
		{ value: 'm', label: 'Comprimento: Metro (m)' },
		{ value: 'km', label: 'Comprimento: Quilometro (km)' },
		{ value: 'cm', label: 'Comprimento: Centimetro (cm)' },
		{ value: 'mm', label: 'Comprimento: Milimetro (mm)' },
		{ value: 'kg', label: 'Massa: Quilograma (kg)' },
		{ value: 'g', label: 'Massa: Grama (g)' },
		{ value: 'mg', label: 'Massa: Miligrama (mg)' },
		{ value: 't', label: 'Massa: Tonelada (t)' },
		{ value: 'l', label: 'Capacidade/Volume: Litro (L)' },
		{ value: 'ml', label: 'Capacidade/Volume: Mililitro (mL)' },
		{ value: 'm3', label: 'Capacidade/Volume: Metro cubico (m3)' },
		{ value: 'm2', label: 'Area: Metro quadrado (m2)' },
		{ value: 'cm2', label: 'Area: Centimetro quadrado (cm2)' },
		{ value: 'ha', label: 'Area: Hectare (ha)' }
	];

	/** Indica se a unidade exige quantidade inteira. */
	function isUnidadeInteira(unidadeMedida: string | null | undefined) {
		const normalized = normalize(unidadeMedida || '');
		return normalized === 'un' || normalized === 'unidade';
	}

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

	let filteredProdutosForLoteSelect = $derived(
		produtos.filter((produto) => {
			const id = produto.id.toString();
			if (loteProdutoTipoIds.includes(id)) return true;

			const search = normalize(loteProdutoSearch);
			if (!search) return true;

			const haystack = `${produto.id} ${produto.nome} ${produto.sku || ''}`;
			return normalize(haystack).includes(search);
		})
	);

	/** Limpa mensagens de erro dos formulários de produtos e lotes. */
	function resetProdutoForm() {
		formError = '';
	}

	/** Abre o modal para criação de produto. */
	function openProdutoModal() {
		resetProdutoForm();
		editingProdutoId = null;
		produtoClienteId = '';
		produtoNome = '';
		produtoSku = '';
		produtoUnidadeMedida = 'un';
		isProdutoModalOpen = true;
	}

	/** Preenche o modal com dados do produto selecionado para edição. */
	function handleEditProduto(produtoId: number) {
		const produto = produtos.find((item) => item.id === produtoId);
		if (!produto) return;

		resetProdutoForm();
		editingProdutoId = produtoId;
		produtoClienteId = produto.cliente_id == null ? '' : String(produto.cliente_id);
		produtoNome = produto.nome || '';
		produtoSku = produto.sku || '';
		produtoUnidadeMedida = produto.unidade_medida || 'un';
		isProdutoModalOpen = true;
	}

	/** Confirma e envia a exclusão do produto selecionado. */
	function handleDeleteProduto(produtoId: number) {
		if (!window.confirm('Tem certeza que deseja excluir este produto?')) return;

		deleteProdutoForms[produtoId]?.requestSubmit();
	}

	/** Abre o modal de lote com produtos e quantidades atuais do EPC informado. */
	function handleEditLote(epcTag: string) {
		const lote = lotes.find((item) => item.epc_tag === epcTag);
		if (!lote) return;

		resetProdutoForm();
		editingLoteEpcTag = lote.epc_tag;
		const ids =
			lote.produto_assoc && lote.produto_assoc.length > 0
				? lote.produto_assoc.map((assoc) => assoc.produto_tipo_id)
				: lote.produto_tipo_ids && lote.produto_tipo_ids.length > 0
					? lote.produto_tipo_ids
					: lote.produto_tipo_id == null
						? []
						: [lote.produto_tipo_id];
		loteProdutoTipoIds = ids.map((id) => String(id));
		const quantitiesById: Record<string, string> = {};
		if (lote.produto_assoc && lote.produto_assoc.length > 0) {
			for (const assoc of lote.produto_assoc) {
				quantitiesById[String(assoc.produto_tipo_id)] = String(assoc.quantidade);
			}
		} else {
			for (const id of ids) {
				quantitiesById[String(id)] = String(lote.quantidade_atual ?? 1);
			}
		}
		loteQuantidades = quantitiesById;
		loteProdutoSearch = '';
		isLoteModalOpen = true;
	}

	/** Abre o modal para mover o lote atualmente em edição para outra câmara. */
	function openMoveLoteModal() {
		if (!editingLoteEpcTag) return;
		resetProdutoForm();

		if (camaras.length === 0) {
			formError = 'Nenhuma câmara disponível para movimentação.';
			return;
		}

		movingLoteEpcTag = editingLoteEpcTag;
		moveDestinoCamaraId = '';
		isMoveLoteModalOpen = true;
	}

	/** Mantém apenas quantidades dos produtos selecionados no lote. */
	function syncLoteQuantidades() {
		const next: Record<string, string> = {};
		for (const id of loteProdutoTipoIds) {
			next[id] = loteQuantidades[id] ?? '1';
		}
		loteQuantidades = next;
	}

	/** Retorna o nome de um produto pelo id usado no formulário de lote. */
	function getProdutoNomeById(id: string) {
		const produto = produtos.find((item) => String(item.id) === id);
		return produto?.nome || `Produto ${id}`;
	}

	/** Retorna a unidade de medida de um produto pelo id. */
	function getProdutoUnidadeById(id: string) {
		const produto = produtos.find((item) => String(item.id) === id);
		return produto?.unidade_medida || null;
	}

	/** Define o step do input de quantidade conforme a unidade do produto. */
	function getStepForProduto(id: string) {
		return isUnidadeInteira(getProdutoUnidadeById(id)) ? '1' : '0.01';
	}

	/** Define o mínimo do input de quantidade conforme a unidade do produto. */
	function getMinForProduto(id: string) {
		return isUnidadeInteira(getProdutoUnidadeById(id)) ? '1' : '0.01';
	}

	/** Serializa produtos selecionados e quantidades para envio ao action server-side. */
	function buildProdutoAssocJson() {
		const produtoAssoc = loteProdutoTipoIds.map((idValue) => ({
			produto_tipo_id: Number(idValue),
			quantidade: Number(loteQuantidades[idValue])
		}));

		return JSON.stringify(produtoAssoc);
	}

	const handleProdutoSubmit: SubmitFunction = () => {
		isSubmitting = true;
		resetProdutoForm();

		return async ({ result, update }) => {
			isSubmitting = false;
			await update({ invalidateAll: result.type === 'success' });
			if (result.type === 'error') {
				formError = 'Não foi possível salvar o produto.';
			}
		};
	};

	const handleDeleteProdutoSubmit: SubmitFunction = () => {
		isSubmitting = true;
		resetProdutoForm();

		return async ({ result, update }) => {
			isSubmitting = false;
			await update({ invalidateAll: result.type === 'success' });
			if (result.type === 'error') {
				formError = 'Não foi possível excluir o produto.';
			}
		};
	};

	const handleLoteSubmit: SubmitFunction = () => {
		isSubmitting = true;
		resetProdutoForm();

		return async ({ result, update }) => {
			isSubmitting = false;
			await update({ invalidateAll: result.type === 'success' });
			if (result.type === 'error') {
				formError = 'Não foi possível atualizar o lote.';
			}
		};
	};

	const handleMoveLoteSubmit: SubmitFunction = () => {
		isSubmitting = true;
		resetProdutoForm();

		return async ({ result, update }) => {
			isSubmitting = false;
			await update({ invalidateAll: result.type === 'success' });
			if (result.type === 'error') {
				formError = 'Não foi possível movimentar o lote.';
			}
		};
	};

	$effect(() => {
		if (!actionResult) return;

		if (actionResult.action === 'createProduto' || actionResult.action === 'updateProduto') {
			if (actionResult.success) {
				isProdutoModalOpen = false;
				editingProdutoId = null;
				produtoClienteId = '';
				produtoNome = '';
				produtoSku = '';
				produtoUnidadeMedida = 'un';
				formError = '';
				return;
			}

			if (actionResult.error) {
				formError = actionResult.error;
			}

			const fieldValues = actionResult.fieldValues;
			if (fieldValues) {
				if (typeof fieldValues.clienteId === 'string') produtoClienteId = fieldValues.clienteId;
				if (typeof fieldValues.nome === 'string') produtoNome = fieldValues.nome;
				if (typeof fieldValues.sku === 'string') produtoSku = fieldValues.sku;
				if (typeof fieldValues.unidadeMedida === 'string') {
					produtoUnidadeMedida = fieldValues.unidadeMedida;
				}
			}

			isProdutoModalOpen = true;
			return;
		}

		if (actionResult.action === 'updateLote') {
			if (actionResult.success) {
				isLoteModalOpen = false;
				editingLoteEpcTag = '';
				formError = '';
				return;
			}

			if (actionResult.error) {
				formError = actionResult.error;
			}

			const fieldValues = actionResult.fieldValues;
			if (fieldValues?.loteProdutoTipoIds) {
				loteProdutoTipoIds = fieldValues.loteProdutoTipoIds;
			}
			if (fieldValues?.loteQuantidades) {
				loteQuantidades = fieldValues.loteQuantidades;
			}

			isLoteModalOpen = true;
			return;
		}

		if (actionResult.action === 'moveLote') {
			if (actionResult.success) {
				isMoveLoteModalOpen = false;
				isLoteModalOpen = false;
				movingLoteEpcTag = '';
				editingLoteEpcTag = '';
				moveDestinoCamaraId = '';
				formError = '';
				return;
			}

			if (actionResult.error) {
				formError = actionResult.error;
			}
		}

		if (actionResult.action === 'deleteProduto' && actionResult.error) {
			formError = actionResult.error;
		}
	});
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

	{#if formError && !isProdutoModalOpen && !isLoteModalOpen && !isMoveLoteModalOpen}
		<Alert class="mt-4">
			{#snippet icon()}<InfoCircleSolid class="h-4 w-4" />{/snippet}
			{formError}
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
		<div class="mb-4 flex items-center justify-between">
			<h2 class="h1 text-gray-900 dark:text-white">Produtos Cadastrados</h2>
			<Button color="orange" onclick={openProdutoModal}
				><PlusOutline class="mr-2 w-4" />Adicionar Produto</Button
			>
		</div>

		<TableSearch
			placeholder="Buscar por ID, cliente, nome, SKU ou unidade..."
			hoverable={true}
			bind:inputValue={searchProdutos}
			divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
			innerDivClass="flex flex-col md:flex-row md:flex-wrap items-start justify-between p-4 gap-4"
			searchClass="w-full md:w-1/2"
		>
			{#snippet header()}
				<TableActions idPrefix="produtos" />
			{/snippet}
			<TableHead>
				<TableHeadCell>ID</TableHeadCell>
				<TableHeadCell>Cliente ID</TableHeadCell>
				<TableHeadCell>Nome</TableHeadCell>
				<TableHeadCell>SKU</TableHeadCell>
				<TableHeadCell>Unidade</TableHeadCell>
				<TableHeadCell>Total de Lotes</TableHeadCell>
				<TableHeadCell class="text-right">Ações</TableHeadCell>
			</TableHead>
			<TableBody>
				{#each filteredProdutos as produto}
					<TableBodyRow>
						<form
							method="POST"
							action="?/deleteProduto"
							class="hidden"
							bind:this={deleteProdutoForms[produto.id]}
							use:enhance={handleDeleteProdutoSubmit}
						>
							<input type="hidden" name="produtoId" value={produto.id} />
						</form>
						<TableBodyCell>{produto.id}</TableBodyCell>
						<TableBodyCell>{produto.cliente_id ?? '-'}</TableBodyCell>
						<TableBodyCell>{produto.nome}</TableBodyCell>
						<TableBodyCell>{produto.sku || '-'}</TableBodyCell>
						<TableBodyCell>{produto.unidade_medida || '-'}</TableBodyCell>
						<TableBodyCell>{produto.total_lotes ?? 0}</TableBodyCell>
						<TableBodyCell class="text-right">
							<RowActionsMenu
								menuId={`produto-actions-button-${produto.id}`}
								headerLabel="Ações do produto"
								onEdit={() => handleEditProduto(produto.id)}
								onDelete={() => handleDeleteProduto(produto.id)}
							/>
						</TableBodyCell>
					</TableBodyRow>
				{:else}
					<TableBodyRow>
						<TableBodyCell colspan={7} class="py-4 text-center text-gray-500">
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
			{#snippet header()}
				<TableActions idPrefix="lotes" />
			{/snippet}
			<TableHead>
				<TableHeadCell>EPC Tag</TableHeadCell>
				<TableHeadCell>Produto Tipo ID</TableHeadCell>
				<TableHeadCell>Produtos</TableHeadCell>
				<TableHeadCell>Quantidade</TableHeadCell>
				<TableHeadCell>Local atual</TableHeadCell>
				<TableHeadCell>Desde</TableHeadCell>
				<TableHeadCell class="text-right">Ações</TableHeadCell>
			</TableHead>
			<TableBody>
				{#each filteredLotes as lote}
					<TableBodyRow>
						<TableBodyCell>{lote.epc_tag || lote.id}</TableBodyCell>
						<TableBodyCell
							>{lote.produto_tipo_ids && lote.produto_tipo_ids.length > 0
								? lote.produto_tipo_ids.join(', ')
								: (lote.produto_tipo_id ?? '-')}</TableBodyCell
						>
						<TableBodyCell>
							{#if lote.produto_assoc && lote.produto_assoc.length > 0}
								{#each lote.produto_assoc as assoc, idx}
									{assoc.produto_nome} ({assoc.quantidade}){idx < lote.produto_assoc.length - 1
										? ', '
										: ''}
								{/each}
							{:else}
								{lote.produto_nomes && lote.produto_nomes.length > 0
									? lote.produto_nomes.join(', ')
									: lote.produto_nome || lote.nome || '-'}
							{/if}
						</TableBodyCell>
						<TableBodyCell>{lote.quantidade_atual ?? '-'}</TableBodyCell>
						<TableBodyCell>{lote.local_atual || '-'}</TableBodyCell>
						<TableBodyCell>{lote.local_desde || '-'}</TableBodyCell>
						<TableBodyCell class="text-right">
							<RowActionsMenu
								menuId={`lote-actions-button-${lote.epc_tag}`}
								headerLabel="Ações do lote"
								onEdit={() => handleEditLote(lote.epc_tag)}
								showDelete={false}
							/>
						</TableBodyCell>
					</TableBodyRow>
				{:else}
					<TableBodyRow>
						<TableBodyCell colspan={7} class="py-4 text-center text-gray-500">
							Nenhum lote encontrado para "{searchLotes}".
						</TableBodyCell>
					</TableBodyRow>
				{/each}
			</TableBody>
		</TableSearch>
	{/if}

	<Modal bind:open={isProdutoModalOpen} title={produtoModalTitle} size="md">
		<form
			class="space-y-4"
			method="POST"
			action={editingProdutoId ? '?/updateProduto' : '?/createProduto'}
			use:enhance={handleProdutoSubmit}
		>
			{#if editingProdutoId}
				<input type="hidden" name="produtoId" value={editingProdutoId} />
			{/if}
			<div>
				<Label for="produto-cliente-id">Cliente</Label>
				<Select id="produto-cliente-id" name="clienteId" bind:value={produtoClienteId}>
					<option value="">Sem cliente</option>
					{#each clientes as cliente}
						<option value={cliente.id.toString()}>
							{cliente.id} - {cliente.nome}
						</option>
					{/each}
				</Select>
			</div>
			<div>
				<Label for="produto-nome">Nome</Label>
				<Input id="produto-nome" name="nome" bind:value={produtoNome} required />
			</div>
			<div>
				<Label for="produto-sku">SKU</Label>
				<Input id="produto-sku" name="sku" bind:value={produtoSku} />
			</div>
			<div>
				<Label for="produto-unidade-medida">Unidade de medida</Label>
				<Select
					id="produto-unidade-medida"
					name="unidadeMedida"
					bind:value={produtoUnidadeMedida}
					required
				>
					{#each unidadeMedidaOptions as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				</Select>
			</div>
			{#if formError}
				<p class="text-sm text-red-600">{formError}</p>
			{/if}
			<div class="flex justify-end gap-2">
				<Button type="button" color="light" onclick={() => (isProdutoModalOpen = false)}>
					Cancelar
				</Button>
				<Button type="submit" color="orange" disabled={isSubmitting}>{produtoSubmitLabel}</Button>
			</div>
		</form>
	</Modal>

	<Modal bind:open={isLoteModalOpen} title={loteModalTitle} size="md">
		<form class="space-y-4" method="POST" action="?/updateLote" use:enhance={handleLoteSubmit}>
			<input type="hidden" name="epcTag" value={editingLoteEpcTag} />
			<input type="hidden" name="produtoAssocJson" value={buildProdutoAssocJson()} />
			<div>
				<Label for="lote-epc-tag">EPC Tag</Label>
				<Input id="lote-epc-tag" value={editingLoteEpcTag} disabled />
			</div>
			<div>
				<Label for="lote-produto">Produtos associados</Label>
				<Input
					id="lote-produto-search"
					placeholder="Pesquisar produto por ID, nome ou SKU..."
					bind:value={loteProdutoSearch}
					class="mb-2"
				/>
				<Select
					id="lote-produto"
					bind:value={loteProdutoTipoIds}
					multiple
					onchange={syncLoteQuantidades}
				>
					{#each filteredProdutosForLoteSelect as produto}
						<option value={produto.id.toString()}>
							{produto.id} - {produto.nome}{produto.sku ? ` (${produto.sku})` : ''}
						</option>
					{/each}
				</Select>
				<p class="mt-1 text-xs text-gray-500">
					Segure Ctrl (ou Cmd) para selecionar mais de um produto.
				</p>
			</div>
			{#if loteProdutoTipoIds.length > 0}
				<div class="space-y-3">
					<Label>Quantidade por produto</Label>
					{#each loteProdutoTipoIds as produtoId}
						<div class="grid grid-cols-1 gap-2 md:grid-cols-[1fr_140px] md:items-center">
							<p class="text-sm text-gray-700">{getProdutoNomeById(produtoId)}</p>
							<Input
								type="number"
								min={getMinForProduto(produtoId)}
								step={getStepForProduto(produtoId)}
								bind:value={loteQuantidades[produtoId]}
								required
							/>
						</div>
					{/each}
				</div>
			{/if}
			{#if formError}
				<p class="text-sm text-red-600">{formError}</p>
			{/if}
			<div class="flex items-center justify-between gap-2">
				<Button type="button" color="dark" outline onclick={openMoveLoteModal}>
					Movimentar lote
				</Button>
				<div class="flex justify-end gap-2">
					<Button type="button" color="light" onclick={() => (isLoteModalOpen = false)}>
						Cancelar
					</Button>
					<Button type="submit" color="orange" disabled={isSubmitting}>{loteSubmitLabel}</Button>
				</div>
			</div>
		</form>
	</Modal>

	<Modal bind:open={isMoveLoteModalOpen} title={moveLoteModalTitle} size="md">
		<form class="space-y-4" method="POST" action="?/moveLote" use:enhance={handleMoveLoteSubmit}>
			<input type="hidden" name="epcTag" value={movingLoteEpcTag} />
			<div>
				<Label for="move-lote-epc">EPC Tag</Label>
				<Input id="move-lote-epc" value={movingLoteEpcTag} disabled />
			</div>
			<div>
				<Label for="move-lote-camara">Destino (Câmara)</Label>
				<Select id="move-lote-camara" name="camaraId" bind:value={moveDestinoCamaraId} required>
					<option value="">Selecione uma câmara</option>
					{#each camaras as camara}
						<option value={camara.id.toString()}>
							{camara.id} - {camara.nome}
						</option>
					{/each}
				</Select>
			</div>
			{#if formError}
				<p class="text-sm text-red-600">{formError}</p>
			{/if}
			<div class="flex justify-end gap-2">
				<Button type="button" color="light" onclick={() => (isMoveLoteModalOpen = false)}>
					Cancelar
				</Button>
				<Button type="submit" color="orange" disabled={isSubmitting}>Movimentar lote</Button>
			</div>
		</form>
	</Modal>
</div>
