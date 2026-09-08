<script lang="ts">
	import './layout.css';
	let { children } = $props();
</script>

<div class="min-h-screen bg-primary text-text-primary selection:bg-accent selection:text-white overflow-x-hidden">
	{@render children()}
</div>
