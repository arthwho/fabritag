<script lang="ts">
	import { enhance } from '$app/forms';
	import type { SubmitFunction } from '@sveltejs/kit';
	import { Button, Input, Label, Modal, Select } from '$lib/uicomponents.js';

	type ProdutoOption = {
		id: string;
		nome: string;
		sku: string | null;
		unidade_medida: string | null;
	};

	interface Props {
		open?: boolean;
		title?: string;
		submitLabel?: string;
		editingLoteEpcTag?: string;
		loteProdutoTipoIds?: string[];
		loteProdutoSearch?: string;
		loteQuantidades?: Record<string, string>;
		formError?: string;
		isSubmitting?: boolean;
		produtos?: ProdutoOption[];
		onSubmit: SubmitFunction;
		onNovoProduto?: () => void;
		onMoveLote?: () => void;
		formAction?: string;
		showMoveButton?: boolean;
	}

	let {
		open = $bindable(false),
		title = 'Editar Lote',
		submitLabel = 'Salvar alterações',
		editingLoteEpcTag = '',
		loteProdutoTipoIds = $bindable([]),
		loteProdutoSearch = $bindable(''),
		loteQuantidades = $bindable({}),
		formError = '',
		isSubmitting = false,
		produtos = [],
		onSubmit,
		onNovoProduto,
		onMoveLote,
		formAction = '?/updateLote',
		showMoveButton = true
	}: Props = $props();

	const normalize = (str: string) =>
		str
			.toString()
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '');

	function isUnidadeInteira(unidadeMedida: string | null | undefined) {
		const normalized = normalize(unidadeMedida || '');
		return normalized === 'un' || normalized === 'unidade';
	}

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

	function buildProdutoAssocJson() {
		const produtoAssoc = loteProdutoTipoIds.map((idValue) => ({
			produto_tipo_id: idValue,
			quantidade: Number(loteQuantidades[idValue])
		}));

		return JSON.stringify(produtoAssoc);
	}
</script>

<Modal bind:open {title} size="md">
	<form class="space-y-4" method="POST" action={formAction} use:enhance={onSubmit}>
		<input type="hidden" name="epcTag" value={editingLoteEpcTag} />
		<input type="hidden" name="produtoAssocJson" value={buildProdutoAssocJson()} />
		<div>
			<Label for="lote-epc-tag">EPC Tag</Label>
			<Input id="lote-epc-tag" value={editingLoteEpcTag} disabled />
		</div>
		<div>
			<div class="flex items-center justify-between gap-2 pb-4">
				<Label for="lote-produto">Produtos associados</Label>
				{#if onNovoProduto}
					<Button type="button" color="light" onclick={onNovoProduto}>
						<span class="hidden sm:inline">Novo Produto</span>
					</Button>
				{/if}
			</div>
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
			{#if showMoveButton && onMoveLote}
				<Button type="button" color="dark" outline onclick={onMoveLote}>Movimentar lote</Button>
			{:else}
				<span></span>
			{/if}
			<div class="flex justify-end gap-2">
				<Button type="button" color="light" onclick={() => (open = false)}>Cancelar</Button>
				<Button type="submit" color="orange" disabled={isSubmitting}>{submitLabel}</Button>
			</div>
		</div>
	</form>
</Modal>
