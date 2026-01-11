<script>
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '../components/sidebar.svelte';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div class="ml-64 flex min-h-screen">
	<Sidebar />
	<main class="flex-1">
		{@render children()}
	</main>
</div>
