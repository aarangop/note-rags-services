<script lang="ts">
	import Link from '$lib/components/Link.svelte';
</script>

<div class="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
	<div class="flex min-h-[calc(100vh-6rem)] flex-col items-center justify-center space-y-4">
		<p class="h3 pb-4">No note is open</p>
		<Link href="/new-note" class="w-full">Create new note (Cmd + N)</Link>
		<Link href="" class="w-full">Open Quick Switcher (Cmd + O)</Link>
	</div>
</div>
