<script lang="ts">
	interface Props {
		children?: import('svelte').Snippet;
		class?: string;
		[key: string]: any;
	}

	let { children, class: className = '', ...props }: Props = $props();
</script>

<div class="container rounded-xl border border-gray-300 bg-white p-8{className}" {...props}>
	{@render children?.()}
</div>
