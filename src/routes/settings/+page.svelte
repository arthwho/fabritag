<script lang="ts">
	import { Label, Input, Button } from '$lib/uicomponents.js';
	import { InfoCircleOutline } from 'flowbite-svelte-icons';
	import Section from '$lib/components/Container.svelte';

	let { data } = $props();

	let buttons = [
		{ name: 'Perfil', href: '/settings/profile' },
		{ name: 'Conta', href: '/settings/account' },
		{ name: 'Notificações', href: '/settings/notifications' },
		{ name: 'Privacidade', href: '/settings/privacy' }
	];
</script>

<div class="main-content p-8">
	<div class="header">
		<h1>Configurações</h1>
		<p>Gerencie suas preferências e configurações de conta.</p>
	</div>

	<div class="header">
		<h1>Configurar meu fabritag</h1>
	</div>

	<div class="mt-6 mb-6">
		<div class="mb-4 flex items-center justify-between">
			<Section>
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded bg-orange-50 font-semibold text-orange-800"
					>
						1
					</div>
					<p class="text-base">Conecte seu fabritag ao computador.</p>
				</div>
				<img class="mx-auto mt-4 block" src="src\lib\assets\connect-usb.svg" alt="Passo 1" />
			</Section>
		</div>
	</div>

	<div class="mt-6 mb-6 grid grid-cols-1 gap-8 md:grid-cols-2">
		<Section
			><Section
				><div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded bg-orange-50 font-semibold text-orange-800"
					>
						2
					</div>
					<p class="text-base">Configuração do fabritag</p>
				</div>
				<div class="block"><InfoCircleOutline />Esses dados não serão processados</div>
				<Button>Salvar</Button></Section
			></Section
		>
		<Section><Section></Section></Section>
	</div>

	<div class="mt-6 mb-6"><Button>Salvar alterações</Button></div>
</div>

<style>
	h1 {
		font-size: 24px;
		font-family: Inter;
		font-weight: 700;
		line-height: 34px;
		word-wrap: break-word;
	}
	p {
		color: var(--Text-Neutral-Neutral-900, #383e41);
		font-size: 12px;
		font-family: Inter;
		font-weight: 400;
		line-height: 18px;
		word-wrap: break-word;
	}

	.header {
		width: 100%;
		justify-content: center;
		display: flex;
		flex-direction: column;
	}

	:global(ul),
	:global(li) {
		list-style-type: none !important;
	}
</style>
