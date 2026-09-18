<script lang="ts">
    let { title, description = 'This Decision-Intel module is being prepared for a future phase.' }: { title: string; description?: string } = $props();
</script>
<svelte:head><title>{title} | DecisionIntel</title></svelte:head>
<section class="max-w-3xl"><p class="text-xs uppercase tracking-[.18em] text-accent font-bold mb-3">Coming soon</p><h1 class="text-3xl font-bold text-white mb-3">{title}</h1><p class="text-text-secondary leading-relaxed">{description}</p><div class="mt-8 p-6 rounded-2xl border border-white/10 bg-card/80"><p class="text-white font-medium">Module placeholder</p><p class="text-sm text-text-secondary mt-2">Navigation and access control are ready. Detailed functionality is intentionally outside Phase 2.</p></div></section>
