<script>
	import { fabritagData } from '$lib/fabritag_store.js';
	import Button from './Button.svelte';

	export let showModal = false;
	export let modalType = '';

	let formData = {};

	function handleInputChange(e) {
		formData = { ...formData, [e.target.name]: e.target.value };
	}

	function handleSubmit() {
		if (modalType === 'produto') {
			const newProduct = {
				id: $fabritagData.produtos.length + 1,
				nome: formData.nome,
				sku: formData.sku,
				tipo: formData.tipo,
				status: 'Aguardando',
				local: 'Recebimento'
			};
			fabritagData.update((data) => ({
				...data,
				produtos: [...data.produtos, newProduct]
			}));
		} else if (modalType === 'sensor') {
			const newSensor = {
				id: $fabritagData.sensores.length + 1,
				modelo: formData.modelo,
				ip: formData.ip,
				local_id: parseInt(formData.local_id),
				status: 'Ativo'
			};
			fabritagData.update((data) => ({
				...data,
				sensores: [...data.sensores, newSensor]
			}));
		}
		showModal = false;
		formData = {};
	}
</script>

{#if showModal}
	<div class="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
		<div class="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
			<h3 class="mb-4 text-lg font-bold capitalize">Adicionar {modalType}</h3>

			<form on:submit|preventDefault={handleSubmit} class="space-y-4">
				{#if modalType === 'produto'}
					<input
						name="nome"
						placeholder="Nome do Produto"
						required
						on:input={handleInputChange}
						class="w-full rounded border p-2"
					/>
					<input
						name="sku"
						placeholder="SKU (Ex: PRE-10)"
						required
						on:input={handleInputChange}
						class="w-full rounded border p-2"
					/>
					<input
						name="tipo"
						placeholder="Tipo (Granel/Unidade)"
						required
						on:input={handleInputChange}
						class="w-full rounded border p-2"
					/>
				{:else if modalType === 'sensor'}
					<input
						name="modelo"
						placeholder="Modelo (Ex: PN5180)"
						required
						on:input={handleInputChange}
						class="w-full rounded border p-2"
					/>
					<input
						name="ip"
						placeholder="IP (Ex: 192.168.0.10)"
						required
						on:input={handleInputChange}
						class="w-full rounded border p-2"
					/>
					<select
						name="local_id"
						required
						on:change={handleInputChange}
						class="w-full rounded border p-2"
					>
						<option value="">Selecione a Câmara...</option>
						{#each $fabritagData.camaras as c}
							<option value={c.id}>{c.nome}</option>
						{/each}
					</select>
				{/if}

				<div class="mt-6 flex justify-end gap-2">
					<Button variant="secondary" on:click={() => (showModal = false)} type="button"
						>Cancelar</Button
					>
					<Button variant="success" type="submit">Salvar</Button>
				</div>
			</form>
		</div>
	</div>
{/if}
