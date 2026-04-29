<script lang="ts">
	import {
		Sidebar,
		SidebarGroup,
		SidebarItem,
		SidebarBrand,
		SidebarDropdownWrapper,
		Button,
		Dropdown,
		DropdownItem,
		Avatar,
		DropdownHeader,
		DropdownGroup,
		DropdownDivider
	} from 'flowbite-svelte';
	import {
		ChartPieOutline,
		BuildingOutline,
		TagOutline,
		UsersGroupOutline,
		UserHeadsetOutline,
		BookOutline,
		LifeSaverOutline,
		ArrowRightToBracketOutline,
		AdjustmentsHorizontalOutline,
		UserOutline,
		UserSettingsOutline
	} from 'flowbite-svelte-icons';
	import { ArrowRightLeft, User } from 'lucide-svelte';
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

	let { user = null } = $props();

	const displayName = $derived.by(() => {
		if (user?.nome_completo) return user.nome_completo;
		const email = user?.email || '';
		if (!email) return 'Usuário';
		const [namePart] = email.split('@');
		return namePart || 'Usuário';
	});
</script>

<Sidebar
	activeUrl={$page.url.pathname}
	class="h-screen w-72"
	divClass="h-full flex flex-col"
	position="fixed"
>
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
				<UsersGroupOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
		<SidebarItem label="Usuários" href="/usuarios" {spanClass} {activeClass} {nonActiveClass}>
			{#snippet icon()}
				<UserSettingsOutline
					class="h-5 w-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
				/>
			{/snippet}
		</SidebarItem>
	</SidebarGroup>
	<SidebarGroup
		border
		borderClass="space-y-2 pt-4 mt-4 border-t border-gray-200 dark:border-gray-700"
	>
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
	<div class="mt-auto mb-4 pt-6">
		<Button class="w-full" color="light" size="sm" id="user-dropdown">
			<div class="flex w-full items-center gap-2 text-left">
				{#if user?.foto_perfil_url}
					<img
						src={user.foto_perfil_url}
						alt="Foto de perfil"
						class="h-8 w-8 rounded-full object-cover"
						referrerpolicy="no-referrer"
					/>
				{:else}
					<Avatar />
				{/if}
				<div class="leading-tight">
					<span class="block font-medium">{displayName}</span>
					<span class="block text-xs text-gray-500">{user?.email || 'Sem sessão'}</span>
				</div>
			</div>
		</Button>
	</div>
	<Dropdown triggeredBy="#user-dropdown" placement="top-start">
		<DropdownItem class="flex items-center gap-2"><UserOutline />Conta</DropdownItem>
		<DropdownItem class="flex items-center gap-2" href="/settings">
			<AdjustmentsHorizontalOutline />Configurações</DropdownItem
		>
		<DropdownItem class="flex items-center gap-2 text-red-600" href="/logout"
			><ArrowRightToBracketOutline />Sair</DropdownItem
		>
	</Dropdown>
</Sidebar>
