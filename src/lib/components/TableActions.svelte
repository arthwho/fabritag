<script lang="ts">
	import {
		Button,
		ChevronDownOutline,
		FilterOutline,
		Dropdown,
		DropdownItem
	} from '$lib/uicomponents.js';

	interface Props {
		idPrefix: string;
		filterOptions?: string[];
		exportOptions?: string[];
		filterLabel?: string;
		exportLabel?: string;
		class?: string;
		[key: string]: any;
	}

	let {
		idPrefix,
		filterOptions = ['Todos'],
		exportOptions = ['Excel (.xlsx)', 'PDF (.pdf)', 'CSV (.csv)'],
		filterLabel = 'Filtros',
		exportLabel = 'Exportar',
		class: className = '',
		...props
	}: Props = $props();

	let isFilterExpanded = $state(false);
	let selectedFilter = $state('Todos');

	$effect(() => {
		if (filterOptions.length === 0) {
			selectedFilter = 'Todos';
			return;
		}

		if (!filterOptions.includes(selectedFilter)) {
			selectedFilter = filterOptions[0];
		}
	});

	let filterButtonId = $derived(`${idPrefix}-filter-btn`);
	let exportButtonId = $derived(`${idPrefix}-export-btn`);
</script>

<div class={`flex flex-col gap-2 md:contents ${className}`} {...props}>
	<div class="flex justify-start gap-2 md:justify-end">
		<Button
			id={filterButtonId}
			outline
			size="sm"
			color="dark"
			class="gap-2"
			onclick={() => (isFilterExpanded = !isFilterExpanded)}
		>
			<FilterOutline class="h-4 w-4" />
			{filterLabel}
			<ChevronDownOutline class="h-4 w-4" />
		</Button>

		<Button id={exportButtonId} outline size="sm" color="dark" class="gap-2">
			{exportLabel}
			<ChevronDownOutline class="h-4 w-4" />
		</Button>
		<Dropdown triggeredBy={`#${exportButtonId}`}>
			{#each exportOptions as option}
				<DropdownItem>{option}</DropdownItem>
			{/each}
		</Dropdown>
	</div>

	{#if isFilterExpanded}
		<div class="flex w-full flex-wrap justify-start gap-2 md:basis-full">
			{#each filterOptions as option}
				<Button
					size="sm"
					outline={selectedFilter !== option}
					color={selectedFilter === option ? 'orange' : 'dark'}
					onclick={() => (selectedFilter = option)}
				>
					{option}
				</Button>
			{/each}
		</div>
	{/if}
</div>
