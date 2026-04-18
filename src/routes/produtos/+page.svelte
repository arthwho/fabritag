<script lang="ts">
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
		InfoCircleSolid
	} from '$lib/uicomponents.js';
	import InfoCard from '$lib/components/InfoCard.svelte';
	import TableActions from '$lib/components/TableActions.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';
	import { invalidateAll } from '$app/navigation';
	import { fly } from 'svelte/transition';

	let { data } = $props();

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

	type CamaraPayload = CamaraOption[] | { value?: CamaraOption[] } | null | undefined;

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

	function normalizeCamaras(payload: CamaraPayload): CamaraOption[] {
		if (Array.isArray(payload)) return payload;
		if (payload && Array.isArray(payload.value)) return payload.value;
		return [];
	}

	let produtos = $derived((data.produtos || []) as ProdutoRow[]);
	let clientes = $derived((data.clientes || []) as ClienteOption[]);
	let camarasFallback = $state<CamaraOption[] | null>(null);
	let camaras = $derived(camarasFallback ?? normalizeCamaras(data.camaras as CamaraPayload));
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

	let produtoModalTitle = $derived(editingProdutoId ? 'Editar Produto' : 'Adicionar Produto');
	let produtoSubmitLabel = $derived(editingProdutoId ? 'Salvar alterações' : 'Salvar');
	let loteModalTitle = $derived('Editar Lote');
	let loteSubmitLabel = $derived('Salvar alterações');
	let moveLoteModalTitle = $derived('Movimentar lote');

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

	function resetProdutoForm() {
		formError = '';
	}

	function openProdutoModal() {
		resetProdutoForm();
		editingProdutoId = null;
		produtoClienteId = '';
		produtoNome = '';
		produtoSku = '';
		produtoUnidadeMedida = 'un';
		isProdutoModalOpen = true;
	}

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

	async function runProdutoMutation(url: string, options: RequestInit, fallbackError: string) {
		resetProdutoForm();
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

	async function handleDeleteProduto(produtoId: number) {
		if (!window.confirm('Tem certeza que deseja excluir este produto?')) return;

		await runProdutoMutation(
			`http://127.0.0.1:5000/api/produtos/${produtoId}`,
			{ method: 'DELETE' },
			'Não foi possível excluir o produto.'
		);
	}

	async function createProduto(event: SubmitEvent) {
		event.preventDefault();
		resetProdutoForm();

		const nome = produtoNome.trim();
		if (!nome) {
			formError = 'O nome do produto é obrigatório.';
			return;
		}

		const clienteIdInput = String(produtoClienteId ?? '').trim();
		const clienteId = clienteIdInput ? Number(clienteIdInput) : null;
		if (clienteIdInput && (!Number.isInteger(clienteId) || Number(clienteId) < 1)) {
			formError = 'Informe um cliente válido.';
			return;
		}

		const success = await runProdutoMutation(
			'http://127.0.0.1:5000/api/produtos',
			{
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					cliente_id: clienteId,
					nome,
					sku: produtoSku.trim() || null,
					unidade_medida: produtoUnidadeMedida || null
				})
			},
			'Não foi possível criar o produto.'
		);

		if (success) {
			isProdutoModalOpen = false;
		}
	}

	async function updateProduto(event: SubmitEvent) {
		event.preventDefault();
		if (!editingProdutoId) return;

		const nome = produtoNome.trim();
		if (!nome) {
			formError = 'O nome do produto é obrigatório.';
			return;
		}

		const clienteIdInput = String(produtoClienteId ?? '').trim();
		const clienteId = clienteIdInput ? Number(clienteIdInput) : null;
		if (clienteIdInput && (!Number.isInteger(clienteId) || Number(clienteId) < 1)) {
			formError = 'Informe um cliente válido.';
			return;
		}

		const success = await runProdutoMutation(
			`http://127.0.0.1:5000/api/produtos/${editingProdutoId}`,
			{
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					cliente_id: clienteId,
					nome,
					sku: produtoSku.trim() || null,
					unidade_medida: produtoUnidadeMedida || null
				})
			},
			'Não foi possível atualizar o produto.'
		);

		if (success) {
			isProdutoModalOpen = false;
			editingProdutoId = null;
		}
	}

	async function submitProdutoForm(event: SubmitEvent) {
		if (editingProdutoId) {
			await updateProduto(event);
			return;
		}
		await createProduto(event);
	}

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

	async function openMoveLoteModal() {
		if (!editingLoteEpcTag) return;
		resetProdutoForm();

		if (camaras.length === 0) {
			try {
				const response = await fetch('http://127.0.0.1:5000/api/camaras');
				if (response.ok) {
					const payload = (await response.json()) as CamaraPayload;
					camarasFallback = normalizeCamaras(payload);
				}
			} catch {
				// Keep default error handling below.
			}
		}

		if (camaras.length === 0) {
			formError = 'Nenhuma câmara disponível para movimentação.';
			return;
		}

		movingLoteEpcTag = editingLoteEpcTag;
		moveDestinoCamaraId = '';
		isMoveLoteModalOpen = true;
	}

	function syncLoteQuantidades() {
		const next: Record<string, string> = {};
		for (const id of loteProdutoTipoIds) {
			next[id] = loteQuantidades[id] ?? '1';
		}
		loteQuantidades = next;
	}

	function getProdutoNomeById(id: string) {
		const produto = produtos.find((item) => String(item.id) === id);
		return produto?.nome || `Produto ${id}`;
	}

	function getProdutoUnidadeById(id: string) {
		const produto = produtos.find((item) => String(item.id) === id);
		return produto?.unidade_medida || null;
	}

	function getStepForProduto(id: string) {
		return isUnidadeInteira(getProdutoUnidadeById(id)) ? '1' : '0.01';
	}

	function getMinForProduto(id: string) {
		return isUnidadeInteira(getProdutoUnidadeById(id)) ? '1' : '0.01';
	}

	async function updateLote(event: SubmitEvent) {
		event.preventDefault();
		if (!editingLoteEpcTag) return;

		const produtoTipoIds = loteProdutoTipoIds
			.map((value) => Number(value))
			.filter((value) => Number.isInteger(value) && value > 0);

		if (produtoTipoIds.length === 0) {
			formError = 'Selecione ao menos um produto.';
			return;
		}

		const produtoAssoc = loteProdutoTipoIds.map((idValue) => {
			const produtoTipoId = Number(idValue);
			const quantidade = Number(loteQuantidades[idValue]);

			if (!Number.isFinite(quantidade) || quantidade <= 0) {
				throw new Error(`Informe uma quantidade válida para ${getProdutoNomeById(idValue)}.`);
			}

			if (isUnidadeInteira(getProdutoUnidadeById(idValue)) && !Number.isInteger(quantidade)) {
				throw new Error(`Para ${getProdutoNomeById(idValue)}, informe um valor inteiro.`);
			}

			return {
				produto_tipo_id: produtoTipoId,
				quantidade
			};
		});

		const success = await runProdutoMutation(
			`http://127.0.0.1:5000/api/lotes/${editingLoteEpcTag}`,
			{
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					produto_assoc: produtoAssoc
				})
			},
			'Não foi possível atualizar o lote.'
		);

		if (success) {
			isLoteModalOpen = false;
			editingLoteEpcTag = '';
		}
	}

	async function moveLote(event: SubmitEvent) {
		event.preventDefault();
		resetProdutoForm();

		if (!movingLoteEpcTag) return;

		const camaraId = Number(moveDestinoCamaraId);
		if (!Number.isInteger(camaraId) || camaraId <= 0) {
			formError = 'Selecione uma câmara de destino válida.';
			return;
		}

		const success = await runProdutoMutation(
			`http://127.0.0.1:5000/api/lotes/${movingLoteEpcTag}/movimentar`,
			{
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					camara_id: camaraId
				})
			},
			'Não foi possível movimentar o lote.'
		);

		if (success) {
			isMoveLoteModalOpen = false;
			isLoteModalOpen = false;
			movingLoteEpcTag = '';
			editingLoteEpcTag = '';
		}
	}
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
		<div class="mb-4 flex items-center justify-between">
			<h2 class="h1 text-gray-900 dark:text-white">Produtos Cadastrados</h2>
			<Button color="orange" onclick={openProdutoModal}>Adicionar Produto</Button>
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
		<form class="space-y-4" onsubmit={submitProdutoForm}>
			<div>
				<Label for="produto-cliente-id">Cliente</Label>
				<Select id="produto-cliente-id" bind:value={produtoClienteId}>
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
				<Input id="produto-nome" bind:value={produtoNome} required />
			</div>
			<div>
				<Label for="produto-sku">SKU</Label>
				<Input id="produto-sku" bind:value={produtoSku} />
			</div>
			<div>
				<Label for="produto-unidade-medida">Unidade de medida</Label>
				<Select id="produto-unidade-medida" bind:value={produtoUnidadeMedida} required>
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
		<form class="space-y-4" onsubmit={updateLote}>
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
		<form class="space-y-4" onsubmit={moveLote}>
			<div>
				<Label for="move-lote-epc">EPC Tag</Label>
				<Input id="move-lote-epc" value={movingLoteEpcTag} disabled />
			</div>
			<div>
				<Label for="move-lote-camara">Destino (Câmara)</Label>
				<Select id="move-lote-camara" bind:value={moveDestinoCamaraId} required>
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
