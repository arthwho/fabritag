<script lang="ts">
	import { onMount } from 'svelte';
	import { enhance } from '$app/forms';
	import type { SubmitFunction } from '@sveltejs/kit';
	import { Modal, Input, Label, Select, Button } from '$lib/uicomponents.js';

	type PredioOption = {
		id: number;
		nome: string;
	};

	type CamaraOption = {
		id: number;
		nome: string;
	};

	let {
		isPredioModalOpen = $bindable(false),
		isCamaraModalOpen = $bindable(false),
		isSensorModalOpen = $bindable(false),
		isSubmitting = false,
		formError = '',
		predioModalTitle = 'Adicionar Prédio',
		camaraModalTitle = 'Adicionar Câmara',
		sensorModalTitle = 'Adicionar Sensor',
		predioSubmitLabel = 'Salvar',
		camaraSubmitLabel = 'Salvar',
		sensorSubmitLabel = 'Salvar',
		predioNome = $bindable(''),
		predioEndereco = $bindable(''),
		predioCep = $bindable(''),
		predioLogradouro = $bindable(''),
		predioNumero = $bindable(''),
		predioComplemento = $bindable(''),
		predioBairro = $bindable(''),
		predioCidade = $bindable(''),
		predioEstado = $bindable(''),
		camaraPredioId = $bindable(''),
		camaraNome = $bindable(''),
		camaraCapacidade = $bindable(''),
		sensorCamaraId = $bindable(''),
		sensorModelo = $bindable('PN5180'),
		sensorAtivo = $bindable(true),
		predios = [],
		camaras = [],
		predioFormAction = '?/createPredio',
		camaraFormAction = '?/createCamara',
		sensorFormAction = '?/createSensor',
		onEnhancePredio,
		onEnhanceCamara,
		onEnhanceSensor,
		editingPredioId = null,
		editingCamaraId = null,
		editingSensorId = null
	}: {
		isPredioModalOpen?: boolean;
		isCamaraModalOpen?: boolean;
		isSensorModalOpen?: boolean;
		isSubmitting?: boolean;
		formError?: string;
		predioModalTitle?: string;
		camaraModalTitle?: string;
		sensorModalTitle?: string;
		predioSubmitLabel?: string;
		camaraSubmitLabel?: string;
		sensorSubmitLabel?: string;
		predioNome?: string;
		predioEndereco?: string;
		predioCep?: string;
		predioLogradouro?: string;
		predioNumero?: string;
		predioComplemento?: string;
		predioBairro?: string;
		predioCidade?: string;
		predioEstado?: string;
		camaraPredioId?: string;
		camaraNome?: string;
		camaraCapacidade?: string;
		sensorCamaraId?: string;
		sensorModelo?: string;
		sensorAtivo?: boolean;
		predios?: PredioOption[];
		camaras?: CamaraOption[];
		predioFormAction?: string;
		camaraFormAction?: string;
		sensorFormAction?: string;
		onEnhancePredio: SubmitFunction;
		onEnhanceCamara: SubmitFunction;
		onEnhanceSensor: SubmitFunction;
		editingPredioId?: number | null;
		editingCamaraId?: number | null;
		editingSensorId?: number | null;
	} = $props();

	let consultaCepAtiva = $state(true);
	let cepStatus = $state('');
	let cepLoading = $state(false);

	onMount(() => {
		consultaCepAtiva = localStorage.getItem('fabritag-consulta-cep-ativa') !== 'false';
	});

	$effect(() => {
		if (typeof localStorage === 'undefined') return;
		localStorage.setItem('fabritag-consulta-cep-ativa', consultaCepAtiva ? 'true' : 'false');
	});

	const onlyCepDigits = (value: string) => value.replace(/\D/g, '').slice(0, 8);

	async function consultarCep() {
		const cep = onlyCepDigits(predioCep);
		if (!consultaCepAtiva || cep.length !== 8 || cepLoading) return;

		cepLoading = true;
		cepStatus = 'Consultando CEP...';

		try {
			const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
			const data = await response.json();

			if (!response.ok || data?.erro) {
				cepStatus = 'CEP não encontrado. Preencha manualmente.';
				return;
			}

			predioCep = data.cep || predioCep;
			predioLogradouro = data.logradouro || predioLogradouro;
			predioComplemento = data.complemento || predioComplemento;
			predioBairro = data.bairro || predioBairro;
			predioCidade = data.localidade || data.cidade || predioCidade;
			predioEstado = data.estado || data.uf || predioEstado;
			cepStatus = 'Endereço preenchido pelo ViaCEP.';
		} catch {
			cepStatus = 'Consulta ViaCEP indisponível. Preencha manualmente.';
		} finally {
			cepLoading = false;
		}
	}
</script>

<Modal bind:open={isPredioModalOpen} title={predioModalTitle} size="md">
	<form class="space-y-4" method="POST" action={predioFormAction} use:enhance={onEnhancePredio}>
		{#if editingPredioId}
			<input type="hidden" name="predioId" value={editingPredioId} />
		{/if}
		<div>
			<Label for="predio-nome">Nome</Label>
			<Input id="predio-nome" name="predioNome" bind:value={predioNome} required />
		</div>
		<input type="hidden" name="predioEndereco" value={predioEndereco} />
		<div class="flex items-center justify-between gap-3 rounded-lg border border-gray-200 p-3">
			<div>
				<p class="text-sm font-medium text-gray-900">Consulta automática de CEP</p>
				<p class="text-xs text-gray-500">Use este controle para desligar o ViaCEP em testes.</p>
			</div>
			<label class="flex items-center gap-2 text-sm text-gray-700">
				<input type="checkbox" bind:checked={consultaCepAtiva} />
				Ativa
			</label>
		</div>
		<div class="grid gap-4 md:grid-cols-3">
			<div>
				<Label for="predio-cep">CEP</Label>
				<div class="flex gap-2">
					<Input
						id="predio-cep"
						name="predioCep"
						bind:value={predioCep}
						placeholder="00000-000"
						onblur={consultarCep}
					/>
					<Button
						type="button"
						color="light"
						disabled={!consultaCepAtiva || cepLoading}
						onclick={consultarCep}
					>
						Buscar
					</Button>
				</div>
			</div>
			<div class="md:col-span-2">
				<Label for="predio-logradouro">Logradouro</Label>
				<Input id="predio-logradouro" name="predioLogradouro" bind:value={predioLogradouro} />
			</div>
			<div>
				<Label for="predio-numero">Número</Label>
				<Input id="predio-numero" name="predioNumero" bind:value={predioNumero} />
			</div>
			<div>
				<Label for="predio-complemento">Complemento</Label>
				<Input id="predio-complemento" name="predioComplemento" bind:value={predioComplemento} />
			</div>
			<div>
				<Label for="predio-bairro">Bairro</Label>
				<Input id="predio-bairro" name="predioBairro" bind:value={predioBairro} />
			</div>
			<div>
				<Label for="predio-cidade">Cidade</Label>
				<Input id="predio-cidade" name="predioCidade" bind:value={predioCidade} />
			</div>
			<div>
				<Label for="predio-estado">Estado</Label>
				<Input id="predio-estado" name="predioEstado" bind:value={predioEstado} />
			</div>
		</div>
		{#if cepStatus}
			<p class="text-sm text-gray-500">{cepStatus}</p>
		{/if}
		{#if formError}
			<p class="text-sm text-red-600">{formError}</p>
		{/if}
		<div class="flex justify-end gap-2">
			<Button type="button" color="light" onclick={() => (isPredioModalOpen = false)}
				>Cancelar</Button
			>
			<Button type="submit" color="orange" disabled={isSubmitting}>{predioSubmitLabel}</Button>
		</div>
	</form>
</Modal>

<Modal bind:open={isCamaraModalOpen} title={camaraModalTitle} size="md">
	<form class="space-y-4" method="POST" action={camaraFormAction} use:enhance={onEnhanceCamara}>
		{#if editingCamaraId}
			<input type="hidden" name="camaraId" value={editingCamaraId} />
		{/if}
		<div>
			<Label for="camara-predio">Prédio</Label>
			<Select id="camara-predio" name="camaraPredioId" bind:value={camaraPredioId} required>
				{#each predios as predio}
					<option value={predio.id.toString()}>{predio.nome}</option>
				{/each}
			</Select>
		</div>
		<div>
			<Label for="camara-nome">Nome</Label>
			<Input id="camara-nome" name="camaraNome" bind:value={camaraNome} required />
		</div>
		<div>
			<Label for="camara-capacidade">Capacidade de Vagas</Label>
			<Input
				id="camara-capacidade"
				name="camaraCapacidade"
				type="number"
				min="0"
				bind:value={camaraCapacidade}
			/>
		</div>
		{#if formError}
			<p class="text-sm text-red-600">{formError}</p>
		{/if}
		<div class="flex justify-end gap-2">
			<Button type="button" color="light" onclick={() => (isCamaraModalOpen = false)}
				>Cancelar</Button
			>
			<Button type="submit" color="orange" disabled={isSubmitting}>{camaraSubmitLabel}</Button>
		</div>
	</form>
</Modal>

<Modal bind:open={isSensorModalOpen} title={sensorModalTitle} size="md">
	<form class="space-y-4" method="POST" action={sensorFormAction} use:enhance={onEnhanceSensor}>
		{#if editingSensorId}
			<input type="hidden" name="sensorId" value={editingSensorId} />
		{/if}
		<div>
			<Label for="sensor-camara">Câmara</Label>
			<Select id="sensor-camara" name="sensorCamaraId" bind:value={sensorCamaraId} required>
				{#each camaras as camara}
					<option value={camara.id.toString()}>{camara.nome}</option>
				{/each}
			</Select>
		</div>
		<div>
			<Label for="sensor-modelo">Modelo</Label>
			<Input id="sensor-modelo" name="sensorModelo" bind:value={sensorModelo} />
		</div>
		<input type="hidden" name="sensorAtivo" value={sensorAtivo ? 'true' : 'false'} />
		{#if formError}
			<p class="text-sm text-red-600">{formError}</p>
		{/if}
		<div class="flex justify-end gap-2">
			<Button type="button" color="light" onclick={() => (isSensorModalOpen = false)}
				>Cancelar</Button
			>
			<Button type="submit" color="orange" disabled={isSubmitting}>{sensorSubmitLabel}</Button>
		</div>
	</form>
</Modal>
