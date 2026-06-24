<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '../lib/components/sidebar.svelte';
	import GlobalLoteDetector from './GlobalLoteDetector.svelte';
	import { Button, Dropdown, DropdownItem, Avatar, DropdownGroup } from 'flowbite-svelte';
	import {
		AdjustmentsHorizontalOutline,
		ArrowRightToBracketOutline,
		UserOutline,
		BellSolid,
		EyeSolid,
		ChevronLeftOutline
	} from 'flowbite-svelte-icons';
	import { page } from '$app/stores';

	let { children, data } = $props();

	const pageTitle = $derived.by(() => $page.data.pageTitle || '');
	const pageDescription = $derived.by(() => $page.data.pageDescription || '');
	const pageBackHref = $derived.by(() => $page.data.pageBackHref || '');
	const pageBackLabel = $derived.by(() => $page.data.pageBackLabel || 'Voltar');
	let lotesSemProduto = $state([]);
	let notificationError = $state('');
	const notificationCount = $derived(lotesSemProduto.length);
	const displayName = $derived.by(() => {
		const user = data.currentUser;
		if (user?.nome_completo) return user.nome_completo;
		const email = user?.email || '';
		if (!email) return 'Usuário';
		const [namePart] = email.split('@');
		return namePart || 'Usuário';
	});
	async function refreshNotifications() {
		if ($page.url.pathname.startsWith('/login') || $page.url.pathname.startsWith('/registro')) {
			lotesSemProduto = [];
			return;
		}

		try {
			const response = await fetch('http://127.0.0.1:5000/api/produtos');
			if (!response.ok) return;

			const payload = await response.json();
			lotesSemProduto = Array.isArray(payload?.lotes_sem_produto) ? payload.lotes_sem_produto : [];
			notificationError = '';
		} catch (error) {
			notificationError = 'Nao foi possivel atualizar as notificacoes.';
		}
	}

	onMount(() => {
		refreshNotifications();
		const interval = setInterval(refreshNotifications, 3000);

		return () => clearInterval(interval);
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

{#if $page.url.pathname.startsWith('/login') || $page.url.pathname.startsWith('/registro')}
	<main class="min-h-screen bg-page">
		{@render children()}
	</main>
{:else}
	<div class="min-h-screen bg-page pl-72">
		<Sidebar />
		<main class="min-w-0">
			<header
				class="flex flex-col gap-4 border-b border-gray-200 bg-surface px-8 py-4 lg:flex-row lg:items-start lg:justify-between"
			>
				{#if pageTitle}
					<div class="flex min-w-0 items-center gap-3">
						{#if pageBackHref}
							<a
								href={pageBackHref}
								aria-label={pageBackLabel}
								title={pageBackLabel}
								class="mt-0.5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-gray-600 transition-colors hover:bg-gray-100 hover:text-orange-600 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-orange-500"
							>
								<ChevronLeftOutline class="h-5 w-5" />
							</a>
						{/if}
						<div class="min-w-0">
							<h1 class="m-0 text-2xl font-semibold text-gray-900 dark:text-white">{pageTitle}</h1>
							{#if pageDescription}
								<p class="mt-1 max-w-4xl text-sm text-gray-500 dark:text-gray-400">
									{pageDescription}
								</p>
							{/if}
						</div>
					</div>
				{/if}

				<div class="flex items-center justify-end gap-4 lg:ml-auto">
					<div
						id="bell"
						class="inline-flex items-center text-center text-sm font-medium text-gray-500 hover:text-gray-900 focus:outline-hidden dark:text-gray-400 dark:hover:text-white"
					>
						<BellSolid class="h-8 w-8" />
						{#if notificationCount > 0}
							<div class="relative flex">
								<div
									class="relative end-4 -top-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full border-2 border-white bg-red-500 px-1 text-xs font-semibold text-white dark:border-gray-900"
								>
									{notificationCount > 9 ? '9+' : notificationCount}
								</div>
							</div>
						{/if}
					</div>
					<Dropdown
						triggeredBy="#bell"
						class="w-full max-w-sm divide-y divide-gray-100 rounded-sm shadow-sm dark:divide-gray-700 dark:bg-gray-800"
					>
						<div class="py-2 text-center font-bold">Notificações</div>
						<DropdownGroup>
							{#if lotesSemProduto.length > 0}
								{#each lotesSemProduto as lote}
									<DropdownItem href="/produtos" class="flex space-x-4 rtl:space-x-reverse">
										<div
											class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-orange-100 text-sm font-semibold text-orange-700"
										>
											!
										</div>
										<div class="w-full ps-3">
											<div class="mb-1 text-sm text-gray-500 dark:text-gray-400">
												<span class="font-semibold text-gray-900 dark:text-white">
													Lote sem produto
												</span>
											</div>
											<div class="text-xs text-primary-600 dark:text-primary-500">
												EPC {lote.epc_tag} aguardando configuração.
											</div>
										</div>
									</DropdownItem>
								{/each}
							{:else if notificationError}
								<div class="px-4 py-3 text-sm text-red-600">{notificationError}</div>
							{:else}
								<div class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
									Nenhuma notificação no momento.
								</div>
							{/if}
						</DropdownGroup>
					</Dropdown>

					<Button class="min-w-0" color="light" size="sm" id="user-dropdown">
						<div class="flex w-full items-center gap-2 text-left">
							{#if data.currentUser?.foto_perfil_url}
								<img
									src={data.currentUser.foto_perfil_url}
									alt="Foto de perfil"
									class="h-8 w-8 rounded-full object-cover"
									referrerpolicy="no-referrer"
								/>
							{:else}
								<Avatar />
							{/if}
							<div class="leading-tight">
								<span class="block font-medium">{displayName}</span>
								<span class="block text-xs text-gray-500"
									>{data.currentUser?.email || 'Sem sessão'}</span
								>
							</div>
						</div>
					</Button>
					<Dropdown triggeredBy="#user-dropdown" placement="bottom-end">
						<DropdownItem class="flex items-center gap-2"><UserOutline />Conta</DropdownItem>
						<DropdownItem class="flex items-center gap-2" href="/settings">
							<AdjustmentsHorizontalOutline />Configurações
						</DropdownItem>
						<DropdownItem class="flex items-center gap-2 text-red-600" href="/logout">
							<ArrowRightToBracketOutline />Sair
						</DropdownItem>
					</Dropdown>
				</div>
			</header>
			{@render children()}
			<GlobalLoteDetector />
		</main>
	</div>
{/if}
