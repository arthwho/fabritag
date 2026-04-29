<script lang="ts">
	import { enhance } from '$app/forms';
	import { onMount } from 'svelte';
	import { tick } from 'svelte';
	import { A, Alert, Button, Checkbox, InfoCircleSolid, Input, Label } from '$lib/uicomponents.js';

	let { form, data } = $props();

	type RegisterFormPayload = {
		error?: string;
		fieldValues?: {
			nomeCompleto?: string;
			email?: string;
			isAlsoCliente?: boolean;
			cpfCnpj?: string;
		};
	};

	let actionResult = $derived((form || null) as RegisterFormPayload | null);
	let nomeCompleto = $state('');
	let email = $state('');
	let password = $state('');
	let isAlsoCliente = $state(false);
	let cpfCnpj = $state('');
	let isSubmitting = $state(false);
	let formError = $state('');
	let googleIdToken = $state('');
	let googleContainer = $state<HTMLDivElement | null>(null);
	let googleForm = $state<HTMLFormElement | null>(null);
	const googleClientId = $derived(
		String(data?.googleClientId || import.meta.env.PUBLIC_GOOGLE_CLIENT_ID || '').trim()
	);

	const handleRegisterSubmit = () => {
		isSubmitting = true;
		formError = '';

		return async ({ result, update }) => {
			isSubmitting = false;
			await update();
			if (result.type === 'error') {
				formError = 'Não foi possível concluir o registro.';
			}
		};
	};

	$effect(() => {
		if (!actionResult) return;
		if (actionResult.error) {
			formError = actionResult.error;
		}
		if (typeof actionResult.fieldValues?.nomeCompleto === 'string') {
			nomeCompleto = actionResult.fieldValues.nomeCompleto;
		}
		if (typeof actionResult.fieldValues?.email === 'string') {
			email = actionResult.fieldValues.email;
		}
		if (typeof actionResult.fieldValues?.isAlsoCliente === 'boolean') {
			isAlsoCliente = actionResult.fieldValues.isAlsoCliente;
		}
		if (typeof actionResult.fieldValues?.cpfCnpj === 'string') {
			cpfCnpj = actionResult.fieldValues.cpfCnpj;
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
			<h1>Registrar Novo Usuário</h1>
			<p>Crie sua conta para acessar o sistema.</p>
		</div>

		{#if formError}
			<Alert class="mb-4">
				{#snippet icon()}<InfoCircleSolid class="h-4 w-4" />{/snippet}
				{formError}
			</Alert>
		{/if}

		<form method="POST" action="?/register" class="space-y-4" use:enhance={handleRegisterSubmit}>
			<div>
				<Label for="registro-nome-completo">Nome completo</Label>
				<Input
					id="registro-nome-completo"
					name="nomeCompleto"
					placeholder="Nome e sobrenome"
					required
					bind:value={nomeCompleto}
				/>
			</div>
			<div>
				<Label for="registro-email">Email</Label>
				<Input
					id="registro-email"
					name="email"
					type="email"
					required
					autocomplete="username"
					bind:value={email}
				/>
			</div>
			<div>
				<Label for="registro-password">Senha</Label>
				<Input
					id="registro-password"
					name="password"
					type="password"
					required
					minlength={6}
					autocomplete="new-password"
					bind:value={password}
				/>
			</div>

			<div class="rounded-lg border border-gray-200 p-3">
				<Checkbox id="registro-is-cliente" name="isAlsoCliente" bind:checked={isAlsoCliente}>
					Usuário também será cliente
				</Checkbox>
			</div>

			{#if isAlsoCliente}
				<div>
					<Label for="registro-cpf-cnpj">CPF/CNPJ</Label>
					<Input
						id="registro-cpf-cnpj"
						name="cpfCnpj"
						placeholder="000.000.000-00 ou 00.000.000/0000-00"
						bind:value={cpfCnpj}
						required={isAlsoCliente}
					/>
				</div>
			{/if}

			<Button class="w-full" type="submit" color="orange" disabled={isSubmitting}>Registrar</Button>
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
			Já possui conta?
			<A href="/login" class="font-medium text-orange-700 hover:underline">Acessar login</A>
		</p>
	</div>
</div>
