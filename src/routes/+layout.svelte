<script>
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '../lib/components/sidebar.svelte';
	import { page } from '$app/stores';

	let { children, data } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

{#if $page.url.pathname.startsWith('/login') || $page.url.pathname.startsWith('/registro')}
	<main class="min-h-screen bg-page">
		{@render children()}
	</main>
{:else}
	<div class="min-h-screen bg-page pl-72">
		<Sidebar user={data.currentUser} />
		<main class="min-w-0">
			{@render children()}
		</main>
	</div>
{/if}
