<script lang="ts">
	import './layout.css';
	import { siteMotion } from '$lib/site-motion';
	let { children } = $props();
</script>

<div use:siteMotion class="site-motion min-h-screen bg-primary text-text-primary selection:bg-accent selection:text-white overflow-x-hidden">
	{@render children()}
</div>
