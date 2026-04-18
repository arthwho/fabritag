<script lang="ts">
	import {
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Badge,
		ChevronLeftOutline
	} from '$lib/uicomponents.js';
	import InfoCard from '$lib/components/InfoCard.svelte';

	let { data } = $props();
	const camara = $derived(data.camara);
	const error = $derived(data.error);
	const warning = $derived(data.camara?.warning || null);

	// Helper to convert number to Excel-style column (A, B, C... Z, AA, AB...)
	function getColumnLetter(n: number): string {
		let letter = '';
		while (n > 0) {
			let temp = (n - 1) % 26;
			letter = String.fromCharCode(temp + 65) + letter;
			n = (n - temp - 1) / 26;
		}
		return letter;
	}

	// Grid calculations
	const capacity = $derived(camara?.capacidade || 0);

	// Determine grid dimensions (try to keep it somewhat square or wider)
	const cols = $derived(Math.ceil(Math.sqrt(capacity * 1.5)) || 1);
	const rows = $derived(Math.ceil(capacity / cols) || 0);

	// Map lotes to positions based on their quantity (size) and stored posicao_vaga
	const lotesWithPositions = $derived.by(() => {
		if (!camara?.lotes) return [];

		return camara.lotes.map((lote) => {
			const startPos = lote.posicao_vaga ?? 0;
			const quantity = Math.max(1, Math.ceil(lote.quantidade || 1));
			const endPos = startPos + quantity - 1;

			// Generate position string (e.g., "A1" or "A1-B1")
			const getPosStr = (idx: number) => {
				const r = Math.floor(idx / cols) + 1;
				const c = (idx % cols) + 1;
				return `${getColumnLetter(c)}${r}`;
			};

			return {
				...lote,
				quantity,
				startPos,
				endPos,
				posicao:
					quantity > 1 ? `${getPosStr(startPos)} - ${getPosStr(endPos)}` : getPosStr(startPos)
			};
		});
	});

	const occupiedPositions = $derived.by(() => {
		const map = new Map();
		lotesWithPositions.forEach((lote) => {
			for (let i = lote.startPos; i <= lote.endPos; i++) {
				map.set(i, lote);
			}
		});
		return map;
	});

	function getOccupant(r: number, c: number) {
		const index = (r - 1) * cols + (c - 1);
		return occupiedPositions.get(index);
	}

	const numOccupiedSpaces = $derived(
		lotesWithPositions.reduce((acc, lote) => acc + lote.quantity, 0)
	);
</script>

<div class="p-6">
	<a
		href="/infraestrutura"
		class="mb-6 inline-flex items-center gap-1 text-sm font-medium text-gray-600 transition-colors hover:text-orange-600 dark:text-gray-400 dark:hover:text-orange-500"
	>
		<ChevronLeftOutline class="h-4 w-4" />
		Voltar para Infraestrutura
	</a>

	{#if error}
		<div
			class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:bg-gray-800 dark:text-red-400"
			role="alert"
		>
			{error}
		</div>
	{:else if camara}
		<div class="mb-8">
			<h1 class="h1 text-gray-900 dark:text-white">{camara.nome}</h1>
			<p class="mt-1 text-gray-500 dark:text-gray-400">ID: {camara.id} • Prédio: {camara.predio}</p>
		</div>

		{#if warning}
			<div
				class="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:bg-gray-800 dark:text-amber-300"
				role="alert"
			>
				{warning}
			</div>
		{/if}

		<div class="mb-10 grid grid-cols-1 gap-6 md:grid-cols-3">
			<InfoCard
				title="Capacidade"
				description="Total de vagas físicas"
				value={camara.capacidade || 'N/A'}
			/>
			<InfoCard
				title="Ocupação"
				description="Espaços físicos ocupados"
				value={`${camara.ocupacao_total ?? numOccupiedSpaces} / ${capacity}`}
			/>
			<InfoCard title="Status" description="Estado de operação" value="Operacional">
				{#snippet badge()}
					<Badge color="green" class="rounded-full">Ativo</Badge>
				{/snippet}
			</InfoCard>
		</div>

		<!-- 2D Grid Representation -->
		<div
			class="mb-10 rounded-xl border border-gray-300 bg-white p-6 dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="mb-6 flex items-center justify-between">
				<div>
					<h2 class="text-lg font-bold text-gray-900 dark:text-white">Mapa de Ocupação</h2>
					<p class="text-xs text-gray-500">Representação visual das prateleiras industriais</p>
				</div>
				<div class="flex gap-4 text-xs">
					<div class="flex items-center gap-1.5">
						<div class="h-3 w-3 rounded-sm bg-orange-500"></div>
						<span class="text-gray-600 dark:text-gray-400">Ocupado</span>
					</div>
					<div class="flex items-center gap-1.5">
						<div
							class="h-3 w-3 rounded-sm border border-gray-300 bg-gray-100 dark:border-gray-600 dark:bg-gray-700"
						></div>
						<span class="text-gray-600 dark:text-gray-400">Disponível</span>
					</div>
				</div>
			</div>

			<div class="overflow-x-auto pb-2">
				<div
					class="inline-grid gap-2"
					style="grid-template-columns: auto repeat({cols}, minmax(40px, 1fr));"
				>
					<!-- Header Row (Columns A, B, C...) -->
					<div class="w-8"></div>
					{#each Array(cols) as _, c}
						<div class="text-center text-[10px] font-bold text-gray-400 uppercase">
							{getColumnLetter(c + 1)}
						</div>
					{/each}

					<!-- Grid Rows -->
					{#each Array(rows) as _, r}
						<!-- Row Label (1, 2, 3...) -->
						<div class="flex items-center justify-end pr-2 text-[10px] font-bold text-gray-400">
							{r + 1}
						</div>

						{#each Array(cols) as _, c}
							{@const cellIndex = r * cols + c}
							{@const occupant = getOccupant(r + 1, c + 1)}
							{#if cellIndex < capacity}
								<div
									class="flex aspect-square items-center justify-center rounded-md border transition-all duration-200 {occupant
										? 'border-orange-600 bg-orange-500 shadow-sm'
										: 'border-gray-200 bg-gray-50 dark:border-gray-600 dark:bg-gray-700/30'}"
									title={occupant
										? `Lote: ${occupant.epc_tag}\nPosição: ${getColumnLetter(c + 1)}${r + 1}`
										: `Posição ${getColumnLetter(c + 1)}${r + 1}: Disponível`}
								>
									{#if occupant}
										<div class="h-1.5 w-1.5 animate-pulse rounded-full bg-white/40"></div>
									{/if}
								</div>
							{:else}
								<div class="aspect-square"></div>
							{/if}
						{/each}
					{/each}
				</div>
			</div>
		</div>

		<div
			class="overflow-hidden rounded-xl border border-gray-300 bg-white shadow-none dark:border-gray-700 dark:bg-gray-800"
		>
			<div
				class="flex items-center justify-between border-b border-gray-200 bg-gray-50 p-5 dark:border-gray-700 dark:bg-gray-800/50"
			>
				<h2 class="text-lg font-bold text-gray-900 dark:text-white">Lotes Presentes na Câmara</h2>
				<span
					class="rounded-md bg-gray-200 px-2.5 py-1 text-xs font-medium text-gray-500 dark:bg-gray-700"
					>{camara.lotes.length} Lotes</span
				>
			</div>
			<Table hoverable={true} shadow={false} divClass="overflow-x-auto">
				<TableHead class="bg-gray-50 dark:bg-gray-700">
					<TableHeadCell>Posição</TableHeadCell>
					<TableHeadCell>Tamanho</TableHeadCell>
					<TableHeadCell>EPC Tag</TableHeadCell>
					<TableHeadCell>Produto</TableHeadCell>
					<TableHeadCell>Data de Entrada</TableHeadCell>
					<TableHeadCell class="text-right">Ações</TableHeadCell>
				</TableHead>
				<TableBody>
					{#each lotesWithPositions as lote}
						<TableBodyRow>
							<TableBodyCell>
								<Badge color="orange" class="font-bold whitespace-nowrap">{lote.posicao}</Badge>
							</TableBodyCell>
							<TableBodyCell>
								<span class="text-sm text-gray-600 dark:text-gray-400">{lote.quantity}</span>
							</TableBodyCell>
							<TableBodyCell class="font-mono text-xs text-gray-600 dark:text-gray-400"
								>{lote.epc_tag}</TableBodyCell
							>
							<TableBodyCell class="font-medium text-gray-900 dark:text-white"
								>{lote.produto}</TableBodyCell
							>
							<TableBodyCell class="text-gray-600 dark:text-gray-400"
								>{lote.data_entrada}</TableBodyCell
							>
							<TableBodyCell class="text-right">
								<a
									href={`/movimentacao?search=${lote.epc_tag}`}
									class="font-semibold text-orange-600 transition-colors hover:text-orange-700 dark:text-orange-500 dark:hover:text-orange-400"
								>
									Ver Histórico
								</a>
							</TableBodyCell>
						</TableBodyRow>
					{:else}
						<TableBodyRow>
							<TableBodyCell colspan={6} class="text-center py-12 text-gray-500 italic">
								Nenhum lote presente nesta câmara no momento.
							</TableBodyCell>
						</TableBodyRow>
					{/each}
				</TableBody>
			</Table>
		</div>
	{:else}
		<div class="flex flex-col items-center justify-center p-20">
			<div class="mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-orange-600"></div>
			<p class="animate-pulse text-gray-500">Carregando detalhes da câmara...</p>
		</div>
	{/if}
</div>
