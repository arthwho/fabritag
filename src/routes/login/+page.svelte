<script lang="ts">
	import { enhance } from '$app/forms';
	import { onMount } from 'svelte';
	import { tick } from 'svelte';
	import { A, Alert, Button, InfoCircleSolid, Input, Label } from '$lib/uicomponents.js';

	let { form, data } = $props();

	type LoginFormPayload = {
		error?: string;
		fieldValues?: {
			email?: string;
		};
	};

	let actionResult = $derived((form || null) as LoginFormPayload | null);
	let email = $state('');
	let password = $state('');
	let isSubmitting = $state(false);
	let formError = $state('');
	let googleIdToken = $state('');
	let googleContainer = $state<HTMLDivElement | null>(null);
	let googleForm = $state<HTMLFormElement | null>(null);
	const googleClientId = $derived(
		String(data?.googleClientId || import.meta.env.PUBLIC_GOOGLE_CLIENT_ID || '').trim()
	);

	const handleLoginSubmit = () => {
		isSubmitting = true;
		formError = '';

		return async ({ result, update }) => {
			isSubmitting = false;
			await update();
			if (result.type === 'error') {
				formError = 'Não foi possível concluir o login.';
			}
		};
	};

	$effect(() => {
		if (!actionResult) return;
		if (actionResult.error) {
			formError = actionResult.error;
		}
		if (actionResult.fieldValues?.email) {
			email = actionResult.fieldValues.email;
		}
	});

	onMount(() => {
		if (!googleClientId || !googleContainer) return;

		const initGoogle = () => {
			const google = (window as any)?.google;
			if (!google?.accounts?.id) return;

			google.accounts.id.initialize({
				client_id: googleClientId,
				callback: async (response: { credential?: string }) => {
					googleIdToken = response?.credential || '';
					if (googleIdToken) {
						await tick();
						googleForm?.requestSubmit();
					}
				}
			});

			google.accounts.id.renderButton(googleContainer, {
				type: 'standard',
				theme: 'outline',
				size: 'large',
				text: 'signin_with'
			});
		};

		if ((window as any)?.google?.accounts?.id) {
			initGoogle();
			return;
		}

		const script = document.createElement('script');
		script.src = 'https://accounts.google.com/gsi/client';
		script.async = true;
		script.defer = true;
		script.onload = initGoogle;
		document.head.appendChild(script);
	});
</script>

<div class="flex min-h-screen items-center justify-center bg-neutral-100 p-6">
	<div class="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
		<div class="header mb-6">
			<h1>Acesso ao Sistema</h1>
			<p>Entre com seu usuário cadastrado para continuar.</p>
		</div>

		{#if formError}
			<Alert class="mb-4">
				{#snippet icon()}<InfoCircleSolid class="h-4 w-4" />{/snippet}
				{formError}
			</Alert>
		{/if}

		<form method="POST" action="?/login" class="space-y-4" use:enhance={handleLoginSubmit}>
			<div>
				<Label for="login-email">Email</Label>
				<Input
					id="login-email"
					name="email"
					type="email"
					required
					autocomplete="username"
					bind:value={email}
				/>
			</div>
			<div>
				<Label for="login-password">Senha</Label>
				<Input
					id="login-password"
					name="password"
					type="password"
					required
					autocomplete="current-password"
					bind:value={password}
				/>
			</div>
			<Button class="w-full" type="submit" color="orange" disabled={isSubmitting}>Entrar</Button>
		</form>

		<div class="my-4 flex items-center gap-3 text-xs text-gray-500">
			<div class="h-px flex-1 bg-gray-200"></div>
			<span>ou continue com Google</span>
			<div class="h-px flex-1 bg-gray-200"></div>
		</div>

		<form method="POST" action="?/google" class="mt-4 w-full" bind:this={googleForm}>
			<input type="hidden" name="idToken" value={googleIdToken} />
			{#if googleClientId}
				<div class="w-full" bind:this={googleContainer}></div>
			{:else}
				<p class="text-xs text-gray-500">
					Login Google indisponível: configure PUBLIC_GOOGLE_CLIENT_ID.
				</p>
			{/if}
		</form>

		<p class="mt-4 text-xs text-gray-500">
			Não possui conta?
			<A href="/registro" class="font-medium text-orange-700 hover:underline">Criar novo usuário</A>
		</p>

		<p class="mt-4 text-xs text-gray-500">Usuário inicial: admin@fabritag.com | senha: admin123</p>
	</div>
</div>
