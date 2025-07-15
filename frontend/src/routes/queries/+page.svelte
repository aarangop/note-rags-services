<script lang="ts">
	import {
		submitQueryStream,
		testConnection,
		type QueryResponse,
		type StreamChunk
	} from '$lib/api/queries';
	import { onMount } from 'svelte';

	let query = '';
	let isLoading = false;
	let response: QueryResponse | null = null;
	let streamingContent = '';
	let currentContext: string[] = [];
	let error = '';
	let isApiConnected = false;
	let isCheckingConnection = true;
	let hasContent = false; // Flag to keep UI visible after completion

	// Debug reactive statements
	$: console.log('UI Update - streamingContent:', streamingContent);
	$: console.log('UI Update - currentContext:', currentContext);
	$: console.log('UI Update - response:', response);
	$: console.log('UI Update - isLoading:', isLoading);
	$: console.log('UI Update - hasContent:', hasContent);

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
		streamingContent = '';
		currentContext = [];
		hasContent = false;

		try {
			await submitQueryStream(
				query.trim(),
				// onChunk callback - handles real-time updates
				(chunk: StreamChunk) => {
					console.log('Received chunk:', chunk);

					switch (chunk.type) {
						case 'context':
							if (Array.isArray(chunk.context)) {
								currentContext = [...chunk.context]; // Use chunk.context instead of chunk.data
								hasContent = true;
							}
							break;
						case 'answer': // Changed from 'response' to 'answer'
							if (typeof chunk.content === 'string') {
								streamingContent = streamingContent + chunk.content; // Use chunk.content instead of chunk.data
								hasContent = true;
							}
							break;
						case 'complete':
							// Handle completion - build final response from accumulated data
							response = {
								question: query.trim(),
								response: streamingContent,
								context: currentContext,
								tokens: 0 // We'll update this if we get token info
							};
							hasContent = true;
							break;
						case 'error':
							error =
								typeof chunk.data === 'string' ? chunk.data : 'An error occurred during streaming';
							hasContent = true;
							break;
					}
				},
				// onComplete callback - final response
				(finalResponse: QueryResponse | undefined) => {
					console.log('Final response received:', finalResponse);
					// If we have a proper final response, use it, otherwise keep what we built
					if (finalResponse) {
						response = finalResponse;
						if (finalResponse.response && !streamingContent) {
							streamingContent = finalResponse.response;
						}
					}
					hasContent = true;
				},
				// onError callback
				(errorMessage: string) => {
					error = errorMessage;
				}
			);
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			isLoading = false;
		}
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

	<!-- Streaming Response -->
	{#if isLoading || hasContent}
		<div class="space-y-6">
			<!-- Debug info -->
			<div class="rounded border border-yellow-400 bg-yellow-100 p-3 text-sm">
				<p><strong>Debug:</strong></p>
				<p>isLoading: {isLoading}</p>
				<p>hasContent: {hasContent}</p>
				<p>streamingContent length: {streamingContent.length}</p>
				<p>streamingContent preview: "{streamingContent.slice(0, 50)}..."</p>
				<p>currentContext length: {currentContext.length}</p>
				<p>response: {response ? 'exists' : 'null'}</p>
				{#if response}
					<p>response.response: "{response.response.slice(0, 50)}..."</p>
				{/if}
			</div>

			<!-- Context Section (if available) -->
			{#if currentContext.length > 0}
				<div class="card variant-filled-secondary-50-900 p-6">
					<h3 class="h3 mb-4">📚 Retrieved Context</h3>
					<div class="space-y-2">
						{#each currentContext as contextItem, i}
							<div class="bg-surface-200-700 rounded p-3">
								<span class="text-surface-600-300 text-sm font-medium">Source {i + 1}:</span>
								<p class="mt-1 text-sm">{contextItem}</p>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Response Section -->
			<div class="card variant-filled-surface-50-900 p-6">
				<h3 class="h3 mb-4">
					{#if isLoading}
						🤖 AI Response (Streaming...)
					{:else}
						🤖 AI Response
					{/if}
				</h3>

				<div class="bg-surface-100-800 min-h-32 rounded p-4">
					{#if streamingContent}
						<div class="text-sm whitespace-pre-wrap">
							{streamingContent}
							{#if isLoading}
								<span class="bg-primary-500 ml-1 inline-block h-4 w-2 animate-pulse"></span>
							{/if}
						</div>
					{:else if isLoading}
						<div class="text-surface-400-500 flex items-center space-x-2">
							<div
								class="border-primary-500 h-4 w-4 animate-spin rounded-full border-2 border-t-transparent"
							></div>
							<span class="text-sm">Generating response...</span>
						</div>
					{/if}
				</div>

				<!-- Final Response Metadata -->
				{#if response && !isLoading}
					<div class="border-surface-300-600 mt-4 border-t pt-4">
						<div class="text-surface-500-400 flex flex-wrap gap-4 text-xs">
							<span>Question: <strong>{response.question}</strong></span>
							<span>Tokens used: <strong>{response.tokens}</strong></span>
							<span>Context items: <strong>{response.context.length}</strong></span>
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
