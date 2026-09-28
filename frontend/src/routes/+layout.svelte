<script lang="ts">
	import './layout.css';
	import '$lib/di-light.css';
	import { siteMotion } from '$lib/site-motion';
	let { children } = $props();
</script>

<div use:siteMotion class="di-light site-motion flex min-h-screen flex-col bg-primary text-text-primary selection:bg-accent selection:text-white overflow-x-hidden">
	{@render children()}
</div>
