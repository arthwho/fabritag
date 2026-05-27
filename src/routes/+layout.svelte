<script>
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '../lib/components/sidebar.svelte';
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
	const displayName = $derived.by(() => {
		const user = data.currentUser;
		if (user?.nome_completo) return user.nome_completo;
		const email = user?.email || '';
		if (!email) return 'Usuário';
		const [namePart] = email.split('@');
		return namePart || 'Usuário';
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
						<div class="relative flex">
							<div
								class="relative end-4 -top-2 inline-flex h-3 w-3 rounded-full border-2 border-white bg-red-500 dark:border-gray-900"
							></div>
						</div>
					</div>
					<Dropdown
						triggeredBy="#bell"
						class="w-full max-w-sm divide-y divide-gray-100 rounded-sm shadow-sm dark:divide-gray-700 dark:bg-gray-800"
					>
						<div class="py-2 text-center font-bold">Notificações</div>
						<DropdownGroup>
							<DropdownItem class="flex space-x-4 rtl:space-x-reverse">
								<Avatar src="/images/profile-picture-1.webp" dot={{ color: 'gray' }} />
								<div class="w-full ps-3">
									<div class="mb-1.5 text-sm text-gray-500 dark:text-gray-400">
										New message from <span class="font-semibold text-gray-900 dark:text-white"
											>Jese Leos</span
										>
										: "Hey, what's up? All set for the presentation?"
									</div>
									<div class="text-xs text-primary-600 dark:text-primary-500">
										a few moments ago
									</div>
								</div>
							</DropdownItem>
							<DropdownItem class="flex space-x-4 rtl:space-x-reverse">
								<Avatar src="/images/profile-picture-2.webp" dot={{ color: 'red' }} />
								<div class="w-full ps-3">
									<div class="mb-1.5 text-sm text-gray-500 dark:text-gray-400">
										<span class="font-semibold text-gray-900 dark:text-white">Joseph Mcfall</span>
										and
										<span class="font-medium text-gray-900 dark:text-white">5 others</span>
										started following you.
									</div>
									<div class="text-xs text-primary-600 dark:text-primary-500">10 minutes ago</div>
								</div>
							</DropdownItem>
							<DropdownItem class="flex space-x-4 rtl:space-x-reverse">
								<Avatar src="/images/profile-picture-3.webp" dot={{ color: 'green' }} />
								<div class="w-full ps-3">
									<div class="mb-1.5 text-sm text-gray-500 dark:text-gray-400">
										<span class="font-semibold text-gray-900 dark:text-white">Bonnie Green</span>
										and
										<span class="font-medium text-gray-900 dark:text-white">141 others</span>
										love your story. See it and view more stories.
									</div>
									<div class="text-xs text-primary-600 dark:text-primary-500">44 minutes ago</div>
								</div>
							</DropdownItem>
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
		</main>
	</div>
{/if}
