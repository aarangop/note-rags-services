<script lang="ts">
	import { submitQuery, testConnection } from '$lib/api/queries';
	import { onMount } from 'svelte';

	let query = '';
	let isLoading = false;
	let response: any = null;
	let error = '';
	let isApiConnected = false;
	let isCheckingConnection = true;

	onMount(async () => {
		// Test API connection on component mount
		try {
			isApiConnected = await testConnection();
		} catch {
			isApiConnected = false;
		} finally {
			isCheckingConnection = false;
		}
	});

	async function handleSubmit() {
		if (!query.trim()) return;

		isLoading = true;
		error = '';
		response = null;

		try {
			const data = await submitQuery(query.trim());
			response = data;
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			isLoading = false;
		}
	}

	// Format the response for better display
	function formatResponse(data: any): string {
		if (typeof data === 'string') {
			return data;
		}
		return JSON.stringify(data, null, 2);
	}
</script>

<div class="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
	<!-- Page Header -->
	<div class="mb-8">
		<div class="mb-4 flex items-center justify-between">
			<h1 class="text-3xl font-bold text-gray-900">Query Your Notes</h1>

			<!-- API Connection Status -->
			<div class="flex items-center space-x-2">
				{#if isCheckingConnection}
					<div class="flex animate-pulse items-center space-x-2">
						<div class="h-2 w-2 rounded-full bg-gray-400"></div>
						<span class="text-sm text-gray-500">Checking connection...</span>
					</div>
				{:else if isApiConnected}
					<div class="flex items-center space-x-2">
						<div class="h-2 w-2 rounded-full bg-green-500"></div>
						<span class="text-sm text-green-600">API Connected</span>
					</div>
				{:else}
					<div class="flex items-center space-x-2">
						<div class="h-2 w-2 rounded-full bg-red-500"></div>
						<span class="text-sm text-red-600">API Disconnected</span>
					</div>
				{/if}
			</div>
		</div>
		<p class="text-lg text-gray-600">
			Ask questions about your notes and get AI-powered answers with relevant context.
		</p>
	</div>

	<!-- Query Form -->
	<div class="mb-8">
		<form on:submit|preventDefault={handleSubmit} class="space-y-4">
			<div>
				<label for="query" class="mb-2 block text-sm font-medium text-gray-700">
					Enter your question
				</label>
				<textarea
					id="query"
					bind:value={query}
					placeholder="What would you like to know about your notes?"
					rows="4"
					class="textarea variant-form-material w-full resize-none"
					disabled={isLoading}
				></textarea>
			</div>

			<button
				type="submit"
				class="btn variant-filled-primary"
				disabled={isLoading || !query.trim() || !isApiConnected}
			>
				{#if isLoading}
					<svg
						class="mr-3 -ml-1 h-5 w-5 animate-spin"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
					>
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					Processing...
				{:else}
					Submit Query
				{/if}
			</button>
		</form>
	</div>

	<!-- Response Section -->
	{#if error}
		<div class="alert variant-filled-error mb-6">
			<div class="alert-message">
				<h3 class="h3">Error</h3>
				<p>{error}</p>
			</div>
		</div>
	{/if}

	{#if response}
		<div class="card variant-filled-surface-50-900 p-6">
			<h3 class="h3 mb-4">Response</h3>
			<div class="bg-surface-100-800 max-h-96 overflow-auto rounded p-4">
				{#if typeof response === 'string'}
					<p class="text-sm whitespace-pre-wrap">{response}</p>
				{:else if response && typeof response === 'object'}
					<pre class="text-sm whitespace-pre-wrap">{formatResponse(response)}</pre>
				{:else}
					<p class="text-sm">{response}</p>
				{/if}
			</div>
		</div>
	{/if}
</div>
