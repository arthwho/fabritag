<script lang="ts">
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
		camaraPredioId = $bindable(''),
		camaraNome = $bindable(''),
		camaraCapacidade = $bindable(''),
		sensorCamaraId = $bindable(''),
		sensorModelo = $bindable('PN5180'),
		sensorIpAddress = $bindable(''),
		sensorAtivo = $bindable(true),
		predios = [],
		camaras = [],
		onSubmitPredio,
		onSubmitCamara,
		onSubmitSensor
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
		camaraPredioId?: string;
		camaraNome?: string;
		camaraCapacidade?: string;
		sensorCamaraId?: string;
		sensorModelo?: string;
		sensorIpAddress?: string;
		sensorAtivo?: boolean;
		predios?: PredioOption[];
		camaras?: CamaraOption[];
		onSubmitPredio: (event: SubmitEvent) => Promise<void>;
		onSubmitCamara: (event: SubmitEvent) => Promise<void>;
		onSubmitSensor: (event: SubmitEvent) => Promise<void>;
	} = $props();
</script>

<Modal bind:open={isPredioModalOpen} title={predioModalTitle} size="md">
	<form class="space-y-4" onsubmit={onSubmitPredio}>
		<div>
			<Label for="predio-nome">Nome</Label>
			<Input id="predio-nome" bind:value={predioNome} required />
		</div>
		<div>
			<Label for="predio-endereco">Endereço</Label>
			<Input id="predio-endereco" bind:value={predioEndereco} />
		</div>
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
	<form class="space-y-4" onsubmit={onSubmitCamara}>
		<div>
			<Label for="camara-predio">Prédio</Label>
			<Select id="camara-predio" bind:value={camaraPredioId} required>
				{#each predios as predio}
					<option value={predio.id.toString()}>{predio.nome}</option>
				{/each}
			</Select>
		</div>
		<div>
			<Label for="camara-nome">Nome</Label>
			<Input id="camara-nome" bind:value={camaraNome} required />
		</div>
		<div>
			<Label for="camara-capacidade">Capacidade de Vagas</Label>
			<Input id="camara-capacidade" type="number" min="0" bind:value={camaraCapacidade} />
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
	<form class="space-y-4" onsubmit={onSubmitSensor}>
		<div>
			<Label for="sensor-camara">Câmara</Label>
			<Select id="sensor-camara" bind:value={sensorCamaraId} required>
				{#each camaras as camara}
					<option value={camara.id.toString()}>{camara.nome}</option>
				{/each}
			</Select>
		</div>
		<div>
			<Label for="sensor-modelo">Modelo</Label>
			<Input id="sensor-modelo" bind:value={sensorModelo} />
		</div>
		<div>
			<Label for="sensor-ip">IP Address</Label>
			<Input id="sensor-ip" bind:value={sensorIpAddress} placeholder="192.168.2.175" />
		</div>
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
