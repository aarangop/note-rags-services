<script lang="ts">
</script>

<div class="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
	<!-- Hero Section -->
	<div class="mb-12 text-center">
		<h1 class="mb-4 text-4xl font-bold text-gray-900">Welcome to Note-RAGs</h1>
		<p class="mx-auto max-w-2xl text-xl text-gray-600">My intelligent note making system.</p>
	</div>

	<!-- Feature Cards -->
	<div class="grid grid-cols-1 gap-6 md:grid-cols-3">
		<!-- Query Feature Card -->
		<a
			href="/queries"
			class="card variant-filled-surface-50-900 hover:variant-filled-primary cursor-pointer shadow-lg transition-all duration-200"
		>
			<div class="p-6 text-center">
				<div class="mb-4">
					<svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						></path>
					</svg>
				</div>
				<h3 class="mb-2 text-xl font-semibold">Query Notes</h3>
				<p class="text-sm opacity-75">
					Search through your notes with intelligent queries and get contextual answers powered by
					AI.
				</p>
			</div>
		</a>

		<!-- Chat Feature Card -->
		<a
			href="/chat"
			class="card variant-filled-surface-50-900 hover:variant-filled-secondary cursor-pointer shadow-lg transition-all duration-200"
		>
			<div class="p-6 text-center">
				<div class="mb-4">
					<svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
						></path>
					</svg>
				</div>
				<h3 class="mb-2 text-xl font-semibold">Chat Interface</h3>
				<p class="text-sm opacity-75">
					Have natural conversations about your notes. Ask questions and get detailed responses.
				</p>
			</div>
		</a>

		<!-- Note Editing Feature Card -->
		<a
			href="/notes"
			class="card variant-filled-surface-50-900 hover:variant-filled-tertiary cursor-pointer shadow-lg transition-all duration-200"
		>
			<div class="p-6 text-center">
				<div class="mb-4">
					<svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
						></path>
					</svg>
				</div>
				<h3 class="mb-2 text-xl font-semibold">Edit Notes</h3>
				<p class="text-sm opacity-75">
					Create, edit, and organize your notes with a powerful and intuitive editor interface.
				</p>
			</div>
		</a>
	</div>
</div>
