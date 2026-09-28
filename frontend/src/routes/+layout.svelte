<script lang="ts">
	import './layout.css';
	import '$lib/di-light.css';
	import { siteMotion } from '$lib/site-motion';
	import { initTheme } from '$lib/theme.svelte';
	import { onMount } from 'svelte';
	let { children } = $props();
	// app.html already set the class before paint; this syncs reactive state.
	onMount(initTheme);
</script>

<div use:siteMotion class="site-motion flex min-h-screen flex-col bg-primary text-text-primary selection:bg-accent selection:text-white overflow-x-hidden">
	{@render children()}
</div>
