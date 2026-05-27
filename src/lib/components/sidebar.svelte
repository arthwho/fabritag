<script lang="ts">
	import { Sidebar, SidebarGroup, SidebarItem, SidebarBrand } from 'flowbite-svelte';
	import {
		ChartPieOutline,
		BuildingOutline,
		TagOutline,
		UsersGroupOutline,
		UserHeadsetOutline,
		BookOutline,
		LifeSaverOutline,
		UserSettingsOutline,
		ChartPieSolid,
		BuildingSolid,
		TagSolid,
		UsersGroupSolid,
		UserHeadsetSolid,
		BookSolid,
		LifeSaverSolid,
		UserSettingsSolid
	} from 'flowbite-svelte-icons';
	import { page } from '$app/stores';
	import logo from '$lib/assets/logo-on-white.svg';

	const spanClass = 'flex-1 ms-3 whitespace-nowrap';
	const spanActiveClass = 'flex-1 ms-3 whitespace-nowrap text-orange-700';
	const site = {
		href: '/',
		img: logo
	};
	const activeClass =
		'flex items-center p-2 text-base font-normal text-orange-700 bg-neutral-200 rounded-lg hover:bg-neutral-100';
	const nonActiveClass =
		'flex items-center p-2 text-base font-normal text-black-900 rounded-lg hover:bg-neutral-200 ';
</script>

<Sidebar
	activeUrl={$page.url.pathname}
	class="h-screen w-72 border-r border-gray-200 bg-surface"
	divClass="h-full flex flex-col bg-surface"
	position="fixed"
>
	<SidebarGroup>
		<SidebarBrand {site} classes={{ img: 'w-32' }} />
		<SidebarItem label="Dashboard" href="/dashboard" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				{#if $page.url.pathname.startsWith('/dashboard')}
					<ChartPieSolid class="h-5 w-5 text-orange-700 transition duration-75 dark:text-white" />
				{:else}
					<ChartPieOutline
						class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
					/>
				{/if}
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
				{#if $page.url.pathname.startsWith('/infraestrutura')}
					<BuildingSolid class="h-5 w-5 text-orange-700" />
				{:else}
					<BuildingOutline
						class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
					/>
				{/if}
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Produtos" href="/produtos" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				{#if $page.url.pathname.startsWith('/produtos')}
					<TagSolid class="h-5 w-5 text-orange-700" />
				{:else}
					<TagOutline
						class="h-5 w-5 text-gray-500 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
					/>
				{/if}
			{/snippet}
		</SidebarItem>
		<!-- <SidebarItem label="Relatórios" href="/relatorios" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<ChartOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem> -->
	</SidebarGroup>
	<SidebarGroup
		border
		borderClass="space-y-2 pt-4 mt-4 border-t border-gray-200 dark:border-gray-700"
	>
		<SidebarItem label="Clientes" href="/clientes" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				{#if $page.url.pathname.startsWith('/clientes')}
					<UsersGroupSolid class="h-5 w-5 text-orange-700 transition duration-75 dark:text-white" />
				{:else}
					<UsersGroupOutline
						class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
					/>
				{/if}
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Usuários" href="/usuarios" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				{#if $page.url.pathname.startsWith('/usuarios')}
					<UserSettingsSolid
						class="h-5 w-5 text-orange-700 transition duration-75 dark:text-white"
					/>
				{:else}
					<UserSettingsOutline
						class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
					/>
				{/if}
			{/snippet}
		</SidebarItem>
	</SidebarGroup>
	<SidebarGroup
		border
		borderClass="space-y-2 pt-4 mt-4 border-t border-gray-200 dark:border-gray-700"
	>
		<SidebarItem label="Suporte" href="/suporte" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				{#if $page.url.pathname.startsWith('/suporte')}
					<UserHeadsetSolid
						class="h-5 w-5 text-orange-700 transition duration-75 dark:text-white"
					/>
				{:else}
					<UserHeadsetOutline
						class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
					/>
				{/if}
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Docs" href="/docs" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				{#if $page.url.pathname.startsWith('/docs')}
					<BookSolid class="h-5 w-5 text-orange-700 transition duration-75 dark:text-white" />
				{:else}
					<BookOutline
						class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
					/>
				{/if}
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Ajuda" href="/ajuda" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				{#if $page.url.pathname.startsWith('/ajuda')}
					<LifeSaverSolid class="h-5 w-5 text-orange-700 transition duration-75 dark:text-white" />
				{:else}
					<LifeSaverOutline
						class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
					/>
				{/if}
			{/snippet}
		</SidebarItem>
	</SidebarGroup>
</Sidebar>
