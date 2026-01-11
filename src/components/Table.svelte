<script>
	export let headers;
</script>

<div class="relative overflow-x-auto border border-gray-200 shadow-md sm:rounded-lg">
	<table class="w-full text-left text-sm text-gray-500">
		<thead class="bg-gray-50 text-xs text-gray-700 uppercase">
			<tr>
				{#each headers as h}
					<th scope="col" class="px-6 py-3">{h}</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			<slot />
		</tbody>
	</table>
</div>
