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
			const quantity = Math.max(1, Math.floor(lote.quantidade || 1));
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
				posicao: quantity > 1 
					? `${getPosStr(startPos)} - ${getPosStr(endPos)}`
					: getPosStr(startPos)
			};
		});
	});

	const occupiedPositions = $derived.by(() => {
		const map = new Map();
		lotesWithPositions.forEach(lote => {
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
	<a href="/infraestrutura" class="mb-6 inline-flex items-center gap-1 text-sm font-medium text-gray-600 hover:text-orange-600 dark:text-gray-400 dark:hover:text-orange-500 transition-colors">
		<ChevronLeftOutline class="w-4 h-4" />
		Voltar para Infraestrutura
	</a>

	{#if error}
		<div class="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-gray-800 dark:text-red-400 border border-red-200" role="alert">
			{error}
		</div>
	{:else if camara}
		<div class="mb-8">
			<h1 class="h1 text-gray-900 dark:text-white">{camara.nome}</h1>
			<p class="text-gray-500 dark:text-gray-400 mt-1">ID: {camara.id} • Prédio: {camara.predio}</p>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
			<InfoCard 
				title="Capacidade" 
				description="Total de vagas físicas" 
				value={camara.capacidade || 'N/A'} 
			/>
			<InfoCard 
				title="Ocupação" 
				description="Espaços físicos ocupados" 
				value={`${numOccupiedSpaces} / ${capacity}`} 
			/>
			<InfoCard 
				title="Status" 
				description="Estado de operação" 
				value="Operacional"
			>
				{#snippet badge()}
					<Badge color="green" class="rounded-full">Ativo</Badge>
				{/snippet}
			</InfoCard>
		</div>

		<!-- 2D Grid Representation -->
		<div class="mb-10 bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-300 dark:border-gray-700">
			<div class="flex items-center justify-between mb-6">
				<div>
					<h2 class="text-lg font-bold text-gray-900 dark:text-white">Mapa de Ocupação</h2>
					<p class="text-xs text-gray-500">Representação visual das prateleiras industriais</p>
				</div>
				<div class="flex gap-4 text-xs">
					<div class="flex items-center gap-1.5">
						<div class="w-3 h-3 bg-orange-500 rounded-sm"></div>
						<span class="text-gray-600 dark:text-gray-400">Ocupado</span>
					</div>
					<div class="flex items-center gap-1.5">
						<div class="w-3 h-3 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-sm"></div>
						<span class="text-gray-600 dark:text-gray-400">Disponível</span>
					</div>
				</div>
			</div>

			<div class="overflow-x-auto pb-2">
				<div class="inline-grid gap-2" style="grid-template-columns: auto repeat({cols}, minmax(40px, 1fr));">
					<!-- Header Row (Columns A, B, C...) -->
					<div class="w-8"></div>
					{#each Array(cols) as _, c}
						<div class="text-center text-[10px] font-bold text-gray-400 uppercase">{getColumnLetter(c + 1)}</div>
					{/each}

					<!-- Grid Rows -->
					{#each Array(rows) as _, r}
						<!-- Row Label (1, 2, 3...) -->
						<div class="flex items-center justify-end pr-2 text-[10px] font-bold text-gray-400">{r + 1}</div>
						
						{#each Array(cols) as _, c}
							{@const cellIndex = r * cols + c}
							{@const occupant = getOccupant(r + 1, c + 1)}
							{#if cellIndex < capacity}
								<div 
									class="aspect-square rounded-md border flex items-center justify-center transition-all duration-200 {occupant ? 'bg-orange-500 border-orange-600 shadow-sm' : 'bg-gray-50 dark:bg-gray-700/30 border-gray-200 dark:border-gray-600'}"
									title={occupant ? `Lote: ${occupant.epc_tag}\nPosição: ${getColumnLetter(c + 1)}${r + 1}` : `Posição ${getColumnLetter(c + 1)}${r + 1}: Disponível`}
								>
									{#if occupant}
										<div class="w-1.5 h-1.5 bg-white/40 rounded-full animate-pulse"></div>
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

		<div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-700 overflow-hidden shadow-none">
			<div class="p-5 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-800/50">
				<h2 class="text-lg font-bold text-gray-900 dark:text-white">Lotes Presentes na Câmara</h2>
				<span class="text-xs font-medium text-gray-500 bg-gray-200 dark:bg-gray-700 px-2.5 py-1 rounded-md">{camara.lotes.length} Lotes</span>
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
							<TableBodyCell class="font-mono text-xs text-gray-600 dark:text-gray-400">{lote.epc_tag}</TableBodyCell>
							<TableBodyCell class="font-medium text-gray-900 dark:text-white">{lote.produto}</TableBodyCell>
							<TableBodyCell class="text-gray-600 dark:text-gray-400">{lote.data_entrada}</TableBodyCell>
							<TableBodyCell class="text-right">
								<a href={`/movimentacao?search=${lote.epc_tag}`} class="font-semibold text-orange-600 hover:text-orange-700 dark:text-orange-500 dark:hover:text-orange-400 transition-colors">
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
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mb-4"></div>
			<p class="text-gray-500 animate-pulse">Carregando detalhes da câmara...</p>
		</div>
	{/if}
</div>

<style>
	.h1 {
		font-size: 32px;
		font-family: Inter, sans-serif;
		font-weight: 800;
		line-height: 1.2;
		letter-spacing: -0.02em;
	}
</style>
