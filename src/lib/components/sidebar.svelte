<script lang="ts">
	import {
		Sidebar,
		SidebarGroup,
		SidebarItem,
		SidebarBrand,
		SidebarDropdownWrapper
	} from 'flowbite-svelte';
	import {
		ChartPieOutline,
		BuildingOutline,
		HomeOutline,
		ChartOutline,
		TagOutline,
		BarcodeOutline,
		UsersGroupOutline,
		UserHeadsetOutline,
		BookOutline,
		LifeSaverOutline
	} from 'flowbite-svelte-icons';
	import { ArrowRightLeft } from 'lucide-svelte';
	import { page } from '$app/stores';
	import logo from '$lib/assets/logo-on-white.svg';

	const spanClass = 'flex-1 ms-3 whitespace-nowrap';
	const site = {
		href: '/',
		img: logo
	};
	const activeClass =
		'flex items-center p-2 text-base font-normal text-orange-700 bg-neutral-200 dark:bg-orange-700 rounded-lg dark:text-white hover:bg-neutral-100 dark:hover:bg-gray-700';
	const nonActiveClass =
		'flex items-center p-2 text-base font-normal text-black-900 rounded-lg dark:text-white hover:bg-neutral-200 dark:hover:bg-neutral-700';
</script>

<Sidebar activeUrl={$page.url.pathname} class="h-full w-72" position="absolute">
	<SidebarGroup>
		<SidebarBrand {site} classes={{ img: 'w-32' }} />
		<SidebarItem label="Dashboard" href="/dashboard" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<ChartPieOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
		<SidebarItem
			label="Infraestrutura"
			href="/infraestrutura"
			{spanClass}
			{activeClass}
			{nonActiveClass}
		>
			{#snippet icon()}
				<BuildingOutline
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
		<SidebarItem
			label="Movimentar lote"
			href="/movimentacao"
			{spanClass}
			{activeClass}
			{nonActiveClass}
		>
			{#snippet icon()}
				<ArrowRightLeft
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Relatórios" href="/relatorios" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<ChartOutline
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
	<SidebarGroup border>
		<SidebarItem label="Suporte" href="/suporte" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<UserHeadsetOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Docs" href="/docs" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<BookOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Ajuda" href="/ajuda" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<LifeSaverOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
	</SidebarGroup>
</Sidebar>
