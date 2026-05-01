<script lang="ts">
	import { enhance } from '$app/forms';
	import {
		Alert,
		Button,
		Checkbox,
		InfoCircleSolid,
		Input,
		Label,
		Modal,
		Select,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		TableSearch,
		UserAddSolid
	} from '$lib/uicomponents.js';
	import type { SubmitFunction } from '@sveltejs/kit';
	import InfoCard from '$lib/components/InfoCard.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';
	import TableActions from '$lib/components/TableActions.svelte';

	let { data, form } = $props();

	type UsuarioRow = {
		id: number;
		nome_completo?: string | null;
		email: string;
		cliente_id: number | null;
		cliente_nome: string | null;
		has_password?: boolean;
	};

	type ClienteRow = {
		id: number;
		nome?: string | null;
		nome_razao_social?: string | null;
	};

	type ActionResultPayload = {
		action?: 'create' | 'update' | 'delete';
		success?: boolean;
		error?: string;
		fieldValues?: {
			nomeCompleto?: string;
			email?: string;
			clienteId?: string;
			isAlsoCliente?: boolean;
			cpfCnpj?: string;
		};
	};

	let usuarios = $derived((data.usuarios || []) as UsuarioRow[]);
	let clientes = $derived((data.clientes || []) as ClienteRow[]);
	let actionResult = $derived((form || null) as ActionResultPayload | null);

	let searchUsuarios = $state('');
	let isUsuarioModalOpen = $state(false);
	let editingUsuarioId = $state<number | null>(null);
	let isSubmitting = $state(false);
	let formError = $state('');
	let usuarioNomeCompleto = $state('');
	let usuarioEmail = $state('');
	let usuarioPassword = $state('');
	let usuarioClienteId = $state('');
	let usuarioIsAlsoCliente = $state(false);
	let usuarioCpfCnpj = $state('');
	let deleteForms = $state<Record<number, HTMLFormElement | undefined>>({});

	/** Normaliza texto para filtros sem acento e sem diferenciar maiúsculas. */
	const normalize = (str: string) =>
		str
			.toString()
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '');

	$effect(() => {
		if (usuarioClienteId && usuarioIsAlsoCliente) {
			usuarioIsAlsoCliente = false;
		}
	});

	let filteredUsuarios = $derived(
		usuarios.filter((item) => {
			const search = normalize(searchUsuarios);
			const combined = {
				id: item.id,
				nome_completo: item.nome_completo ?? '',
				email: item.email,
				cliente_id: item.cliente_id ?? '',
				cliente_nome: item.cliente_nome ?? ''
			};
			return Object.values(combined).some((val) =>
				normalize((val ?? '').toString()).includes(search)
			);
		})
	);

	let usuarioModalTitle = $derived(editingUsuarioId ? 'Editar Usuário' : 'Adicionar Usuário');
	let usuarioSubmitLabel = $derived(editingUsuarioId ? 'Salvar alterações' : 'Salvar');

	/** Limpa mensagens de erro do formulário de usuário. */
	function resetUsuarioForm() {
		formError = '';
	}

	/** Abre o modal para criação de usuário. */
	function openUsuarioModal() {
		resetUsuarioForm();
		editingUsuarioId = null;
		usuarioNomeCompleto = '';
		usuarioEmail = '';
		usuarioPassword = '';
		usuarioClienteId = '';
		usuarioIsAlsoCliente = false;
		usuarioCpfCnpj = '';
		isUsuarioModalOpen = true;
	}

	/** Preenche o modal com dados do usuário selecionado para edição. */
	function handleEditUsuario(usuarioId: number) {
		const usuario = usuarios.find((item) => item.id === usuarioId);
		if (!usuario) return;

		resetUsuarioForm();
		editingUsuarioId = usuarioId;
		usuarioNomeCompleto = (usuario.nome_completo || '').trim();
		usuarioEmail = (usuario.email || '').trim();
		usuarioPassword = '';
		usuarioClienteId = usuario.cliente_id == null ? '' : String(usuario.cliente_id);
		usuarioIsAlsoCliente = false;
		usuarioCpfCnpj = '';
		isUsuarioModalOpen = true;
	}

	/** Confirma e envia a exclusão do usuário selecionado. */
	function handleDeleteUsuario(usuarioId: number) {
		if (!window.confirm('Tem certeza que deseja excluir este usuário?')) return;
		deleteForms[usuarioId]?.requestSubmit();
	}

	const handleUsuarioSubmit: SubmitFunction = () => {
		isSubmitting = true;
		resetUsuarioForm();

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
		resetUsuarioForm();

		return async ({ result, update }) => {
			isSubmitting = false;
			await update({ invalidateAll: result.type === 'success' });
			if (result.type === 'error') {
				formError = 'Não foi possível excluir o usuário.';
			}
		};
	};

	$effect(() => {
		if (!actionResult) return;

		if (
			(actionResult.action === 'create' || actionResult.action === 'update') &&
			actionResult.success
		) {
			isUsuarioModalOpen = false;
			editingUsuarioId = null;
			usuarioNomeCompleto = '';
			usuarioEmail = '';
			usuarioPassword = '';
			usuarioClienteId = '';
			usuarioIsAlsoCliente = false;
			usuarioCpfCnpj = '';
			formError = '';
			return;
		}

		if (actionResult.action === 'create' || actionResult.action === 'update') {
			if (actionResult.error) {
				formError = actionResult.error;
			}

			const fieldValues = actionResult.fieldValues;
			if (fieldValues) {
				if (typeof fieldValues.nomeCompleto === 'string')
					usuarioNomeCompleto = fieldValues.nomeCompleto;
				if (typeof fieldValues.email === 'string') usuarioEmail = fieldValues.email;
				if (typeof fieldValues.clienteId === 'string') usuarioClienteId = fieldValues.clienteId;
				if (typeof fieldValues.isAlsoCliente === 'boolean') {
					usuarioIsAlsoCliente = fieldValues.isAlsoCliente;
				}
				if (typeof fieldValues.cpfCnpj === 'string') {
					usuarioCpfCnpj = fieldValues.cpfCnpj;
				}
			}

			isUsuarioModalOpen = true;
			return;
		}

		if (actionResult.action === 'delete' && actionResult.error) {
			formError = actionResult.error;
		}
	});
</script>

<div class="main-content p-8">
	<div class="header">
		<h1>Usuários</h1>
		<p>Visão geral dos usuários cadastrados.</p>
	</div>

	{#if data.error}
		<Alert class="mt-8">
			{#snippet icon()}<InfoCircleSolid class="h-4 w-4" />{/snippet}
			{data.error}
		</Alert>
	{/if}

	{#if formError && !isUsuarioModalOpen}
		<Alert class="mt-4">
			{#snippet icon()}<InfoCircleSolid class="h-4 w-4" />{/snippet}
			{formError}
		</Alert>
	{/if}

	<div class="mt-8 mb-8 grid grid-cols-1 gap-8 md:grid-cols-2">
		<InfoCard
			data-variant="Up"
			title="Total de usuários"
			description="Total de usuários no banco de dados"
			value={usuarios.length}
		/>
		<InfoCard
			data-variant="Up"
			title="Com senha definida"
			description="Usuários com senha cadastrada"
			value={usuarios.filter((item) => item.has_password).length}
		/>
	</div>

	<div class="mb-4 flex items-center justify-between">
		<h2 class="h1 text-gray-900 dark:text-white">Usuários Cadastrados</h2>
		<Button color="orange" onclick={openUsuarioModal}>
			<UserAddSolid class="mr-2 w-4" />Adicionar Usuário
		</Button>
	</div>

	<TableSearch
		placeholder="Buscar por ID, email, cliente ou status de senha..."
		hoverable={true}
		bind:inputValue={searchUsuarios}
		divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
		innerDivClass="flex flex-col md:flex-row md:flex-wrap items-start justify-between p-4 gap-4"
		searchClass="w-full md:w-1/2"
	>
		{#snippet header()}
			<TableActions idPrefix="usuarios" />
		{/snippet}
		<TableHead>
			<TableHeadCell>ID</TableHeadCell>
			<TableHeadCell>Nome</TableHeadCell>
			<TableHeadCell>Email</TableHeadCell>
			<TableHeadCell>Cliente</TableHeadCell>
			<TableHeadCell>Senha</TableHeadCell>
			<TableHeadCell class="text-right">Ações</TableHeadCell>
		</TableHead>
		<TableBody>
			{#each filteredUsuarios as usuario}
				<TableBodyRow>
					<form
						method="POST"
						action="?/delete"
						class="hidden"
						bind:this={deleteForms[usuario.id]}
						use:enhance={handleDeleteSubmit}
					>
						<input type="hidden" name="usuarioId" value={usuario.id} />
					</form>
					<TableBodyCell>{usuario.id}</TableBodyCell>
					<TableBodyCell>{usuario.nome_completo || '-'}</TableBodyCell>
					<TableBodyCell>{usuario.email}</TableBodyCell>
					<TableBodyCell>
						{usuario.cliente_id == null
							? '-'
							: `${usuario.cliente_id} - ${usuario.cliente_nome || '-'}`}
					</TableBodyCell>
					<TableBodyCell>{usuario.has_password ? 'Definida' : 'Não definida'}</TableBodyCell>
					<TableBodyCell class="text-right">
						<RowActionsMenu
							menuId={`usuario-actions-button-${usuario.id}`}
							headerLabel="Ações do usuário"
							onEdit={() => handleEditUsuario(usuario.id)}
							onDelete={() => handleDeleteUsuario(usuario.id)}
						/>
					</TableBodyCell>
				</TableBodyRow>
			{:else}
				<TableBodyRow>
					<TableBodyCell colspan={6} class="py-4 text-center text-gray-500">
						Nenhum usuário encontrado para "{searchUsuarios}".
					</TableBodyCell>
				</TableBodyRow>
			{/each}
		</TableBody>
	</TableSearch>

	<Modal bind:open={isUsuarioModalOpen} title={usuarioModalTitle} size="md">
		<form
			class="space-y-4"
			method="POST"
			action={editingUsuarioId ? '?/update' : '?/create'}
			use:enhance={handleUsuarioSubmit}
		>
			{#if editingUsuarioId}
				<input type="hidden" name="usuarioId" value={editingUsuarioId} />
			{/if}
			<div>
				<Label for="usuario-nome-completo">Nome completo</Label>
				<Input
					id="usuario-nome-completo"
					name="nomeCompleto"
					bind:value={usuarioNomeCompleto}
					placeholder="Nome e sobrenome"
					required
				/>
			</div>
			<div>
				<Label for="usuario-email">Email</Label>
				<Input id="usuario-email" name="email" type="email" bind:value={usuarioEmail} required />
			</div>
			<div>
				<Label for="usuario-cliente-id">Cliente</Label>
				<Select id="usuario-cliente-id" name="clienteId" bind:value={usuarioClienteId}>
					<option value="">Sem cliente</option>
					{#each clientes as cliente}
						<option value={cliente.id.toString()}>
							{cliente.id} - {cliente.nome_razao_social || cliente.nome || '-'}
						</option>
					{/each}
				</Select>
			</div>

			<div class="rounded-lg border border-gray-200 p-3">
				<Checkbox
					id="usuario-is-cliente"
					name="isAlsoCliente"
					disabled={Boolean(usuarioClienteId)}
					bind:checked={usuarioIsAlsoCliente}
				>
					Usuário também será cliente
				</Checkbox>
				{#if usuarioClienteId}
					<p class="mt-1 text-xs text-gray-500">
						Desmarque o cliente associado para habilitar esta opção.
					</p>
				{/if}
			</div>

			{#if usuarioIsAlsoCliente}
				<div>
					<Label for="usuario-cpf-cnpj">CPF/CNPJ</Label>
					<Input
						id="usuario-cpf-cnpj"
						name="cpfCnpj"
						placeholder="000.000.000-00 ou 00.000.000/0000-00"
						bind:value={usuarioCpfCnpj}
						required={usuarioIsAlsoCliente}
					/>
				</div>
			{/if}
			<div>
				<Label for="usuario-password">{editingUsuarioId ? 'Nova senha (opcional)' : 'Senha'}</Label>
				<Input
					id="usuario-password"
					name="password"
					type="password"
					bind:value={usuarioPassword}
					required={!editingUsuarioId}
					minlength={6}
				/>
				<p class="mt-1 text-xs text-gray-500">Use ao menos 6 caracteres.</p>
			</div>
			{#if formError}
				<p class="text-sm text-red-600">{formError}</p>
			{/if}
			<div class="flex justify-end gap-2">
				<Button type="button" color="light" onclick={() => (isUsuarioModalOpen = false)}>
					Cancelar
				</Button>
				<Button type="submit" color="orange" disabled={isSubmitting}>{usuarioSubmitLabel}</Button>
			</div>
		</form>
	</Modal>
</div>
