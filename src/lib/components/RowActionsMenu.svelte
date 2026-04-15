<script lang="ts">
	import {
		Button,
		ChevronDownOutline,
		TrashBinOutline,
		Dropdown,
		DropdownItem,
		DropdownDivider,
		DropdownHeader,
		EditOutline
	} from '$lib/uicomponents.js';

	interface Props {
		menuId: string;
		headerLabel: string;
		onEdit: () => void;
		onDelete?: () => void;
		showDelete?: boolean;
		editLabel?: string;
		deleteLabel?: string;
	}

	let {
		menuId,
		headerLabel,
		onEdit,
		onDelete,
		showDelete = true,
		editLabel = 'Editar',
		deleteLabel = 'Excluir'
	}: Props = $props();
</script>

<Button id={menuId} outline color="dark" size="xs">
	Ações <ChevronDownOutline class="ml-1 h-4 w-4" />
</Button>
<Dropdown triggeredBy={`#${menuId}`}>
	<DropdownHeader>{headerLabel}</DropdownHeader>
	<DropdownItem onclick={onEdit}>
		<EditOutline class="mr-2 h-4 w-4" />{editLabel}
	</DropdownItem>
	{#if showDelete && onDelete}
		<DropdownItem class="text-red-600" onclick={onDelete}>
			<TrashBinOutline class="mr-2 h-4 w-4" />{deleteLabel}
		</DropdownItem>
	{:else if showDelete}
		<DropdownItem class="text-red-600">
			<TrashBinOutline class="mr-2 h-4 w-4" />{deleteLabel}
		</DropdownItem>
	{/if}
</Dropdown>
