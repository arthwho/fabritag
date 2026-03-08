<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		description: string;
		value: string | number;
		badge?: Snippet;
		class?: string;
		[key: string]: any;
	}

	let { title, description, value, badge, class: className = '', ...props }: Props = $props();
</script>

<div class="card rounded-xl border border-gray-300 bg-white p-6 shadow-none {className}" {...props}>
	<div class="flex flex-col gap-4">
		<div class="flex items-center justify-between gap-3">
			<span class="block text-2xl leading-9 font-bold text-[#22272a]">{value}</span>
			{#if badge}
				<div class="shrink-0">{@render badge()}</div>
			{/if}
		</div>
		<div>
			<span class="block text-lg leading-7 font-bold text-[#22272a]">{title}</span>
			<span class="text-xs leading-5 font-normal text-[#383e41]">{description}</span>
		</div>
	</div>
</div>
