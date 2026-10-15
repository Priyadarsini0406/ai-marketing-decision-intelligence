<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import { startLiveSync } from '$lib/live-sync';
    type Enquiry = { id: string; course_interested: string; status: string; created_at: number; updated_at: number };
    let items = $state<Enquiry[]>([]), query = $state(''), status = $state('All'), error = $state(''), loading = $state(true);
    let filtered = $derived(items.filter((item) => (status === 'All' || item.status === status) && `${item.course_interested} ${item.status}`.toLowerCase().includes(query.toLowerCase())));
    const date = (value: number) => new Date(value * 1000).toLocaleDateString();
    async function load() { try { items = await api('/student/enquiries'); } catch (e) { error = (e as Error).message; } finally { loading = false; } }
    onMount(() => { void load(); return startLiveSync(load); });
</script>
<svelte:head><title>My Enquiries | DecisionIntel</title></svelte:head>
<div class="space-y-6"><div class="flex flex-col sm:flex-row justify-between gap-4"><div><h1 class="text-3xl font-bold text-white">My Enquiries</h1><p class="text-text-secondary mt-2">View the enquiries you have submitted and their latest status.</p></div><a href="/student/enquiries/new" class="px-5 py-3 rounded-xl bg-cta text-white font-bold text-sm text-center">New Enquiry</a></div>
    {#if error}<p role="alert" class="text-red-400">{error}</p>{/if}
    <div class="flex flex-col sm:flex-row gap-3"><input bind:value={query} placeholder="Search enquiries" class="bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm"/><select bind:value={status} class="bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm"><option>All</option>{#each ['Submitted','Under Review','Counselling','Application','Admitted','Not Converted'] as value}<option>{value}</option>{/each}</select></div>
    <div class="bg-card border border-white/10 rounded-2xl overflow-x-auto"><table class="w-full min-w-[680px] text-sm"><thead class="text-left text-xs uppercase tracking-wider text-text-secondary border-b border-white/10"><tr><th class="p-5">Course / Program</th><th>Submitted</th><th>Current Status</th><th>Last Updated</th><th></th></tr></thead><tbody>{#each filtered as item}<tr class="border-b border-white/5 text-text-secondary"><td class="p-5"><p class="text-white font-medium">{item.course_interested}</p><p class="text-xs mt-1">{item.id.slice(0, 8)}</p></td><td>{date(item.created_at)}</td><td><span class="text-xs px-2 py-1 rounded bg-accent/15 text-accent">{item.status}</span></td><td>{date(item.updated_at)}</td><td><a href="/student/enquiries/status" class="text-accent hover:underline">View Details</a></td></tr>{:else}<tr><td colspan="5" class="p-5">{loading ? 'Loading enquiries…' : 'No enquiries saved yet. Submit a new enquiry to get started.'}</td></tr>{/each}</tbody></table></div>
</div>
