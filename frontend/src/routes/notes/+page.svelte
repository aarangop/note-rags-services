<script lang="ts">
	import { Button, Card } from '$lib';
</script>

<svelte:head>
	<title>Notes - Note-RAGs</title>
	<meta name="description" content="Manage your notes - Coming Soon" />
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
	<div class="text-center">
		<Card class="mx-auto max-w-lg">
			{#snippet header()}
				<h1 class="text-3xl font-bold text-gray-900">Manage Notes</h1>
			{/snippet}

			<div class="py-8">
				<div
					class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-200"
				>
					<svg class="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
						/>
					</svg>
				</div>

				<p class="mb-6 text-gray-600">
					Note management features are coming soon! This will be your central hub for organizing and
					managing your notes.
				</p>

				<div class="mb-6 space-y-3 text-sm text-gray-500">
					<p>📁 Upload and organize notes</p>
					<p>✏️ Edit and format content</p>
					<p>🏷️ Tag and categorize notes</p>
					<p>🔍 Search and filter notes</p>
				</div>
			</div>

			{#snippet footer()}
				<div class="space-y-3">
					<Button href="/queries" variant="primary" class="w-full">Query Existing Notes</Button>
					<Button href="/" variant="ghost" class="w-full">Back to Home</Button>
				</div>
			{/snippet}
		</Card>
	</div>
</div>
