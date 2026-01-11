<script>
	export let variant = 'primary';
	export let className = '';

	const baseStyle =
		'px-4 py-2 rounded-lg font-medium text-sm transition-colors focus:ring-4 focus:outline-none';
	const variants = {
		primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-300',
		secondary: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-gray-200',
		success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-300'
	};
</script>

<button on:click class={`${baseStyle} ${variants[variant]} ${className}`}>
	<slot />
</button>
