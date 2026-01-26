<script>
	import {
		Input,
		Label,
		Button,
		Select,
		Checkbox,
		A,
		Card,
		Dropdown,
		TruckOutline,
		ChevronDownOutline
	} from '$lib/uicomponents.js';
	import Container from '$lib/components/Container.svelte';
	export let data;
	export let form;
</script>

<div class="main-content p-8">
	<div class="header">
		<h1>Movimentar lote</h1>
		<p>Gerencie a movimentação de lotes entre diferentes locais manualmente.</p>
	</div>
	{#if data.error}
		<div class="mt-4 rounded-lg bg-red-100 p-4 text-center text-red-700">
			{data.error}
		</div>
	{/if}

	<form method="POST">
		<Container class="mt-8">
			<div class="grid justify-items-center gap-6 align-middle md:grid-cols-2 lg:grid-cols-2">
				<div>
					<Label for="produto" class="mb-2 block">Produto / Lote</Label>
					<Select
						id="produto"
						name="produto"
						items={data.produtos.map((p) => ({ value: p.id, name: p.nome }))}
						required
					/>
				</div>
				<div>
					<Label for="destino" class="mb-2 block">Destino (Câmara/Setor)</Label>
					<Select
						id="destino"
						name="destino"
						items={data.camaras.map((c) => ({ value: c.id, name: c.nome }))}
						required
					/>
				</div>
			</div>
		</Container>
		<Button type="submit" class="mt-8 bg-orange-700 text-white hover:bg-orange-800">
			Movimentar lote</Button
		>
	</form>
	{#if form?.success}
		<div class="mt-4 rounded-lg bg-green-100 p-4 text-center text-green-700">
			{form.message}
		</div>
	{/if}
	{#if form?.error}
		<div class="mt-4 rounded-lg bg-red-100 p-4 text-center text-red-700">
			{form.error}
		</div>
	{/if}
</div>

<style>
	h1 {
		font-size: 24px;
		font-family: Inter;
		font-weight: 700;
		line-height: 34px;
		word-wrap: break-word;
	}
	p {
		color: var(--Text-Neutral-Neutral-900, #383e41);
		font-size: 12px;
		font-family: Inter;
		font-weight: 400;
		line-height: 18px;
		word-wrap: break-word;
	}
</style>
