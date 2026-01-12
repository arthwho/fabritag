<script lang="ts">
	import { Card } from 'flowbite-svelte';
	import {
		DatabaseOutline,
		BarcodeOutline,
		VideoCameraOutline,
		TruckOutline
	} from 'flowbite-svelte-icons';
	import {
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Checkbox
	} from 'flowbite-svelte';
</script>

<div class="main-content p-8">
	<div class="header">
		<h1>Monitoramento de Produção</h1>
		<p>Visão em tempo real do fluxo de itens e análise de eficiência da linha.</p>
	</div>

	<div class="mt-8 mb-8 grid grid-cols-1 gap-8 md:grid-cols-4">
		<Card data-variant="Up" class="p-4">
			<div class="flex items-center justify-between">
				<div class="card-content">
					<div class="cardtitle">
						<span class="cardtitle_span">Total de produtos</span>
					</div>
					<div class="content">
						<div><span class="amount_span">3</span></div>
						<div class="info">
							<div class="type-card">
								<span class="typecard_span">Total de produtos no banco de dados</span>
							</div>
						</div>
					</div>
				</div>
				<div data-color="Green" data-size="2xl" data-type="Circle" class="icon-shape bg-orange-100">
					<DatabaseOutline class="w-16 text-orange-900 transition duration-75 dark:text-gray-400" />
				</div>
			</div>
		</Card>
		<Card data-variant="Up" class="p-4">
			<div class="flex items-center justify-between">
				<div class="card-content">
					<div class="cardtitle">
						<span class="cardtitle_span">Sensores ativos</span>
					</div>
					<div class="content">
						<div><span class="amount_span">2</span></div>
						<div class="info">
							<div class="type-card">
								<span class="typecard_span">Sensores ativos em todas as câmaras</span>
							</div>
						</div>
					</div>
				</div>
				<div data-color="Green" data-size="2xl" data-type="Circle" class="icon-shape bg-orange-100">
					<BarcodeOutline class="w-16 text-orange-900 transition duration-75 dark:text-gray-400" />
				</div>
			</div>
		</Card>
		<Card data-variant="Up" class="p-4">
			<div class="flex items-center justify-between">
				<div class="card-content">
					<div class="cardtitle">
						<span class="cardtitle_span">Sensores ativos</span>
					</div>
					<div class="content">
						<div><span class="amount_span">2</span></div>
						<div class="info">
							<div class="type-card">
								<span class="typecard_span">Câmaras monitoradas</span>
							</div>
						</div>
					</div>
				</div>
				<div data-color="Green" data-size="2xl" data-type="Circle" class="icon-shape bg-orange-100">
					<VideoCameraOutline
						class="w-16 text-orange-900 transition duration-75 dark:text-gray-400"
					/>
				</div>
			</div>
		</Card>
		<Card data-variant="Up" class="p-4">
			<div class="flex items-center justify-between">
				<div class="card-content">
					<div class="cardtitle">
						<span class="cardtitle_span">Movimentações hoje</span>
					</div>
					<div class="content">
						<div><span class="amount_span">2</span></div>
						<div class="info">
							<div class="type-card">
								<span class="typecard_span">Sensores ativos em todas as câmaras</span>
							</div>
						</div>
					</div>
				</div>
				<div data-color="Green" data-size="2xl" data-type="Circle" class="icon-shape bg-orange-100">
					<TruckOutline class="w-16 text-orange-900 transition duration-75 dark:text-gray-400" />
				</div>
			</div>
		</Card>
	</div>

	<Table hoverable={true} shadow={true} class="bg-white dark:bg-gray-800">
		<caption
			class="h1 bg-white p-4 text-left text-lg font-semibold text-gray-900 dark:bg-gray-800 dark:text-white"
			>Últimas movimentações</caption
		>
		<TableHead>
			<TableHeadCell class="p-4!">
				<Checkbox />
			</TableHeadCell>
			<TableHeadCell>Produto</TableHeadCell>
			<TableHeadCell>Origem</TableHeadCell>
			<TableHeadCell>Destino</TableHeadCell>
			<TableHeadCell>Data/Hora</TableHeadCell>
			<TableHeadCell>
				<span class="sr-only">Edit</span>
			</TableHeadCell>
		</TableHead>
		<TableBody>
			<TableBodyRow>
				<TableBodyCell class="p-4!">
					<Checkbox />
				</TableBodyCell>
				<TableBodyCell>Apple MacBook Pro 17"</TableBodyCell>
				<TableBodyCell>Silver</TableBodyCell>
				<TableBodyCell>Laptop</TableBodyCell>
				<TableBodyCell>$2999</TableBodyCell>
				<TableBodyCell>
					<a
						href="/tables"
						class="text-primary-600 dark:text-primary-500 font-medium hover:underline">Edit</a
					>
				</TableBodyCell>
			</TableBodyRow>
			<TableBodyRow>
				<TableBodyCell class="p-4!">
					<Checkbox />
				</TableBodyCell>
				<TableBodyCell>Microsoft Surface Pro</TableBodyCell>
				<TableBodyCell>White</TableBodyCell>
				<TableBodyCell>Laptop PC</TableBodyCell>
				<TableBodyCell>$1999</TableBodyCell>
				<TableBodyCell>
					<a
						href="/tables"
						class="text-primary-600 dark:text-primary-500 font-medium hover:underline">Edit</a
					>
				</TableBodyCell>
			</TableBodyRow>
			<TableBodyRow>
				<TableBodyCell class="p-4!">
					<Checkbox />
				</TableBodyCell>
				<TableBodyCell>Magic Mouse 2</TableBodyCell>
				<TableBodyCell>Black</TableBodyCell>
				<TableBodyCell>Accessories</TableBodyCell>
				<TableBodyCell>$99</TableBodyCell>
				<TableBodyCell>
					<a
						href="/tables"
						class="text-primary-600 dark:text-primary-500 font-medium hover:underline">Edit</a
					>
				</TableBodyCell>
			</TableBodyRow>
		</TableBody>
	</Table>
</div>

<style>
	h1,
	.h1 {
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

	.header {
		width: 100%;
		justify-content: center;
		display: flex;
		flex-direction: column;
	}

	.cardtitle_span {
		color: var(--Text-Neutral-Neutral-950, #22272a);
		font-size: 18px;
		font-family: Inter;
		font-weight: 700;
		line-height: 28px;
		word-wrap: break-word;
	}
	.cardtitle {
		align-self: stretch;
	}
	.amount_span {
		color: var(--Text-Neutral-Neutral-950, #22272a);
		font-size: 24px;
		font-family: Inter;
		font-weight: 700;
		line-height: 34px;
		word-wrap: break-word;
	}
	.typecard_span {
		color: var(--Text-Neutral-Neutral-900, #383e41);
		font-size: 12px;
		font-family: Inter;
		font-weight: 400;
		line-height: 18px;
		word-wrap: break-word;
	}
	.type-card {
		flex: 1 1 0;
	}
	.info {
		align-self: stretch;
		justify-content: flex-start;
		align-items: center;
		gap: 8px;
		display: inline-flex;
	}
	.content {
		align-self: stretch;
		flex-direction: column;
		justify-content: flex-start;
		align-items: flex-start;
		gap: 4px;
		display: flex;
	}
	.icon-shape {
		width: 64px;
		height: 64px;
		border-radius: 9999px;
		justify-content: center;
		align-items: center;
		display: flex;
	}
	.card-content {
		flex: 1 1 0;
		flex-direction: column;
		justify-content: flex-start;
		align-items: flex-start;
		display: inline-flex;
	}
</style>
