<script lang="ts">
    import { afterNavigate } from '$app/navigation';
    import { page } from '$app/state';
    import { api, signOut, type User } from '$lib/api';
    let user = $state<User | null>(null), error = $state('');
    afterNavigate(async () => { try { user = await api('/auth/me'); error = ''; } catch(e) { user = null; error = (e as Error).message; } });
    async function logout() { try { await signOut(); window.location.assign('/login'); } catch(e) { error = (e as Error).message; } }
	let { children } = $props();
</script>

{#if user}
<div class="flex h-screen bg-primary font-sans text-text-primary overflow-hidden">
	<!-- Sidebar -->
	<aside class="w-64 bg-card border-r border-white/5 flex flex-col z-20">
		<div class="h-20 border-b border-white/5 flex items-center px-6">
			<a href="/" class="flex items-center gap-2">
				<div class="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-secondary flex items-center justify-center shadow-[0_0_15px_rgba(164,123,224,0.5)]">
					<svg xmlns="http://www.w3.org/-2000/svg" class="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
						<path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
						<path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
					</svg>
				</div>
				<span class="text-xl font-bold tracking-wider text-white">Decision<span class="text-accent font-serif italic">Intel</span></span>
			</a>
		</div>
		<nav aria-label="Marketing dashboard" class="flex-1 p-4 space-y-2 overflow-y-auto">
            {#if user.role === 'admin'}<a href="/admin" class="block px-4 py-3 text-accent">Administration</a>{/if}
			<a href="/dashboard" aria-current={page.url.pathname === '/dashboard' ? 'page' : undefined} class="flex items-center px-4 py-3 rounded-lg text-white font-medium transition-colors">
				<svg xmlns="http://www.w3.org/-2000/svg" class="h-5 w-5 mr-3 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
				</svg>
				Overview
			</a>
			<a href="/dashboard/leads" aria-current={page.url.pathname === '/dashboard/leads' ? 'page' : undefined} class="flex items-center px-4 py-3 text-text-secondary hover:text-white hover:bg-white/5 rounded-lg font-medium transition-colors">
				<svg xmlns="http://www.w3.org/-2000/svg" class="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
				</svg>
				Leads & Predictions
			</a>
			<a href="/dashboard/analytics" aria-current={page.url.pathname === '/dashboard/analytics' ? 'page' : undefined} class="flex items-center px-4 py-3 text-text-secondary hover:text-white hover:bg-white/5 rounded-lg font-medium transition-colors">
				<svg xmlns="http://www.w3.org/-2000/svg" class="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
				</svg>
				Attribution & Segments
			</a>
			<a href="/dashboard/budget" aria-current={page.url.pathname === '/dashboard/budget' ? 'page' : undefined} class="flex items-center px-4 py-3 text-text-secondary hover:text-white hover:bg-white/5 rounded-lg font-medium transition-colors">
				<svg xmlns="http://www.w3.org/-2000/svg" class="h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				Budget Simulator
			</a>
		</nav>
		<div class="p-4 border-t border-white/5">
			<a href="/" class="flex items-center px-4 py-2 text-text-secondary hover:text-white transition-colors text-sm">
				← Back to Site
			</a>
		</div>
	</aside>

	<!-- Main Content -->
	<main class="flex-1 flex flex-col relative z-10">
		<!-- Top header -->
		<header class="h-20 border-b border-white/5 flex items-center px-8 justify-between bg-primary/80 backdrop-blur-md">
			<h2 class="text-xl font-semibold text-white">Platform Dashboard</h2>
			<div class="flex items-center space-x-4">
                <span class="text-sm text-text-secondary">Welcome, {user.name}</span>
                <button onclick={logout}>Sign out</button>
				<div class="h-10 w-10 rounded-full bg-cta text-black flex items-center justify-center font-bold shadow-[0_0_15px_rgba(242,166,43,0.4)]">M</div>
			</div>
		</header>
		
		<!-- Page content -->
		<div class="flex-1 overflow-auto p-8 relative">
			<!-- Subtle background glow -->
			<div class="absolute top-0 right-0 w-[500px] h-[500px] bg-secondary/20 rounded-full blur-[100px] pointer-events-none z-[-1]"></div>
			{@render children()}
		</div>
	</main>
</div>
{:else}<p class="p-8" role="status">{error || 'Checking access…'} <a href="/login">Sign in</a></p>{/if}

<style>
    nav a[aria-current='page'] { background: #38274e; color: #e4c9ff; }
    @media (max-width: 700px) { aside { width: 180px; } header { padding: 12px; height: auto; flex-wrap: wrap; gap: 10px; } }
</style>
