<script lang="ts">
	import {
		DatabaseOutline,
		BarcodeOutline,
		VideoCameraOutline,
		TruckOutline,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Checkbox
	} from '$lib/uicomponents.js';
	import Card from '$lib/components/Card.svelte';
	export let data;
	$: dashboard = data.dashboard;
</script>

<div class="main-content p-8">
	<div class="header">
		<h1>Monitoramento de Produção</h1>
		<p>Visão em tempo real do fluxo de itens e análise de eficiência da linha.</p>
	</div>
	{#if data.error}
		<div class="mt-4 rounded-lg bg-red-100 p-4 text-center text-red-700">
			{data.error}
		</div>
	{/if}

	<div class="mt-8 mb-8 grid grid-cols-1 gap-8 md:grid-cols-4">
		<Card data-variant="Up">
			<div class="flex items-center justify-between">
				<div class="card-content">
					<div class="cardtitle">
						<span class="cardtitle_span">Total de produtos</span>
					</div>
					<div class="content">
						<div>
							<span class="amount_span">{dashboard.total_produtos}</span>
						</div>
					</div>
				</div>
				<div class="icon-shape bg-orange-100">
					<DatabaseOutline class="w-16 text-orange-900 transition duration-75 dark:text-gray-400" />
				</div>
			</div>
			<div class="info">
				<div class="type-card">
					<span class="typecard_span">Total de produtos no banco de dados</span>
				</div>
			</div>
		</Card>
		<Card data-variant="Up">
			<div class="flex items-center justify-between">
				<div class="card-content">
					<div class="cardtitle">
						<span class="cardtitle_span">Sensores ativos</span>
					</div>
					<div class="content">
						<div>
							<span class="amount_span">{dashboard.total_sensores}</span>
						</div>
					</div>
				</div>
				<div class="icon-shape bg-orange-100">
					<BarcodeOutline class="w-16 text-orange-900 transition duration-75 dark:text-gray-400" />
				</div>
			</div>
			<div class="info">
				<div class="type-card">
					<span class="typecard_span">Sensores ativos em todas as câmaras</span>
				</div>
			</div>
		</Card>
		<Card data-variant="Up">
			<div class="flex items-center justify-between">
				<div class="card-content">
					<div class="cardtitle">
						<span class="cardtitle_span">Câmaras monitoradas</span>
					</div>
					<div class="content">
						<div>
							<span class="amount_span">{dashboard.total_camaras}</span>
						</div>
					</div>
				</div>
				<div class="icon-shape bg-orange-100">
					<VideoCameraOutline
						class="w-16 text-orange-900 transition duration-75 dark:text-gray-400"
					/>
				</div>
			</div>
			<div class="info">
				<div class="type-card">
					<span class="typecard_span">Câmaras monitoradas</span>
				</div>
			</div>
		</Card>
		<Card data-variant="Up">
			<div class="flex items-center justify-between">
				<div class="card-content">
					<div class="cardtitle">
						<span class="cardtitle_span">Movimentações hoje</span>
					</div>
					<div class="content">
						<div>
							<span class="amount_span">{dashboard.ultimas_movimentacoes.length}</span>
						</div>
					</div>
				</div>
				<div class="icon-shape bg-orange-100">
					<TruckOutline class="w-16 text-orange-900 transition duration-75 dark:text-gray-400" />
				</div>
			</div>
			<div class="info">
				<div class="type-card">
					<span class="typecard_span">Total de movimentações nas últimas 24h</span>
				</div>
			</div>
		</Card>
	</div>

	<Table hoverable={true} divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800">
		<caption
			class="h1 bg-white p-4 text-left text-lg font-semibold text-gray-900 dark:bg-gray-800 dark:text-white"
		>
			Últimas movimentações
		</caption>
		<TableHead>
			<TableHeadCell class="p-4!"><Checkbox /></TableHeadCell>
			<TableHeadCell>Produto</TableHeadCell>
			<TableHeadCell>Origem</TableHeadCell>
			<TableHeadCell>Destino</TableHeadCell>
			<TableHeadCell>Data/Hora</TableHeadCell>
		</TableHead>
		<TableBody>
			{#each dashboard.ultimas_movimentacoes as movimentacao}
				<TableBodyRow>
					<TableBodyCell class="p-4!"><Checkbox /></TableBodyCell>
					<TableBodyCell>{movimentacao.produto}</TableBodyCell>
					<TableBodyCell>{movimentacao.origem}</TableBodyCell>
					<TableBodyCell>{movimentacao.destino}</TableBodyCell>
					<TableBodyCell>{movimentacao.data}</TableBodyCell>
				</TableBodyRow>
			{/each}
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
		width: 48px;
		height: 48px;
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
