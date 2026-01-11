<script>
	export let title;
	export let value;
	export let icon;
	export let color = 'blue';
</script>

<div
	class="flex items-center justify-between rounded-lg border border-gray-100 bg-white p-6 shadow-sm"
>
	<div>
		<p class="mb-1 text-sm font-medium text-gray-500">{title}</p>
		<h3 class="text-2xl font-bold text-gray-800">{value}</h3>
	</div>
	<div class={`rounded-full p-3 bg-${color}-50 text-${color}-600`}>
		<svelte:component this={icon} size={24} />
	</div>
</div>
