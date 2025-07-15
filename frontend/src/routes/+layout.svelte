<script lang="ts">
	import '../app.css';

	let { children } = $props();
</script>

<div class="min-h-screen bg-gray-50">
	<!-- <Navigation /> -->
	<main>
		{@render children()}
	</main>
</div>
