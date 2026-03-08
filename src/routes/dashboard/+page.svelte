<script lang="ts">
	import {
		TableSearch,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Button,
		Dropdown,
		DropdownItem,
		ChevronDownOutline
	} from '$lib/uicomponents.js';
	import InfoCard from '$lib/components/InfoCard.svelte';
	export let data;
	$: dashboard = data.dashboard;

	let searchTerm = '';
	let dashboardFilter = 'Hoje';

	const normalize = (str: string) =>
		str
			.toString()
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '');

	const parseMovimentacaoDate = (value: string) => {
		if (!value) return null;
		const [datePart, timePart = '00:00:00'] = value.split(' ');
		const [year, month, day] = datePart.split('-').map(Number);
		const [hour, minute, second] = timePart.split(':').map(Number);

		if (!year || !month || !day) return null;
		return new Date(year, month - 1, day, hour || 0, minute || 0, second || 0);
	};

	const isSameDay = (dateA: Date, dateB: Date) =>
		dateA.getFullYear() === dateB.getFullYear() &&
		dateA.getMonth() === dateB.getMonth() &&
		dateA.getDate() === dateB.getDate();

	const isInLastDays = (date: Date, days: number) => {
		const now = new Date();
		const start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - (days - 1));
		return date >= start && date <= now;
	};

	$: movimentacoesNoPeriodo =
		dashboard?.ultimas_movimentacoes?.filter((item) => {
			const movDate = parseMovimentacaoDate(item?.data ?? '');
			if (dashboardFilter === 'Todos') return true;
			if (!movDate) return false;

			if (dashboardFilter === 'Hoje') {
				return isSameDay(movDate, new Date());
			}

			if (dashboardFilter === 'Ultimos 7 dias') {
				return isInLastDays(movDate, 7);
			}

			if (dashboardFilter === 'Ultimos Mês') {
				return isInLastDays(movDate, 30);
			}

			return true;
		}) || [];

	$: movimentacoesCardTitle =
		dashboardFilter === 'Hoje'
			? movimentacoesNoPeriodo.length === 1
				? 'Movimentação hoje'
				: 'Movimentações hoje'
			: dashboardFilter === 'Ultimos 7 dias'
				? movimentacoesNoPeriodo.length === 1
					? 'Movimentação (7 dias)'
					: 'Movimentações (7 dias)'
				: dashboardFilter === 'Ultimos Mês'
					? movimentacoesNoPeriodo.length === 1
						? 'Movimentação (mês)'
						: 'Movimentações (mês)'
					: movimentacoesNoPeriodo.length === 1
						? 'Movimentação total'
						: 'Movimentações totais';

	$: movimentacoesCardDescription =
		dashboardFilter === 'Hoje'
			? 'Total de movimentações realizadas hoje'
			: dashboardFilter === 'Ultimos 7 dias'
				? 'Total de movimentações nos últimos 7 dias'
				: dashboardFilter === 'Ultimos Mês'
					? 'Total de movimentações nos últimos 30 dias'
					: 'Total de movimentações registradas';

	$: filteredMovimentacoes =
		movimentacoesNoPeriodo.filter((item) => {
			const search = normalize(searchTerm);
			return Object.values(item).some((val) => normalize((val ?? '').toString()).includes(search));
		}) || [];
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

	<div class="mt-6 mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
		<div class="flex flex-wrap gap-2">
			<Button
				size="sm"
				outline={dashboardFilter !== 'Hoje'}
				color={dashboardFilter === 'Hoje' ? 'orange' : 'dark'}
				onclick={() => (dashboardFilter = 'Hoje')}
			>
				Hoje
			</Button>
			<Button
				size="sm"
				outline={dashboardFilter !== 'Todos'}
				color={dashboardFilter === 'Todos' ? 'orange' : 'dark'}
				onclick={() => (dashboardFilter = 'Todos')}
			>
				Todos
			</Button>
			<Button
				size="sm"
				outline={dashboardFilter !== 'Ultimos 7 dias'}
				color={dashboardFilter === 'Ultimos 7 dias' ? 'orange' : 'dark'}
				onclick={() => (dashboardFilter = 'Ultimos 7 dias')}
			>
				Ultimos 7 dias
			</Button>
			<Button
				size="sm"
				outline={dashboardFilter !== 'Ultimos Mês'}
				color={dashboardFilter === 'Ultimos Mês' ? 'orange' : 'dark'}
				onclick={() => (dashboardFilter = 'Ultimos Mês')}
			>
				Ultimos Mês
			</Button>
		</div>

		<div class="flex gap-2">
			<Button id="dashboard-export-btn" outline size="sm" color="dark" class="gap-2">
				Exportar
				<ChevronDownOutline class="h-4 w-4" />
			</Button>
			<Dropdown triggeredBy="#dashboard-export-btn">
				<DropdownItem>Excel (.xlsx)</DropdownItem>
				<DropdownItem>PDF (.pdf)</DropdownItem>
				<DropdownItem>CSV (.csv)</DropdownItem>
			</Dropdown>
		</div>
	</div>

	<div class="mt-8 mb-8 grid grid-cols-1 gap-8 md:grid-cols-4">
		<InfoCard
			data-variant="Up"
			title="Total de produtos"
			description="Total de produtos no banco de dados"
			value={dashboard.total_produtos}
		/>
		<InfoCard
			data-variant="Up"
			title={dashboard.total_sensores === 1 ? 'Sensor Ativo' : 'Sensores Ativos'}
			description="Sensores ativos em todas as câmaras"
			value={dashboard.total_sensores}
		/>
		<InfoCard
			data-variant="Up"
			title={dashboard.total_camaras === 1 ? 'Câmara monitorada' : 'Câmaras monitoradas'}
			description="Câmaras monitoradas"
			value={dashboard.total_camaras}
		/>
		<InfoCard
			data-variant="Up"
			title={movimentacoesCardTitle}
			description={movimentacoesCardDescription}
			value={movimentacoesNoPeriodo.length}
		/>
	</div>

	<div class="mb-4 flex items-center justify-between">
		<h2 class="h1 text-gray-900 dark:text-white">Últimas movimentações</h2>
	</div>

	<TableSearch
		placeholder="Buscar por produto, origem, destino ou data..."
		hoverable={true}
		bind:inputValue={searchTerm}
		divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
		innerDivClass="flex flex-col md:flex-row items-center justify-between p-4 gap-4"
		searchClass="w-full md:w-1/2"
	>
		<TableHead>
			<TableHeadCell>Produto</TableHeadCell>
			<TableHeadCell>Origem</TableHeadCell>
			<TableHeadCell>Destino</TableHeadCell>
			<TableHeadCell>Data/Hora</TableHeadCell>
		</TableHead>
		<TableBody>
			{#each filteredMovimentacoes as movimentacao}
				<TableBodyRow>
					<TableBodyCell>{movimentacao.produto}</TableBodyCell>
					<TableBodyCell>{movimentacao.origem}</TableBodyCell>
					<TableBodyCell>{movimentacao.destino}</TableBodyCell>
					<TableBodyCell>{movimentacao.data}</TableBodyCell>
				</TableBodyRow>
			{:else}
				<TableBodyRow>
					<TableBodyCell colspan={4} class="text-center py-4 text-gray-500">
						Nenhuma movimentação encontrada para "{searchTerm}".
					</TableBodyCell>
				</TableBodyRow>
			{/each}
		</TableBody>
	</TableSearch>
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
</style>
