<script>
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '../lib/components/sidebar.svelte';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div class="ml-72 flex min-h-screen bg-neutral-100">
	<Sidebar />
	<main class="flex-1">
		{@render children()}
	</main>
</div>
