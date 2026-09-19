<script lang="ts">
	import { fade, fly } from 'svelte/transition';
	import { onMount } from 'svelte';
    import { api, signIn } from '$lib/api';
    let name = $state(''), email = $state(''), password = $state(''), role = $state('marketer'), error = $state(''), busy = $state(false);
    async function submit(event: SubmitEvent) {
        event.preventDefault(); busy = true; error = '';
        try { await api('/auth/register', { method: 'POST', body: JSON.stringify({name, email, password, role}) }); await signIn(email, password); }
        catch(e) { error = (e as Error).message; } finally { busy = false; }
    }

	let visible = $state(false);

	onMount(() => {
		visible = true;
	});
</script>

<svelte:head>
	<title>Register | DecisionIntel</title>
</svelte:head>

<div class="min-h-[calc(100vh-80px)] flex flex-col lg:flex-row overflow-hidden relative">
	<!-- Background glow for the entire page just in case -->
	<div class="absolute inset-0 bg-primary z-[-2]"></div>
	<div class="absolute top-0 left-0 w-[500px] h-[500px] bg-secondary/30 rounded-full blur-[100px] z-[-1] pointer-events-none"></div>

	<!-- Left Form Section -->
	<div class="w-full lg:w-1/2 flex items-center justify-center p-8 lg:p-16 relative z-10">
		{#if visible}
			<!-- Light Glass Effect Container -->
			<div 
				in:fly={{ y: 20, duration: 800, delay: 100 }}
				class="w-full max-w-md bg-white/5 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.37)] rounded-3xl p-8 relative overflow-hidden"
			>
				<!-- Subtle inner glow to make it look 'light' -->
				<div class="absolute -top-20 -right-20 w-40 h-40 bg-white/10 blur-[50px] rounded-full pointer-events-none"></div>

                <div class="flex justify-between mb-6 text-sm text-accent"><a href="/">← Home</a><a href="/login">Sign in</a></div>
				<div class="text-center mb-8">
					<h2 class="text-3xl font-bold text-white mb-2">Create an account</h2>
					<p class="text-text-secondary text-sm">Join the next generation of marketing intelligence.</p>
				</div>

                {#if error}<p role="alert" class="text-red-400 mb-4">{error}</p>{/if}
				<form class="space-y-5" onsubmit={submit}>
					<div class="space-y-1">
						<label for="name" class="text-sm font-medium text-text-secondary">Full Name</label>
						<input 
							type="text" 
							id="name" 
                            bind:value={name} required maxlength="100"
							placeholder="Jane Doe"
							class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-all"
						/>
					</div>

					<div class="space-y-1">
						<label for="email" class="text-sm font-medium text-text-secondary">Work Email</label>
						<input 
							type="email" 
							id="email" 
                            bind:value={email} required
							placeholder="jane@company.com"
							class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-all"
						/>
					</div>

					<div class="space-y-1">
						<label for="password" class="text-sm font-medium text-text-secondary">Password</label>
						<input 
							type="password" 
							id="password" 
                            bind:value={password} required minlength="12" maxlength="128"
							placeholder="••••••••"
							class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-all"
						/>
					</div>

					<div class="grid grid-cols-2 gap-4">
						<div class="space-y-1">
							<label for="company" class="text-sm font-medium text-text-secondary">Company</label>
							<input 
								type="text" 
								id="company" 
								placeholder="Acme Corp"
								class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-all"
							/>
						</div>
						<div class="space-y-1">
							<label for="role" class="text-sm font-medium text-text-secondary">Role</label>
							<select 
								id="role"
                                bind:value={role}
								class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-all appearance-none"
							>
								<option value="marketer">Marketer</option>
								<option value="data_scientist">Data Scientist</option>
								<option value="executive">Executive</option>
							</select>
						</div>
					</div>

					<button 
						type="submit"
                        disabled={busy}
						class="w-full bg-cta hover:bg-cta/90 text-black font-bold text-lg rounded-xl px-4 py-3 mt-4 transition-all shadow-[0_0_15px_rgba(242,166,43,0.3)] hover:shadow-[0_0_25px_rgba(242,166,43,0.5)] transform hover:-translate-y-0.5"
					>
						Register
					</button>

					<p class="text-center text-sm text-text-secondary mt-6">
						Already have an account? <a href="/login" class="text-accent hover:text-white transition-colors font-medium">Sign In</a>
					</p>
				</form>
			</div>
		{/if}
	</div>

	<!-- Right Image Section -->
	<div class="hidden lg:block w-1/2 relative">
		{#if visible}
			<div 
				in:fade={{ duration: 1500 }}
				class="absolute inset-0 h-full w-full"
			>
				<img 
					src="/graph_analytics.jpg" 
					alt="Graph Analytics" 
					class="w-full h-full object-cover rounded-tl-3xl rounded-bl-3xl border-l border-y border-white/10 shadow-2xl"
				/>
				<!-- Gradient overlay to blend it with the theme -->
				<div class="absolute inset-0 bg-gradient-to-r from-primary via-primary/50 to-transparent"></div>
				
				<!-- Floating text over the image -->
				<div class="absolute bottom-16 left-16 max-w-md" in:fly={{ x: 50, duration: 1000, delay: 500 }}>
					<div class="bg-card/70 backdrop-blur-md border border-white/10 p-6 rounded-2xl shadow-xl">
						<div class="flex items-center gap-3 mb-3">
							<span class="text-2xl">✨</span>
							<h3 class="font-bold text-white text-lg">Intelligent Architecture</h3>
						</div>
						<p class="text-text-secondary text-sm leading-relaxed">
							Connect your database to securely analyze up to millions of leads. Our ML models train locally to ensure strict privacy while giving you 99% accuracy on predictions.
						</p>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>
