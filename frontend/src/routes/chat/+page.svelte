<script lang="ts">
	import { Button, Card } from '$lib';
</script>

<svelte:head>
	<title>Chat - Note-RAGs</title>
	<meta name="description" content="Interactive chat with your notes - Coming Soon" />
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
	<div class="text-center">
		<Card class="mx-auto max-w-lg">
			{#snippet header()}
				<h1 class="text-3xl font-bold text-gray-900">Interactive Chat</h1>
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
							d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.955 8.955 0 01-4.126-.98L3 21l1.98-5.874A8.955 8.955 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z"
						/>
					</svg>
				</div>

				<p class="mb-6 text-gray-600">
					Interactive chat functionality is coming soon! This will allow you to have natural
					conversations with your notes.
				</p>

				<div class="mb-6 space-y-3 text-sm text-gray-500">
					<p>🤖 Natural conversation interface</p>
					<p>💬 Context-aware responses</p>
					<p>📚 Real-time note searching</p>
					<p>🔗 Follow-up questions</p>
				</div>
			</div>

			{#snippet footer()}
				<div class="space-y-3">
					<Button href="/queries" variant="primary" class="w-full">Try Queries Instead</Button>
					<Button href="/" variant="ghost" class="w-full">Back to Home</Button>
				</div>
			{/snippet}
		</Card>
	</div>
</div>
