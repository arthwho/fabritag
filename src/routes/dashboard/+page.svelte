<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import {
		TableSearch,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Button,
		Datepicker,
		Dropdown,
		DropdownItem,
		ChevronDownOutline
	} from '$lib/uicomponents.js';
	import InfoCard from '$lib/components/InfoCard.svelte';

	import { sensorStore } from '$lib/dispositivos.svelte.js';

	let { data } = $props();
	let dashboard = $state(untrack(() => data.dashboard));
	let dashboardError = $state(untrack(() => data.error));
	let lastDashboardUpdate = $state<Date | null>(null);

	let searchTerm = $state('');
	let dashboardFilter = $state('Hoje');
	let selectedDate = $state<Date | undefined>(undefined);

	onMount(() => {
		const stopPolling = sensorStore.startPolling();
		const dashboardInterval = setInterval(refreshDashboard, 2000);

		refreshDashboard();

		return () => {
			stopPolling();
			clearInterval(dashboardInterval);
		};
	});

	/** Normaliza texto para filtros sem acento e sem diferenciar maiúsculas. */
	const normalize = (str: string) =>
		str
			.toString()
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '');

	/** Compara se duas datas estão no mesmo dia local. */
	const isSameDay = (dateA: Date, dateB: Date) =>
		dateA.getFullYear() === dateB.getFullYear() &&
		dateA.getMonth() === dateB.getMonth() &&
		dateA.getDate() === dateB.getDate();

	/** Converte timestamp numérico em Date quando houver valor válido. */
	const dateFromTimestamp = (timestamp: number | null | undefined) =>
		typeof timestamp === 'number' ? new Date(timestamp) : null;

	const parseMovimentacaoDate = (value: string | null | undefined) => {
		if (!value) return null;
		const [datePart, timePart = '00:00:00'] = String(value).split(' ');
		const [year, month, day] = datePart.split('-').map(Number);
		const [hour, minute, second] = timePart.split(':').map(Number);

		if (!year || !month || !day) return null;
		return new Date(year, month - 1, day, hour || 0, minute || 0, second || 0);
	};

	const enrichDashboard = (dashboardData: typeof data.dashboard) => {
		const ultimasMovimentacoes = Array.isArray(dashboardData?.ultimas_movimentacoes)
			? dashboardData.ultimas_movimentacoes.map((item) => {
					const date = parseMovimentacaoDate(item?.data);
					const searchIndex = normalize(
						[item?.produto, item?.camara, item?.movimentacao, item?.data].filter(Boolean).join(' ')
					);

					return {
						...item,
						date_timestamp: date ? date.getTime() : null,
						search_index: searchIndex
					};
				})
			: [];

		return {
			...dashboardData,
			ultimas_movimentacoes: ultimasMovimentacoes
		};
	};

	const refreshDashboard = async () => {
		try {
			const response = await fetch('http://127.0.0.1:5000/api/dashboard');
			if (!response.ok) {
				dashboardError = `Falha ao atualizar dashboard: ${response.statusText}`;
				return;
			}

			const dashboardData = await response.json();
			dashboard = enrichDashboard(dashboardData);
			dashboardError = null;
			lastDashboardUpdate = new Date();
		} catch (error) {
			console.error('Error refreshing dashboard:', error);
			dashboardError = 'NÃ£o foi possÃ­vel conectar ao backend para atualizar o dashboard.';
		}
	};

	/** Retorna a data local de ontem sem preservar hora/minuto atuais. */
	const getYesterday = () => {
		const now = new Date();
		return new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
	};

	/** Verifica se uma data está dentro dos últimos N dias. */
	const isInLastDays = (date: Date, days: number) => {
		const now = new Date();
		const start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - (days - 1));
		return date >= start && date <= now;
	};

	let movimentacoesNoPeriodo = $derived(
		dashboard?.ultimas_movimentacoes?.filter((item) => {
			const movDate = dateFromTimestamp(item?.date_timestamp);
			if (dashboardFilter === 'Todos') return true;
			if (!movDate) return false;

			if (dashboardFilter === 'Hoje') {
				return isSameDay(movDate, new Date());
			}

			if (dashboardFilter === 'Ontem') {
				return isSameDay(movDate, getYesterday());
			}

			if (dashboardFilter === 'Ultimos 7 dias') {
				return isInLastDays(movDate, 7);
			}

			if (dashboardFilter === 'Ultimos Mês') {
				return isInLastDays(movDate, 30);
			}

			if (dashboardFilter === 'Data selecionada') {
				if (!selectedDate) return true;
				return isSameDay(movDate, selectedDate);
			}

			return true;
		}) || []
	);

	let movimentacoesCardTitle = $derived(
		dashboardFilter === 'Hoje'
			? movimentacoesNoPeriodo.length === 1
				? 'Movimentação hoje'
				: 'Movimentações hoje'
			: dashboardFilter === 'Ontem'
				? movimentacoesNoPeriodo.length === 1
					? 'Movimentação ontem'
					: 'Movimentações ontem'
				: dashboardFilter === 'Ultimos 7 dias'
					? movimentacoesNoPeriodo.length === 1
						? 'Movimentação (7 dias)'
						: 'Movimentações (7 dias)'
					: dashboardFilter === 'Ultimos Mês'
						? movimentacoesNoPeriodo.length === 1
							? 'Movimentação (mês)'
							: 'Movimentações (mês)'
						: dashboardFilter === 'Data selecionada'
							? movimentacoesNoPeriodo.length === 1
								? 'Movimentação na data'
								: 'Movimentações na data'
							: movimentacoesNoPeriodo.length === 1
								? 'Movimentação total'
								: 'Movimentações totais'
	);

	let movimentacoesCardDescription = $derived(
		dashboardFilter === 'Hoje'
			? 'Total de movimentações realizadas hoje'
			: dashboardFilter === 'Ontem'
				? 'Total de movimentações realizadas ontem'
				: dashboardFilter === 'Ultimos 7 dias'
					? 'Total de movimentações nos últimos 7 dias'
					: dashboardFilter === 'Ultimos Mês'
						? 'Total de movimentações nos últimos 30 dias'
						: dashboardFilter === 'Data selecionada'
							? 'Total de movimentações para a data selecionada'
							: 'Total de movimentações registradas'
	);

	$effect(() => {
		if (selectedDate) {
			dashboardFilter = 'Data selecionada';
		} else if (dashboardFilter === 'Data selecionada') {
			dashboardFilter = 'Todos';
		}
	});

	let filteredMovimentacoes = $derived(
		movimentacoesNoPeriodo.filter((item) => {
			const search = normalize(searchTerm);
			return normalize(item?.search_index || '').includes(search);
		}) || []
	);
</script>

<div class="main-content p-8">
	<div class="header">
		<h1>Monitoramento de Produção</h1>
		<p>Visão em tempo real do fluxo de itens e análise de eficiência da linha.</p>
	</div>
	{#if dashboardError}
		<div class="mt-4 rounded-lg bg-red-100 p-4 text-center text-red-700">
			{dashboardError}
		</div>
	{/if}

	{#if dashboard}
		<div class="mt-6 mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
			<div class="flex flex-wrap gap-2">
				<Button
					size="sm"
					outline={dashboardFilter !== 'Hoje'}
					color={dashboardFilter === 'Hoje' ? 'orange' : 'dark'}
					onclick={() => {
						dashboardFilter = 'Hoje';
						selectedDate = undefined;
					}}
				>
					Hoje
				</Button>
				<Button
					size="sm"
					outline={dashboardFilter !== 'Ontem'}
					color={dashboardFilter === 'Ontem' ? 'orange' : 'dark'}
					onclick={() => {
						dashboardFilter = 'Ontem';
						selectedDate = undefined;
					}}
				>
					Ontem
				</Button>
				<Button
					size="sm"
					outline={dashboardFilter !== 'Todos'}
					color={dashboardFilter === 'Todos' ? 'orange' : 'dark'}
					onclick={() => {
						dashboardFilter = 'Todos';
						selectedDate = undefined;
					}}
				>
					Todos
				</Button>
				<Button
					size="sm"
					outline={dashboardFilter !== 'Ultimos 7 dias'}
					color={dashboardFilter === 'Ultimos 7 dias' ? 'orange' : 'dark'}
					onclick={() => {
						dashboardFilter = 'Ultimos 7 dias';
						selectedDate = undefined;
					}}
				>
					Ultimos 7 dias
				</Button>
				<Button
					size="sm"
					outline={dashboardFilter !== 'Ultimos Mês'}
					color={dashboardFilter === 'Ultimos Mês' ? 'orange' : 'dark'}
					onclick={() => {
						dashboardFilter = 'Ultimos Mês';
						selectedDate = undefined;
					}}
				>
					Ultimos Mês
				</Button>

				<div class="w-full sm:w-auto">
					<Datepicker
						color="dark"
						placeholder="Filtrar por data"
						locale="pt-BR"
						dateFormat={{ year: 'numeric', month: '2-digit', day: '2-digit' }}
						bind:value={selectedDate}
						inputClass="w-full sm:w-48"
					/>
				</div>
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
				title="Lotes registrados"
				description="Total de lotes no banco de dados"
				value={dashboard.total_lotes}
			/>
			<InfoCard
				data-variant="Up"
				title={sensorStore.onlineCount === 1 ? 'Sensor Ativo' : 'Sensores Ativos'}
				description="Sensores online no momento"
				value={sensorStore.onlineCount}
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

		{#if lastDashboardUpdate}
			<div class="mb-2 text-right text-xs text-gray-500 dark:text-gray-300">
				Atualizado {lastDashboardUpdate.toLocaleTimeString('pt-BR')}
			</div>
		{/if}

		<TableSearch
			placeholder="Buscar por produto, câmara, movimentação ou data..."
			hoverable={true}
			bind:inputValue={searchTerm}
			divClass="overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-none border border-gray-300 dark:border-gray-300"
			innerDivClass="flex flex-col md:flex-row items-center justify-between p-4 gap-4"
			searchClass="w-full md:w-1/2"
		>
			<TableHead>
				<TableHeadCell>Produto</TableHeadCell>
				<TableHeadCell>Câmara</TableHeadCell>
				<TableHeadCell>Movimentação</TableHeadCell>
				<TableHeadCell>Data/Hora</TableHeadCell>
			</TableHead>
			<TableBody>
				{#each filteredMovimentacoes as movimentacao}
					<TableBodyRow>
						<TableBodyCell>{movimentacao.produto}</TableBodyCell>
						<TableBodyCell>{movimentacao.camara}</TableBodyCell>
						<TableBodyCell>{movimentacao.movimentacao}</TableBodyCell>
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
	{/if}
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
