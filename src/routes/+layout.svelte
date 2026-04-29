<script>
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '../lib/components/sidebar.svelte';
	import { page } from '$app/stores';

	let { children, data } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

{#if $page.url.pathname.startsWith('/login') || $page.url.pathname.startsWith('/registro')}
	<main class="min-h-screen bg-neutral-100">
		{@render children()}
	</main>
{:else}
	<div class="ml-72 flex min-h-screen bg-neutral-100">
		<Sidebar user={data.currentUser} />
		<main class="flex-1">
			{@render children()}
		</main>
	</div>
{/if}
