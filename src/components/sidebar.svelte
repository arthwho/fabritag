<script lang="ts">
	import {
		Sidebar,
		SidebarGroup,
		SidebarItem,
		SidebarBrand,
		SidebarDropdownWrapper,
		uiHelpers
	} from 'flowbite-svelte';
	import {
		GridSolid,
		MailBoxSolid,
		UserSolid,
		ArrowRightToBracketOutline,
		EditSolid,
		ChartPieOutline,
		BuildingOutline,
		ChartOutline,
		TagOutline,
		BarcodeOutline,
		UsersGroupOutline,
		UserHeadsetOutline,
		BookOutline,
		LifeSaverOutline
	} from 'flowbite-svelte-icons';
	import { LayoutDashboard, Package, MapPin, ArrowRightLeft } from 'lucide-svelte';
	import { page } from '$app/state';
	import logo from '$lib/assets/logo-on-white.svg';
	let activeUrl = $state(page.url.pathname);
	const spanClass = 'flex-1 ms-3 whitespace-nowrap';
	$effect(() => {
		activeUrl = page.url.pathname;
	});
	const site = {
		href: '/',
		img: logo
	};
	const activeClass =
		'flex items-center p-2 text-base font-normal text-orange-700 bg-neutral-200 dark:bg-orange-700 rounded-lg dark:text-white hover:bg-neutral-100 dark:hover:bg-gray-700';
	const nonActiveClass =
		'flex items-center p-2 text-base font-normal text-black-900 rounded-lg dark:text-white hover:bg-neutral-200 dark:hover:bg-neutral-700';
	const sidebarMatch: string | string[] = 'docs/components/sidebar';
	const matchesRoute = $derived.by(() => {
		const list = Array.isArray(sidebarMatch) ? sidebarMatch : [sidebarMatch];
		return list.some((p) => activeUrl.startsWith(`/${p}`));
	});

	$effect(() => {
		activeUrl = page.url.pathname;
	});
</script>

<Sidebar {activeUrl} class="h-full w-64" position="absolute">
	<SidebarGroup>
		<SidebarBrand {site} classes={{ img: 'w-32' }} />
		<SidebarItem label="Dashboard" href="/dashboard" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<ChartPieOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
		<SidebarDropdownWrapper label="Infraestrutura" classes={{ btn: 'p-2' }} isOpen={matchesRoute}>
			{#snippet icon()}
				<BuildingOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
			<SidebarItem label="Armazéns" href="/ambientes/armazens" />
			<SidebarItem label="Blocos" href="/ambientes/blocos" />
		</SidebarDropdownWrapper>
		<SidebarItem label="Relatórios" href="/relatorios" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<ChartOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Produtos" href="/produtos" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<TagOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Sensores" href="/sensores" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<BarcodeOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Usuários" href="/usuarios" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<UsersGroupOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
	</SidebarGroup>
</Sidebar>
