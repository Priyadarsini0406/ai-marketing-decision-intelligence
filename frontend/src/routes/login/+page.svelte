<script lang="ts">
	import { fade, fly } from 'svelte/transition';
	import { onMount } from 'svelte';
    import { signIn } from '$lib/api';
    let email = $state('');
    let password = $state('');
    let error = $state('');
    let busy = $state(false);
    async function submit(event: SubmitEvent) {
        event.preventDefault(); busy = true; error = '';
        try { await signIn(email, password); }
        catch (e) { error = (e as Error).message; }
        finally { busy = false; }
    }

	let visible = $state(false);

	onMount(() => {
		visible = true;
	});
</script>

<svelte:head>
	<title>Sign In | DecisionIntel</title>
</svelte:head>

<div class="min-h-screen flex flex-col lg:flex-row overflow-hidden relative bg-primary">
	<!-- Background glow for the entire page -->
	<div class="absolute top-0 right-0 w-[600px] h-[600px] bg-accent/20 rounded-full blur-[120px] z-[0] pointer-events-none"></div>

	<!-- Left Image Section -->
	<div class="hidden lg:block w-1/2 relative z-10">
		{#if visible}
			<div 
				in:fade={{ duration: 1500 }}
				class="absolute inset-0 h-full w-full"
			>
				<!-- Use the RL optimization image for login to differentiate from register -->
				<img 
					src="/rl_optimization.jpg" 
					alt="Reinforcement Learning Dashboard" 
					class="w-full h-full object-cover rounded-tr-3xl rounded-br-3xl border-r border-y border-white/5 shadow-2xl"
				/>
				<!-- Gradient overlay -->
				<div class="absolute inset-0 bg-gradient-to-l from-primary via-primary/60 to-transparent"></div>
				
				<div class="absolute top-10 left-10 flex items-center gap-2">
					<div class="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-secondary flex items-center justify-center shadow-[0_0_20px_rgba(164,123,224,0.6)]">
						<svg xmlns="http://www.w3.org/-2000/svg" class="h-6 w-6 text-white" viewBox="0 0 20 20" fill="currentColor">
							<path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
							<path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
						</svg>
					</div>
					<a href="/" class="text-2xl font-bold tracking-wider text-white hover:text-accent transition-colors">Decision<span class="text-accent font-serif italic">Intel</span></a>
				</div>

				<!-- Floating text over the image -->
				<div class="absolute bottom-16 right-16 max-w-md text-right" in:fly={{ x: -50, duration: 1000, delay: 500 }}>
					<div class="bg-card/80 backdrop-blur-md border border-white/10 p-8 rounded-3xl shadow-2xl">
						<div class="flex justify-end mb-4">
							<div class="w-12 h-12 rounded-full bg-cta/20 flex items-center justify-center text-cta shadow-[0_0_15px_rgba(242,166,43,0.3)]">
								<svg xmlns="http://www.w3.org/-2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
								</svg>
							</div>
						</div>
						<h3 class="font-bold text-white text-xl mb-2">Welcome Back</h3>
						<p class="text-text-secondary text-sm leading-relaxed">
							Your AI agents have been optimizing budgets while you were away. Sign in to view your latest predictive metrics and conversion analytics.
						</p>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<!-- Right Form Section -->
	<div class="w-full lg:w-1/2 flex flex-col items-center justify-center p-6 sm:p-8 lg:p-16 relative z-10">
		
		<!-- Mobile Logo (Normal Flow) -->
		<div class="lg:hidden flex items-center gap-2 mb-8 self-start sm:self-center">
			<div class="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-secondary flex items-center justify-center shadow-lg">
				<svg xmlns="http://www.w3.org/-2000/svg" class="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
					<path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
					<path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
				</svg>
			</div>
			<a href="/" class="text-2xl font-bold tracking-wider text-white">Decision<span class="text-accent font-serif italic">Intel</span></a>
		</div>

		{#if visible}
			<!-- Light Glass Effect Container -->
			<div 
				in:fly={{ y: 20, duration: 800, delay: 200 }}
				class="w-full max-w-md bg-white/[0.03] backdrop-blur-2xl border border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.5)] rounded-3xl p-8 sm:p-10 relative overflow-hidden"
			>
				<!-- Subtle inner glow to make it look 'light' -->
				<div class="absolute -top-20 -left-20 w-40 h-40 bg-accent/20 blur-[60px] rounded-full pointer-events-none"></div>

				<div class="text-center mb-10">
					<h2 class="text-3xl font-bold text-white mb-2">Sign In</h2>
					<p class="text-text-secondary text-sm">Access your marketing intelligence platform.</p>
				</div>

                <a href="/admin/login" class="block text-center text-accent mb-5">Admin login</a>
                {#if error}<p role="alert" class="text-red-400 mb-4">{error}</p>{/if}
				<form class="flex flex-col gap-6 w-full" onsubmit={submit}>
					<div class="flex flex-col gap-2 w-full">
						<label for="email" class="text-sm font-medium text-text-secondary">Work Email</label>
						<div class="relative w-full">
							<div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
								<svg xmlns="http://www.w3.org/-2000/svg" class="h-5 w-5 text-slate-500" viewBox="0 0 20 20" fill="currentColor">
									<path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
									<path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
								</svg>
							</div>
							<input 
								type="email" 
								id="email" 
                                bind:value={email}
								placeholder="name@company.com"
								required
								class="w-full bg-black/50 border border-white/10 rounded-xl pl-11 pr-4 py-3.5 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent/80 focus:border-transparent transition-all"
							/>
						</div>
					</div>

					<div class="flex flex-col gap-2 w-full">
						<div class="flex justify-between items-center w-full">
							<label for="password" class="text-sm font-medium text-text-secondary">Password</label>
							<a href="/forgot-password" class="text-xs text-accent hover:text-white transition-colors">Forgot password?</a>
						</div>
						<div class="relative w-full">
							<div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
								<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-500" viewBox="0 0 20 20" fill="currentColor">
									<path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
								</svg>
							</div>
							<input 
								type="password" 
								id="password" 
                                bind:value={password}
								placeholder="••••••••"
								required
								class="w-full bg-black/50 border border-white/10 rounded-xl pl-11 pr-4 py-3.5 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent/80 focus:border-transparent transition-all"
							/>
						</div>
					</div>

					<button 
						type="submit"
                        disabled={busy}
						class="w-full bg-[#F2A62B] hover:bg-[#F2A62B]/90 text-[#0B0A0F] font-bold text-lg rounded-full py-3.5 mt-2 transition-all shadow-[0_0_20px_rgba(242,166,43,0.2)] hover:shadow-[0_0_30px_rgba(242,166,43,0.4)] flex items-center justify-center"
					>
						Sign In
					</button>

					<div class="flex items-center w-full py-2">
						<div class="flex-1 border-t border-white/10"></div>
						<span class="px-4 text-slate-500 text-xs uppercase tracking-wider">Or</span>
						<div class="flex-1 border-t border-white/10"></div>
					</div>

					<div class="flex justify-center items-center gap-1.5 w-full text-sm">
						<span class="text-text-secondary">Don't have an account?</span>
						<a href="/register" class="text-accent hover:text-white transition-colors font-medium">Register here</a>
					</div>
				</form>
			</div>
		{/if}
	</div>
</div>
