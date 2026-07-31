<script lang="ts">
	import { onMount } from 'svelte';
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import type { SubmitFunction } from '@sveltejs/kit';
	import { Button, Input, Label, Modal, Select } from '$lib/uicomponents.js';
	import LoteEditModal from './produtos/LoteEditModal.svelte';
	import { apiPath } from '$lib/api.js';

	type ProdutoOption = {
		id: string;
		nome: string;
		sku: string | null;
		unidade_medida: string | null;
	};

	type LoteSemProduto = {
		epc_tag: string;
	};

	type ClienteOption = {
		id: string;
		nome: string;
	};

	let open = $state(false);
	let produtos = $state<ProdutoOption[]>([]);
	let pendingLotes = $state<LoteSemProduto[]>([]);
	let editingLoteEpcTag = $state('');
	let loteProdutoTipoIds = $state<string[]>([]);
	let loteProdutoSearch = $state('');
	let loteQuantidades = $state<Record<string, string>>({});
	let formError = $state('');
	let produtoFormError = $state('');
	let isSubmitting = $state(false);
	let isSubmittingProduto = $state(false);
	let isProdutoModalOpen = $state(false);
	let clientes = $state<ClienteOption[]>([]);
	let produtoClienteId = $state('');
	let produtoNome = $state('');
	let produtoSku = $state('');
	let produtoUnidadeMedida = $state('un');
	let isPolling = false;
	const dismissedEpcs = new Set<string>();

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

	function resetProdutoForm() {
		produtoFormError = '';
		produtoClienteId = '';
		produtoNome = '';
		produtoSku = '';
		produtoUnidadeMedida = 'un';
	}

	function prepareLote(lote: LoteSemProduto) {
		editingLoteEpcTag = lote.epc_tag;
		loteProdutoTipoIds = [];
		loteProdutoSearch = '';
		loteQuantidades = {};
		formError = '';
		open = true;
	}

	async function refreshPendingLotes() {
		if (isPolling || isSubmitting || open) return;
		isPolling = true;

		try {
			const [produtosRes, clientesRes] = await Promise.all([
				fetch(apiPath('/produtos')),
				fetch(apiPath('/clientes'))
			]);
			if (!produtosRes.ok) return;

			const produtosData = await produtosRes.json();
			produtos = Array.isArray(produtosData?.produtos) ? produtosData.produtos : [];
			pendingLotes = Array.isArray(produtosData?.lotes_sem_produto)
				? produtosData.lotes_sem_produto
				: [];
			if (clientesRes.ok) {
				const clientesData = await clientesRes.json();
				clientes = Array.isArray(clientesData) ? clientesData : [];
			}

			const nextLote = pendingLotes.find(
				(lote) => lote?.epc_tag && !dismissedEpcs.has(lote.epc_tag)
			);
			if (nextLote) {
				prepareLote(nextLote);
			}
		} catch (error) {
			console.error('Erro ao buscar lotes sem produto:', error);
		} finally {
			isPolling = false;
		}
	}

	const handleSubmit: SubmitFunction = () => {
		isSubmitting = true;
		formError = '';

		return async ({ result }) => {
			isSubmitting = false;

			if (result.type === 'success') {
				open = false;
				editingLoteEpcTag = '';
				loteProdutoTipoIds = [];
				loteQuantidades = {};
				await invalidateAll();
				await refreshPendingLotes();
				return;
			}

			formError =
				result.type === 'failure' && typeof result.data?.error === 'string'
					? result.data.error
					: 'Não foi possível configurar o lote.';
		};
	};

	function handleOpenChange() {
		if (!open && editingLoteEpcTag) {
			dismissedEpcs.add(editingLoteEpcTag);
		}
	}

	function handleNovoProduto() {
		resetProdutoForm();
		isProdutoModalOpen = true;
	}

	const handleCreateProdutoSubmit: SubmitFunction = () => {
		isSubmittingProduto = true;
		produtoFormError = '';

		return async ({ result, update }) => {
			isSubmittingProduto = false;
			await update({ invalidateAll: result.type === 'success' });

			if (result.type === 'success') {
				isProdutoModalOpen = false;
				await refreshPendingLotes();
				return;
			}

			if (result.type === 'failure' && typeof result.data?.error === 'string') {
				produtoFormError = result.data.error;
				return;
			}

			produtoFormError = 'Não foi possível salvar o produto.';
		};
	};

	onMount(() => {
		refreshPendingLotes();
		const interval = setInterval(refreshPendingLotes, 3000);

		return () => clearInterval(interval);
	});

	$effect(handleOpenChange);
</script>

<LoteEditModal
	bind:open
	title="Configurar novo lote"
	submitLabel="Configurar lote"
	{editingLoteEpcTag}
	bind:loteProdutoTipoIds
	bind:loteProdutoSearch
	bind:loteQuantidades
	{formError}
	{isSubmitting}
	{produtos}
	formAction="/produtos?/updateLote"
	onSubmit={handleSubmit}
	onNovoProduto={handleNovoProduto}
	showMoveButton={false}
/>

<Modal bind:open={isProdutoModalOpen} title="Adicionar Produto" size="md">
	<form
		class="space-y-4"
		method="POST"
		action="/produtos?/createProduto"
		use:enhance={handleCreateProdutoSubmit}
	>
		<div>
			<Label for="global-produto-cliente-id">Cliente</Label>
			<Select id="global-produto-cliente-id" name="clienteId" bind:value={produtoClienteId}>
				<option value="">Sem cliente</option>
				{#each clientes as cliente}
					<option value={cliente.id.toString()}>{cliente.id} - {cliente.nome}</option>
				{/each}
			</Select>
		</div>
		<div>
			<Label for="global-produto-nome">Nome</Label>
			<Input id="global-produto-nome" name="nome" bind:value={produtoNome} required />
		</div>
		<div>
			<Label for="global-produto-sku">SKU</Label>
			<Input id="global-produto-sku" name="sku" bind:value={produtoSku} />
		</div>
		<div>
			<Label for="global-produto-unidade-medida">Unidade de medida</Label>
			<Select
				id="global-produto-unidade-medida"
				name="unidadeMedida"
				bind:value={produtoUnidadeMedida}
				required
			>
				{#each unidadeMedidaOptions as option}
					<option value={option.value}>{option.label}</option>
				{/each}
			</Select>
		</div>
		{#if produtoFormError}
			<p class="text-sm text-red-600">{produtoFormError}</p>
		{/if}
		<div class="flex justify-end gap-2">
			<Button type="button" color="light" onclick={() => (isProdutoModalOpen = false)}>
				Cancelar
			</Button>
			<Button type="submit" color="orange" disabled={isSubmittingProduto}>Salvar</Button>
		</div>
	</form>
</Modal>
