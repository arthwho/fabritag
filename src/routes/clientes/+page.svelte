<script lang="ts">
	import { enhance } from '$app/forms';
	import {
		Alert,
		Button,
		InfoCircleSolid,
		Input,
		Label,
		Modal,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		TableSearch
	} from '$lib/uicomponents.js';
	import type { SubmitFunction } from '@sveltejs/kit';
	import InfoCard from '$lib/components/InfoCard.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';
	import TableActions from '$lib/components/TableActions.svelte';

	let { data, form } = $props();

	type ClienteRow = {
		id: number;
		nome?: string | null;
		nome_razao_social?: string | null;
		cpf_cnpj?: string | null;
	};

	let clientes = $derived((data.clientes || []) as ClienteRow[]);
	let searchClientes = $state('');
	let isClienteModalOpen = $state(false);
	let editingClienteId = $state<number | null>(null);
	let isSubmitting = $state(false);
	let formError = $state('');
	let clienteNome = $state('');
	let clienteCpfCnpj = $state('');
	let deleteForms = $state<Record<number, HTMLFormElement | undefined>>({});

	type ActionResultPayload = {
		action?: 'create' | 'update' | 'delete';
		success?: boolean;
		error?: string;
		fieldValues?: {
			nome?: string;
			cpfCnpj?: string;
		};
	};

	let actionResult = $derived((form || null) as ActionResultPayload | null);

	function onlyDigits(value: string) {
		return (value || '').replace(/\D/g, '');
	}

	function formatCpfCnpj(value: string) {
		const digits = onlyDigits(value).slice(0, 14);

		if (digits.length <= 11) {
			return digits
				.replace(/(\d{3})(\d)/, '$1.$2')
				.replace(/(\d{3})(\d)/, '$1.$2')
				.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
		}

		return digits
			.replace(/(\d{2})(\d)/, '$1.$2')
			.replace(/(\d{3})(\d)/, '$1.$2')
			.replace(/(\d{3})(\d)/, '$1/$2')
			.replace(/(\d{4})(\d{1,2})$/, '$1-$2');
	}

	function handleCpfCnpjInput(event: Event) {
		const target = event.currentTarget as HTMLInputElement | null;
		clienteCpfCnpj = formatCpfCnpj(target?.value || clienteCpfCnpj);
	}

	const normalize = (str: string) =>
		str
			.toString()
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '');

	let filteredClientes = $derived(
		clientes.filter((item) => {
			const search = normalize(searchClientes);
			const nome = item.nome_razao_social || item.nome || '';
			const combined = {
				id: item.id,
				nome,
				cpf_cnpj: item.cpf_cnpj || ''
			};
			return Object.values(combined).some((val) =>
				normalize((val ?? '').toString()).includes(search)
			);
		})
	);

	let clienteModalTitle = $derived(editingClienteId ? 'Editar Cliente' : 'Adicionar Cliente');
	let clienteSubmitLabel = $derived(editingClienteId ? 'Salvar alterações' : 'Salvar');

	function resetClienteForm() {
		formError = '';
	}

	function openClienteModal() {
		resetClienteForm();
		editingClienteId = null;
		clienteNome = '';
		clienteCpfCnpj = '';
		isClienteModalOpen = true;
	}

	function handleEditCliente(clienteId: number) {
		const cliente = clientes.find((item) => item.id === clienteId);
		if (!cliente) return;

		resetClienteForm();
		editingClienteId = clienteId;
		clienteNome = (cliente.nome_razao_social || cliente.nome || '').trim();
		clienteCpfCnpj = formatCpfCnpj((cliente.cpf_cnpj || '').trim());
		isClienteModalOpen = true;
	}

	function handleDeleteCliente(clienteId: number) {
		if (!window.confirm('Tem certeza que deseja excluir este cliente?')) return;

		deleteForms[clienteId]?.requestSubmit();
	}

	const handleClienteSubmit: SubmitFunction = () => {
		isSubmitting = true;
		resetClienteForm();

		return async ({ result, update }) => {
			isSubmitting = false;
			await update({ invalidateAll: result.type === 'success' });

			if (result.type === 'error') {
				formError = 'Não foi possível processar a solicitação.';
			}
		};
	};

	const handleDeleteSubmit: SubmitFunction = () => {
		isSubmitting = true;
		resetClienteForm();

		return async ({ result, update }) => {
			isSubmitting = false;
			await update({ invalidateAll: result.type === 'success' });

			if (result.type === 'error') {
				formError = 'Não foi possível excluir o cliente.';
			}
		};
	};

	$effect(() => {
		if (!actionResult) return;

		if ((actionResult.action === 'create' || actionResult.action === 'update') && actionResult.success) {
			isClienteModalOpen = false;
			editingClienteId = null;
			clienteNome = '';
			clienteCpfCnpj = '';
			formError = '';
			return;
		}

		if (actionResult.action === 'create' || actionResult.action === 'update') {
			if (actionResult.error) {
				formError = actionResult.error;
			}

			const fieldValues = actionResult.fieldValues;
			if (fieldValues) {
				if (typeof fieldValues.nome === 'string') {
					clienteNome = fieldValues.nome;
				}
				if (typeof fieldValues.cpfCnpj === 'string') {
					clienteCpfCnpj = formatCpfCnpj(fieldValues.cpfCnpj);
				}
			}

			isClienteModalOpen = true;
			return;
		}

		if (actionResult.action === 'delete' && actionResult.error) {
			formError = actionResult.error;
		}
	});
</script>

<div class="main-content p-8">
	<div class="header">
		<h1>Clientes</h1>
		<p>Visão geral dos clientes cadastrados.</p>
	</div>

	{#if data.error}
		<Alert class="mt-8">
			{#snippet icon()}<InfoCircleSolid class="h-4 w-4" />{/snippet}
			{data.error}
		</Alert>
	{/if}

	{#if formError && !isClienteModalOpen}
		<Alert class="mt-4">
			{#snippet icon()}<InfoCircleSolid class="h-4 w-4" />{/snippet}
			{formError}
		</Alert>
	{/if}

	<div class="mt-8 mb-8 grid grid-cols-1 gap-8 md:grid-cols-2">
		<InfoCard
			data-variant="Up"
			title="Total de clientes"
			description="Total de clientes no banco de dados"
			value={clientes.length}
		/>
		<InfoCard
			data-variant="Up"
			title="Com CPF/CNPJ"
			description="Clientes com documento cadastrado"
			value={clientes.filter((item) => Boolean((item.cpf_cnpj || '').trim())).length}
		/>
	</div>

	<div class="mb-4 flex items-center justify-between">
		<h2 class="h1 text-gray-900 dark:text-white">Clientes Cadastrados</h2>
		<Button color="orange" onclick={openClienteModal}>Adicionar Cliente</Button>
	</div>

	<TableSearch
		placeholder="Buscar por ID, nome/razão social ou CPF/CNPJ..."
		hoverable={true}
		bind:inputValue={searchClientes}
		divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
		innerDivClass="flex flex-col md:flex-row md:flex-wrap items-start justify-between p-4 gap-4"
		searchClass="w-full md:w-1/2"
	>
		{#snippet header()}
			<TableActions idPrefix="clientes" />
		{/snippet}
		<TableHead>
			<TableHeadCell>ID</TableHeadCell>
			<TableHeadCell>Nome / Razão Social</TableHeadCell>
			<TableHeadCell>CPF/CNPJ</TableHeadCell>
			<TableHeadCell class="text-right">Ações</TableHeadCell>
		</TableHead>
		<TableBody>
			{#each filteredClientes as cliente}
				<TableBodyRow>
					<form
						method="POST"
						action="?/delete"
						class="hidden"
						bind:this={deleteForms[cliente.id]}
						use:enhance={handleDeleteSubmit}
					>
						<input type="hidden" name="clienteId" value={cliente.id} />
					</form>
					<TableBodyCell>{cliente.id}</TableBodyCell>
					<TableBodyCell>{cliente.nome_razao_social || cliente.nome || '-'}</TableBodyCell>
					<TableBodyCell>{cliente.cpf_cnpj || '-'}</TableBodyCell>
					<TableBodyCell class="text-right">
						<RowActionsMenu
							menuId={`cliente-actions-button-${cliente.id}`}
							headerLabel="Ações do cliente"
							onEdit={() => handleEditCliente(cliente.id)}
							onDelete={() => handleDeleteCliente(cliente.id)}
						/>
					</TableBodyCell>
				</TableBodyRow>
			{:else}
				<TableBodyRow>
					<TableBodyCell colspan={4} class="py-4 text-center text-gray-500">
						Nenhum cliente encontrado para "{searchClientes}".
					</TableBodyCell>
				</TableBodyRow>
			{/each}
		</TableBody>
	</TableSearch>

	<Modal bind:open={isClienteModalOpen} title={clienteModalTitle} size="md">
		<form
			class="space-y-4"
			method="POST"
			action={editingClienteId ? '?/update' : '?/create'}
			use:enhance={handleClienteSubmit}
		>
			{#if editingClienteId}
				<input type="hidden" name="clienteId" value={editingClienteId} />
			{/if}
			<div>
				<Label for="cliente-nome">Nome / Razão social</Label>
				<Input id="cliente-nome" name="nome" bind:value={clienteNome} />
			</div>
			<div>
				<Label for="cliente-cpf-cnpj">CPF/CNPJ</Label>
				<Input
					id="cliente-cpf-cnpj"
					name="cpfCnpj"
					bind:value={clienteCpfCnpj}
					oninput={handleCpfCnpjInput}
					placeholder="000.000.000-00 ou 00.000.000/0000-00"
					maxlength={18}
				/>
				<p class="mt-1 text-xs text-gray-500">
					Aceita apenas CPF (11 dígitos) ou CNPJ (14 dígitos).
				</p>
			</div>
			{#if formError}
				<p class="text-sm text-red-600">{formError}</p>
			{/if}
			<div class="flex justify-end gap-2">
				<Button type="button" color="light" onclick={() => (isClienteModalOpen = false)}>
					Cancelar
				</Button>
				<Button type="submit" color="orange" disabled={isSubmitting}>{clienteSubmitLabel}</Button>
			</div>
		</form>
	</Modal>
</div>
