<script>
	export let status;

	let color = 'gray';
	if (status === 'Ativo' || status === 'Armazenado') color = 'green';
	if (status === 'Inativo' || status === 'Em Trânsito') color = 'yellow';
</script>

<span class={`bg-${color}-100 text-${color}-800 mr-2 rounded px-2.5 py-0.5 text-xs font-semibold`}>
	{status}
</span>
