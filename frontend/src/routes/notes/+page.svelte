<script lang="ts">
	import NoteEditor from '$lib/components/NoteEditor.svelte';
</script>

<svelte:head>
	<title>Notes - Note-RAGs</title>
	<meta name="description" content="Manage your notes - Coming Soon" />
</svelte:head>

<div class="mx-auto flex h-screen max-w-4xl flex-col px-4 pt-4 pb-4 sm:px-6 lg:px-8">
	<NoteEditor fileName="Sample File"></NoteEditor>
</div>
