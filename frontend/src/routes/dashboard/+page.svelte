<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
    import { api } from '$lib/api';
    let exporting = $state(false), error = $state('');
    async function exportReport() {
        exporting = true; error = '';
        try {
            const [channels, simulations] = await Promise.all([api('/analytics/channels'), api('/budget/simulations')]);
            const url = URL.createObjectURL(new Blob([JSON.stringify({generated_at: new Date().toISOString(), channels, simulations}, null, 2)], {type:'application/json'}));
            const link = document.createElement('a'); link.href = url; link.download = 'marketing-summary.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
        } catch(e) { error = (e as Error).message; } finally { exporting = false; }
    }

	let visible = $state(false);

	onMount(() => {
		visible = true;
	});
</script>

<svelte:head>
	<title>Overview - Dashboard</title>
</svelte:head>

{#if visible}
	<div class="space-y-6" in:fade={{ duration: 400 }}>
        <p class="text-text-secondary">Overview metrics below are demonstration data. Use the sidebar for stored leads, channel analytics, and budget simulations. Export downloads stored channel and budget data.</p>
        {#if error}<p role="alert" class="text-red-400">{error}</p>{/if}
		<!-- Header Section -->
		<div class="flex justify-between items-end mb-8" in:fly={{ y: -20, duration: 600, delay: 100 }}>
			<div>
				<h1 class="text-3xl font-bold text-white mb-2">Campaign Overview</h1>
				<p class="text-text-secondary">AI-driven insights and real-time performance metrics.</p>
			</div>
			<div class="flex gap-3">
				<button onclick={exportReport} disabled={exporting} class="px-4 py-2 rounded-lg bg-card border border-white/10 text-white text-sm font-medium hover:bg-white/5 transition-colors">
					Export Report
				</button>
				<button disabled title="Model training is not implemented yet" class="px-4 py-2 rounded-lg bg-accent/40 text-white text-sm font-bold">
					Training unavailable
				</button>
			</div>
		</div>

		<!-- Top Level Metrics -->
		<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
			<!-- Metric 1 -->
			<div in:fly={{ y: 20, duration: 600, delay: 200 }} class="bg-card p-6 rounded-2xl border border-white/5 shadow-lg relative overflow-hidden group hover:border-white/10 transition-colors">
				<div class="absolute inset-0 bg-gradient-to-br from-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
				<div class="flex items-center space-x-4">
					<div class="p-3 bg-white/5 border border-white/10 rounded-xl text-text-secondary">
						<svg xmlns="http://www.w3.org/-2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
						</svg>
					</div>
					<div>
						<p class="text-sm text-text-secondary font-medium mb-1">Total Leads</p>
						<h3 class="text-2xl font-bold text-white">8,000</h3>
					</div>
				</div>
			</div>

			<!-- Metric 2 -->
			<div in:fly={{ y: 20, duration: 600, delay: 300 }} class="bg-card p-6 rounded-2xl border border-white/5 shadow-lg relative overflow-hidden group hover:border-white/10 transition-colors">
				<div class="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
				<div class="flex items-center space-x-4">
					<div class="p-3 bg-white/5 border border-white/10 rounded-xl text-green-400">
						<svg xmlns="http://www.w3.org/-2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
					</div>
					<div>
						<p class="text-sm text-text-secondary font-medium mb-1">Avg Conversion Rate</p>
						<div class="flex items-baseline gap-2">
							<h3 class="text-2xl font-bold text-white">8.5%</h3>
							<span class="text-xs text-green-400 font-bold">↑ 1.2%</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Metric 3 -->
			<div in:fly={{ y: 20, duration: 600, delay: 400 }} class="bg-card p-6 rounded-2xl border border-accent/20 shadow-[0_0_15px_rgba(164,123,224,0.1)] relative overflow-hidden group hover:border-accent/40 transition-colors">
				<div class="absolute inset-0 bg-gradient-to-br from-accent/10 to-transparent opacity-50 group-hover:opacity-100 transition-opacity"></div>
				<div class="flex items-center space-x-4 relative z-10">
					<div class="p-3 bg-accent/20 border border-accent/30 rounded-xl text-accent">
						<svg xmlns="http://www.w3.org/-2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
						</svg>
					</div>
					<div>
						<p class="text-sm text-accent font-medium mb-1">Predicted Conversions</p>
						<h3 class="text-2xl font-bold text-white">640</h3>
					</div>
				</div>
			</div>

			<!-- Metric 4 -->
			<div in:fly={{ y: 20, duration: 600, delay: 500 }} class="bg-card p-6 rounded-2xl border border-white/5 shadow-lg relative overflow-hidden group hover:border-white/10 transition-colors">
				<div class="absolute inset-0 bg-gradient-to-br from-cta/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
				<div class="flex items-center space-x-4">
					<div class="p-3 bg-white/5 border border-white/10 rounded-xl text-cta">
						<svg xmlns="http://www.w3.org/-2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
					</div>
					<div>
						<p class="text-sm text-text-secondary font-medium mb-1">Avg CPA</p>
						<div class="flex items-baseline gap-2">
							<h3 class="text-2xl font-bold text-white">$45.20</h3>
							<span class="text-xs text-red-400 font-bold">↓ $2.10</span>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- AI Recommendations Panel -->
		<div in:fly={{ y: 20, duration: 600, delay: 600 }} class="bg-card p-8 rounded-2xl border border-white/10 shadow-xl flex flex-col md:flex-row justify-between items-center relative overflow-hidden mt-8">
			<!-- Background decorative circle -->
			<div class="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-accent opacity-10 blur-3xl pointer-events-none"></div>
			
			<div class="z-10 mb-6 md:mb-0 max-w-3xl">
				<div class="flex items-center space-x-3 mb-3">
					<div class="w-8 h-8 rounded-lg bg-cta/20 flex items-center justify-center border border-cta/30">
						<span class="text-lg">💡</span>
					</div>
					<h3 class="text-xl font-bold text-cta">RL Agent Recommendation</h3>
					<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-green-500/20 text-green-400 border border-green-500/30 uppercase tracking-wider">High Confidence</span>
				</div>
				<p class="text-text-secondary leading-relaxed text-lg">
					Based on the latest learning episode, shifting <span class="text-white font-bold px-1">15%</span> of the budget from <span class="text-red-400 font-medium px-1">PPC</span> to <span class="text-green-400 font-medium px-1">Social Media</span> is projected to reduce overall CPA to <span class="text-white font-bold">$42.80</span> and increase expected conversions by <span class="text-white font-bold">4.2%</span>.
				</p>
			</div>
			<button class="z-10 px-8 py-4 bg-cta hover:bg-cta/90 text-black font-bold text-lg rounded-xl transition-all shadow-[0_0_20px_rgba(242,166,43,0.3)] hover:scale-105 whitespace-nowrap">
				Apply Allocation
			</button>
		</div>

		<!-- Charts placeholder area -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
			<div in:fly={{ y: 20, duration: 600, delay: 700 }} class="bg-card p-6 rounded-2xl border border-white/5 shadow-lg h-96 flex flex-col relative overflow-hidden">
				<div class="flex justify-between items-center mb-6 z-10">
					<h3 class="font-bold text-white text-lg">Channel Performance</h3>
					<select class="bg-white/5 border border-white/10 text-sm text-text-secondary rounded-lg px-3 py-1 outline-none">
						<option>Last 30 Days</option>
						<option>Last 7 Days</option>
					</select>
				</div>
				<div class="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-white/5 rounded-xl z-10">
					<span class="text-4xl mb-4 opacity-50">📈</span>
					<p class="text-text-secondary">ECharts Instance Placeholder</p>
					<p class="text-xs text-slate-500 mt-2">Data will be fetched from FastAPI backend.</p>
				</div>
			</div>

			<div in:fly={{ y: 20, duration: 600, delay: 800 }} class="bg-card p-6 rounded-2xl border border-white/5 shadow-lg h-96 flex flex-col relative overflow-hidden">
				<div class="flex justify-between items-center mb-6 z-10">
					<h3 class="font-bold text-white text-lg">Customer Segments (K-Means)</h3>
					<button class="text-accent text-sm hover:underline">View Details</button>
				</div>
				<div class="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-white/5 rounded-xl z-10">
					<span class="text-4xl mb-4 opacity-50">🧮</span>
					<p class="text-text-secondary">ECharts Scatter Plot Placeholder</p>
					<p class="text-xs text-slate-500 mt-2">Awaiting ML Pipeline execution.</p>
				</div>
			</div>
		</div>
	</div>
{/if}
