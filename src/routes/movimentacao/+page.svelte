<script>
	import {
		Input,
		Label,
		Button,
		Checkbox,
		A,
		Card,
		Dropdown,
		TruckOutline,
		ChevronDownOutline
	} from '$lib/uicomponents.js';
	import Container from '$lib/components/Container.svelte';
</script>

<div class="main-content p-8">
	<div class="header">
		<h1>Movimentar lote</h1>
		<p>Gerencie a movimentação de lotes entre diferentes locais manualmente.</p>
	</div>

	<Container class="mt-8">
		<div class="mb-6 grid justify-items-center gap-6 align-middle md:grid-cols-3 lg:grid-cols-3">
			<Button class="bg-orange-700 text-white hover:bg-orange-800"
				>Produto / Lote<ChevronDownOutline class="ms-2 h-6 w-6 text-white" /></Button
			>
			<Dropdown simple class="w-44 space-y-3 p-3 text-sm">
				<li>
					<Checkbox>Default checkbox</Checkbox>
				</li>
				<li>
					<Checkbox checked>Checked state</Checkbox>
				</li>
				<li>
					<Checkbox>Default checkbox</Checkbox>
				</li>
			</Dropdown>
			<div>
				<TruckOutline
					class="h-16 w-16 justify-center align-middle text-gray-500 transition duration-75 dark:text-gray-400"
				/>
			</div>
			<Button class="bg-orange-700 text-white hover:bg-orange-800"
				>Destino (Câmara/Setor)<ChevronDownOutline class="ms-2 h-6 w-6 text-white" /></Button
			>
			<Dropdown simple class="w-44 space-y-3 p-3 text-sm">
				<li>
					<Checkbox>Default checkbox</Checkbox>
				</li>
				<li>
					<Checkbox checked>Checked state</Checkbox>
				</li>
				<li>
					<Checkbox>Default checkbox</Checkbox>
				</li>
			</Dropdown>
		</div>
	</Container>
	<Button type="submit" class="mt-8 bg-orange-700 text-white hover:bg-orange-800">
		Movimentar lote</Button
	>
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
