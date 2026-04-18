<script lang="ts">
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
	import { invalidateAll } from '$app/navigation';
	import InfoCard from '$lib/components/InfoCard.svelte';
	import RowActionsMenu from '$lib/components/RowActionsMenu.svelte';
	import TableActions from '$lib/components/TableActions.svelte';

	let { data } = $props();

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

	function isRepeatedDigits(value: string) {
		return /^(\d)\1+$/.test(value);
	}

	function validateCpf(digits: string) {
		if (digits.length !== 11 || isRepeatedDigits(digits)) return false;

		const calcDigit = (base: string, factor: number) => {
			let total = 0;
			for (const char of base) {
				total += Number(char) * factor;
				factor -= 1;
			}
			const mod = total % 11;
			return mod < 2 ? 0 : 11 - mod;
		};

		const first = calcDigit(digits.slice(0, 9), 10);
		const second = calcDigit(digits.slice(0, 9) + String(first), 11);

		return digits === `${digits.slice(0, 9)}${first}${second}`;
	}

	function validateCnpj(digits: string) {
		if (digits.length !== 14 || isRepeatedDigits(digits)) return false;

		const calcDigit = (base: string, factors: number[]) => {
			let total = 0;
			for (let i = 0; i < base.length; i += 1) {
				total += Number(base[i]) * factors[i];
			}
			const mod = total % 11;
			return mod < 2 ? 0 : 11 - mod;
		};

		const first = calcDigit(digits.slice(0, 12), [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
		const second = calcDigit(
			digits.slice(0, 12) + String(first),
			[6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
		);

		return digits === `${digits.slice(0, 12)}${first}${second}`;
	}

	function getValidatedCpfCnpjOrNull() {
		const digits = onlyDigits(clienteCpfCnpj);
		if (!digits) return null;
		if (digits.length !== 11 && digits.length !== 14) {
			throw new Error('Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido.');
		}

		const isValid = digits.length === 11 ? validateCpf(digits) : validateCnpj(digits);
		if (!isValid) {
			throw new Error('CPF/CNPJ inválido. Verifique os dígitos informados.');
		}

		return digits;
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

	async function runClienteMutation(url: string, options: RequestInit, fallbackError: string) {
		resetClienteForm();
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

	async function handleDeleteCliente(clienteId: number) {
		if (!window.confirm('Tem certeza que deseja excluir este cliente?')) return;

		await runClienteMutation(
			`http://127.0.0.1:5000/api/clientes/${clienteId}`,
			{ method: 'DELETE' },
			'Não foi possível excluir o cliente.'
		);
	}

	async function createCliente(event: SubmitEvent) {
		event.preventDefault();
		resetClienteForm();

		const nome = clienteNome.trim();
		let cpfCnpj: string | null = null;
		try {
			cpfCnpj = getValidatedCpfCnpjOrNull();
		} catch (error) {
			formError = error instanceof Error ? error.message : 'CPF/CNPJ inválido.';
			return;
		}

		const success = await runClienteMutation(
			'http://127.0.0.1:5000/api/clientes',
			{
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					nome_razao_social: nome || null,
					cpf_cnpj: cpfCnpj
				})
			},
			'Não foi possível criar o cliente.'
		);

		if (success) {
			isClienteModalOpen = false;
		}
	}

	async function updateCliente(event: SubmitEvent) {
		event.preventDefault();
		if (!editingClienteId) return;

		const nome = clienteNome.trim();
		let cpfCnpj: string | null = null;
		try {
			cpfCnpj = getValidatedCpfCnpjOrNull();
		} catch (error) {
			formError = error instanceof Error ? error.message : 'CPF/CNPJ inválido.';
			return;
		}

		const success = await runClienteMutation(
			`http://127.0.0.1:5000/api/clientes/${editingClienteId}`,
			{
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					nome_razao_social: nome || null,
					cpf_cnpj: cpfCnpj
				})
			},
			'Não foi possível atualizar o cliente.'
		);

		if (success) {
			isClienteModalOpen = false;
			editingClienteId = null;
		}
	}

	async function submitClienteForm(event: SubmitEvent) {
		if (editingClienteId) {
			await updateCliente(event);
			return;
		}
		await createCliente(event);
	}
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
		<form class="space-y-4" onsubmit={submitClienteForm}>
			<div>
				<Label for="cliente-nome">Nome / Razão social</Label>
				<Input id="cliente-nome" bind:value={clienteNome} />
			</div>
			<div>
				<Label for="cliente-cpf-cnpj">CPF/CNPJ</Label>
				<Input
					id="cliente-cpf-cnpj"
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
