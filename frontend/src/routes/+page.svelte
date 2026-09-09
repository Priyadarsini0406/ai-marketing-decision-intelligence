<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly, scale } from 'svelte/transition';

	let visible = $state(false);
	
	// For scroll animations
	let pipelineVisible = $state(false);
	let customersVisible = $state(false);

	onMount(() => {
		visible = true;
		
		// Simple intersection observer for scroll animations
		const observer = new IntersectionObserver((entries) => {
			entries.forEach(entry => {
				if (entry.target.id === 'pipeline' && entry.isIntersecting) pipelineVisible = true;
				if (entry.target.id === 'customers' && entry.isIntersecting) customersVisible = true;
			});
		}, { threshold: 0.2 });
		
		const pipelineEl = document.getElementById('pipeline');
		const customersEl = document.getElementById('customers');
		
		if (pipelineEl) observer.observe(pipelineEl);
		if (customersEl) observer.observe(customersEl);
		
		return () => observer.disconnect();
	});
</script>

<svelte:head>
	<title>DecisionIntel | AI Marketing Platform</title>
</svelte:head>

<!-- Navbar for Landing Page -->
<header class="fixed top-0 w-full z-50 border-b border-white/5 bg-primary/80 backdrop-blur-md">
	<div class="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
		<div class="flex items-center gap-2">
			<div class="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-secondary flex items-center justify-center shadow-[0_0_15px_rgba(164,123,224,0.5)]">
				<svg xmlns="http://www.w3.org/-2000/svg" class="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
					<path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
					<path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
				</svg>
			</div>
			<span class="text-xl font-bold tracking-wider text-white">Decision<span class="text-accent font-serif italic">Intel</span></span>
		</div>
		<nav class="hidden md:flex gap-8 text-sm font-medium text-text-secondary">
			<a href="#features" class="hover:text-white transition-colors">Features</a>
			<a href="#pipeline" class="hover:text-white transition-colors">How it works</a>
			<a href="#customers" class="hover:text-white transition-colors">Customers</a>
		</nav>
		<div class="flex items-center gap-4">
			<a href="/login" class="text-sm font-medium text-text-secondary hover:text-white transition-colors">Log in</a>
			<a href="/dashboard" class="px-5 py-2.5 rounded-full bg-cta text-black font-semibold text-sm hover:bg-cta/90 transition-all hover:shadow-[0_0_20px_rgba(242,166,43,0.4)]">
				Enter Platform
			</a>
		</div>
	</div>
</header>

<!-- Hero Section -->
<section class="relative min-h-[95vh] flex items-center justify-center overflow-hidden pt-20">
	<!-- Background Ambient Glows -->
	<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-secondary/50 rounded-full blur-[120px] pointer-events-none z-0"></div>
	<div class="absolute top-0 right-0 w-[400px] h-[400px] bg-accent/20 rounded-full blur-[100px] pointer-events-none z-0"></div>
	
	<div class="relative z-10 max-w-5xl mx-auto px-6 text-center">
		{#if visible}
			<div 
				in:fly={{ y: 30, duration: 1000, delay: 100 }}
				class="inline-block mb-6 px-4 py-1.5 rounded-full border border-accent/30 bg-secondary/30 backdrop-blur-sm text-sm text-accent font-medium tracking-wide shadow-[0_0_15px_rgba(164,123,224,0.3)]">
				✨ Powered by Explainable AI & Reinforcement Learning
			</div>
			
			<h1 
				in:fly={{ y: 30, duration: 1000, delay: 300 }}
				class="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-[1.1]">
				Next-Generation Marketing <br/>
				<span class="text-accent font-serif italic font-normal tracking-normal drop-shadow-[0_0_20px_rgba(164,123,224,0.4)]">Decision Intelligence</span>
			</h1>
			
			<p 
				in:fly={{ y: 30, duration: 1000, delay: 500 }}
				class="text-lg md:text-xl text-text-secondary max-w-3xl mx-auto mb-10 leading-relaxed">
				Stop guessing which leads will convert and where to spend your budget. 
				Our platform uses cutting-edge machine learning to predict conversion, explain <span class="text-white font-medium">why</span>, and optimize your multi-channel budget.
			</p>
			
			<div 
				in:fly={{ y: 30, duration: 1000, delay: 700 }}
				class="flex flex-col sm:flex-row items-center justify-center gap-6">
				<a href="/dashboard" class="px-8 py-4 rounded-full bg-cta text-card font-bold text-lg hover:bg-cta/90 transition-all shadow-[0_0_30px_rgba(242,166,43,0.4)] hover:shadow-[0_0_40px_rgba(242,166,43,0.6)] transform hover:-translate-y-1">
					Get Started Free
				</a>
				<a href="/login" class="px-8 py-4 rounded-full bg-card border border-white/10 text-white font-semibold text-lg hover:bg-secondary transition-all hover:border-accent/50 group">
					Sign In <span class="inline-block transition-transform group-hover:translate-x-1">→</span>
				</a>
			</div>
		{/if}
	</div>

	<!-- Decorative Floating Elements -->
	{#if visible}
		<div in:fly={{ x: -50, duration: 1500, delay: 1000 }} class="hidden lg:block absolute left-10 top-1/3 bg-card/80 backdrop-blur-md border border-white/10 p-5 rounded-2xl shadow-[0_10px_40px_rgba(0,0,0,0.5)] animate-[bounce_6s_infinite]">
			<div class="flex items-center gap-3 mb-2">
				<div class="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_10px_#4ade80]"></div>
				<span class="text-xs font-bold text-text-secondary uppercase tracking-wider">Lead Scored</span>
			</div>
			<div class="text-xl font-bold">Sarah Jenkins</div>
			<div class="text-sm text-accent mt-1">94% Conversion Probability</div>
		</div>

		<div in:fly={{ x: 50, duration: 1500, delay: 1200 }} class="hidden lg:block absolute right-10 top-1/2 bg-card/80 backdrop-blur-md border border-white/10 p-5 rounded-2xl shadow-[0_10px_40px_rgba(0,0,0,0.5)] animate-[bounce_5s_infinite_1s]">
			<div class="flex items-center gap-3 mb-2">
				<div class="w-2 h-2 rounded-full bg-cta shadow-[0_0_10px_#F2A62B]"></div>
				<span class="text-xs font-bold text-text-secondary uppercase tracking-wider">RL Agent Action</span>
			</div>
			<div class="text-lg font-bold">Shift +15% to Social</div>
			<div class="text-sm text-white/70 mt-1">Expected ROI increase: +4.2%</div>
		</div>
	{/if}
</section>

<!-- Pipeline Section -->
<section id="pipeline" class="py-24 bg-primary relative border-t border-white/5">
	<div class="max-w-7xl mx-auto px-6">
		<div class="text-center mb-16">
			<h2 class="text-3xl md:text-5xl font-bold mb-4">The <span class="text-accent font-serif italic">Intelligence</span> Pipeline</h2>
			<p class="text-text-secondary text-lg">How we turn your raw marketing data into automated budget decisions.</p>
		</div>

		<div class="relative">
			<!-- Connecting Line -->
			<div class="hidden md:block absolute top-1/2 left-0 w-full h-1 bg-gradient-to-r from-transparent via-accent/50 to-transparent -translate-y-1/2 z-0"></div>

			<div class="grid grid-cols-1 md:grid-cols-4 gap-8 relative z-10">
				{#if pipelineVisible}
					<div in:fly={{ y: 50, duration: 800, delay: 0 }} class="bg-card border border-white/5 p-6 rounded-2xl shadow-xl hover:-translate-y-2 transition-transform text-center relative overflow-hidden group">
						<div class="absolute inset-0 bg-gradient-to-b from-accent/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
						<div class="w-16 h-16 mx-auto bg-secondary rounded-full flex items-center justify-center mb-4 border border-accent/30 shadow-[0_0_15px_rgba(164,123,224,0.2)]">
							<span class="text-2xl">📊</span>
						</div>
						<h3 class="font-bold text-xl mb-2 text-white">1. Connect Data</h3>
						<p class="text-sm text-text-secondary">Import historical campaigns, leads, and engagement metrics.</p>
					</div>

					<div in:fly={{ y: 50, duration: 800, delay: 200 }} class="bg-card border border-white/5 p-6 rounded-2xl shadow-xl hover:-translate-y-2 transition-transform text-center relative overflow-hidden group">
						<div class="absolute inset-0 bg-gradient-to-b from-accent/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
						<div class="w-16 h-16 mx-auto bg-secondary rounded-full flex items-center justify-center mb-4 border border-accent/30 shadow-[0_0_15px_rgba(164,123,224,0.2)]">
							<span class="text-2xl">🧠</span>
						</div>
						<h3 class="font-bold text-xl mb-2 text-white">2. Predict</h3>
						<p class="text-sm text-text-secondary">XGBoost & Random Forest models predict conversion probabilities.</p>
					</div>

					<div in:fly={{ y: 50, duration: 800, delay: 400 }} class="bg-card border border-white/5 p-6 rounded-2xl shadow-xl hover:-translate-y-2 transition-transform text-center relative overflow-hidden group">
						<div class="absolute inset-0 bg-gradient-to-b from-accent/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
						<div class="w-16 h-16 mx-auto bg-secondary rounded-full flex items-center justify-center mb-4 border border-accent/30 shadow-[0_0_15px_rgba(164,123,224,0.2)]">
							<span class="text-2xl">🔍</span>
						</div>
						<h3 class="font-bold text-xl mb-2 text-white">3. Explain</h3>
						<p class="text-sm text-text-secondary">SHAP values decode the AI, telling you exactly why a lead will buy.</p>
					</div>

					<div in:fly={{ y: 50, duration: 800, delay: 600 }} class="bg-card border border-cta/30 p-6 rounded-2xl shadow-xl hover:-translate-y-2 transition-transform text-center relative overflow-hidden group">
						<div class="absolute inset-0 bg-gradient-to-b from-cta/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
						<div class="w-16 h-16 mx-auto bg-secondary rounded-full flex items-center justify-center mb-4 border border-cta shadow-[0_0_20px_rgba(242,166,43,0.4)]">
							<span class="text-2xl">💰</span>
						</div>
						<h3 class="font-bold text-xl mb-2 text-cta">4. Optimize Budget</h3>
						<p class="text-sm text-text-secondary">RL Agent reallocates your budget across channels for max ROI.</p>
					</div>
				{/if}
			</div>
		</div>
	</div>
</section>

<!-- Features Grid -->
<section id="features" class="py-24 bg-card relative z-10 border-t border-white/5">
	<div class="max-w-7xl mx-auto px-6">
		<div class="text-center mb-20">
			<h2 class="text-3xl md:text-5xl font-bold mb-6">Built for <span class="text-accent font-serif italic">performance.</span></h2>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-8">
			<!-- Feature Cards (same as before but enhanced hover states) -->
			<div class="p-8 rounded-3xl bg-primary border border-white/5 hover:border-accent/50 hover:shadow-[0_0_30px_rgba(164,123,224,0.15)] transition-all duration-300 group">
				<div class="w-14 h-14 rounded-2xl bg-secondary flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-accent/20 transition-all">
					<span class="text-2xl">🎯</span>
				</div>
				<h3 class="text-2xl font-bold mb-3">Predictive Lead Scoring</h3>
				<p class="text-text-secondary leading-relaxed">Know exactly who will convert. We compare Logistic Regression, Random Forest, and XGBoost to give you the most accurate prediction models.</p>
			</div>

			<div class="p-8 rounded-3xl bg-primary border border-white/5 hover:border-accent/50 hover:shadow-[0_0_30px_rgba(164,123,224,0.15)] transition-all duration-300 group">
				<div class="w-14 h-14 rounded-2xl bg-secondary flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-accent/20 transition-all">
					<span class="text-2xl">💡</span>
				</div>
				<h3 class="text-2xl font-bold mb-3">Explainable AI (SHAP)</h3>
				<p class="text-text-secondary leading-relaxed">Never trust a black box again. For every prediction, the platform explicitly tells you <em class="text-white font-serif">why</em> using SHAP values.</p>
			</div>
		</div>
	</div>
</section>

<!-- Visual Showcase Section -->
<section class="py-24 bg-card relative z-10 border-t border-white/5 overflow-hidden">
	<div class="max-w-7xl mx-auto px-6">
		<div class="text-center mb-16">
			<h2 class="text-3xl md:text-5xl font-bold mb-4">See the <span class="text-accent font-serif italic">unseen.</span></h2>
			<p class="text-text-secondary text-lg max-w-2xl mx-auto">High-fidelity data visualizations and reinforcement learning optimization dashboards.</p>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
			<!-- Graph Analytics Image -->
			<div class="relative group">
				<div class="absolute -inset-2 bg-gradient-to-r from-accent to-secondary rounded-2xl blur opacity-30 group-hover:opacity-70 transition duration-1000 group-hover:duration-200"></div>
				<img src="/graph_analytics.jpg" alt="Data Analytics Visualization" class="relative rounded-2xl border border-white/10 shadow-2xl transform transition duration-500 hover:scale-[1.02]">
				<div class="absolute -bottom-6 -right-6 bg-card/90 backdrop-blur-md p-4 rounded-xl border border-white/10 shadow-xl">
					<p class="text-sm font-bold text-accent">K-Means Clustering Active</p>
					<p class="text-xs text-text-secondary">Analyzing 8,000+ customer patterns</p>
				</div>
			</div>

			<!-- RL Dashboard Image -->
			<div class="relative group mt-12 lg:mt-0">
				<div class="absolute -inset-2 bg-gradient-to-r from-cta to-accent rounded-2xl blur opacity-30 group-hover:opacity-70 transition duration-1000 group-hover:duration-200"></div>
				<img src="/rl_optimization.jpg" alt="RL Budget Optimization Dashboard" class="relative rounded-2xl border border-white/10 shadow-2xl transform transition duration-500 hover:scale-[1.02]">
				<div class="absolute -top-6 -left-6 bg-card/90 backdrop-blur-md p-4 rounded-xl border border-white/10 shadow-xl">
					<p class="text-sm font-bold text-cta">PPO Agent Training</p>
					<p class="text-xs text-text-secondary">Expected ROI: +312%</p>
				</div>
			</div>
		</div>
	</div>
</section>

<!-- Happy Customers Section -->
<section id="customers" class="py-24 bg-primary relative border-t border-white/5 overflow-hidden">
	<!-- Background glow -->
	<div class="absolute left-0 bottom-0 w-[600px] h-[600px] bg-secondary/30 rounded-full blur-[100px] pointer-events-none"></div>

	<div class="max-w-7xl mx-auto px-6 relative z-10">
		<div class="text-center mb-16">
			<h2 class="text-3xl md:text-5xl font-bold mb-4">Trusted by <span class="text-accent font-serif italic">marketers.</span></h2>
			<p class="text-text-secondary text-lg">See how DecisionIntel is transforming marketing teams.</p>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
			{#if customersVisible}
				<div in:scale={{ duration: 600, delay: 0, start: 0.95 }} class="bg-card p-8 rounded-3xl border border-white/5 hover:border-white/20 transition-colors">
					<div class="flex items-center gap-4 mb-6">
						<div class="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center text-accent font-bold text-xl border border-accent/30">JS</div>
						<div>
							<h4 class="font-bold text-white">John Smith</h4>
							<p class="text-xs text-text-secondary">CMO at TechCorp</p>
						</div>
					</div>
					<p class="text-text-secondary italic">"The RL Agent reallocated our budget automatically and lowered our CAC by 22% in the first month. It's like having a data scientist on staff 24/7."</p>
					<div class="mt-6 flex text-cta">★★★★★</div>
				</div>

				<div in:scale={{ duration: 600, delay: 150, start: 0.95 }} class="bg-card p-8 rounded-3xl border border-white/5 hover:border-white/20 transition-colors">
					<div class="flex items-center gap-4 mb-6">
						<div class="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center text-accent font-bold text-xl border border-accent/30">AD</div>
						<div>
							<h4 class="font-bold text-white">Amanda Doe</h4>
							<p class="text-xs text-text-secondary">VP of Marketing</p>
						</div>
					</div>
					<p class="text-text-secondary italic">"The SHAP explanations completely changed how we write copy. We now know exactly which features drive high-income users to convert."</p>
					<div class="mt-6 flex text-cta">★★★★★</div>
				</div>

				<div in:scale={{ duration: 600, delay: 300, start: 0.95 }} class="bg-card p-8 rounded-3xl border border-white/5 hover:border-white/20 transition-colors">
					<div class="flex items-center gap-4 mb-6">
						<div class="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center text-accent font-bold text-xl border border-accent/30">MK</div>
						<div>
							<h4 class="font-bold text-white">Michael Kim</h4>
							<p class="text-xs text-text-secondary">Growth Lead</p>
						</div>
					</div>
					<p class="text-text-secondary italic">"Finally, a lead scoring system that isn't a black box. Knowing a lead has a 95% probability lets our sales team prioritize effectively."</p>
					<div class="mt-6 flex text-cta">★★★★★</div>
				</div>
			{/if}
		</div>
	</div>
</section>

<!-- Final CTA & Footer / Contact Details -->
<section class="relative bg-card border-t border-white/5 pt-24 pb-12 overflow-hidden">
	<div class="absolute inset-0 flex items-center justify-center pointer-events-none">
		<div class="w-[1000px] h-[400px] bg-accent/10 blur-[150px] rounded-full"></div>
	</div>

	<div class="max-w-4xl mx-auto px-6 text-center relative z-10 mb-24">
		<h2 class="text-4xl md:text-6xl font-bold mb-8">Ready to <span class="text-accent font-serif italic">optimize?</span></h2>
		<p class="text-xl text-text-secondary mb-10">Join the AI-driven marketing revolution today.</p>
		<div class="flex flex-col sm:flex-row items-center justify-center gap-6">
			<a href="/register" class="px-10 py-5 rounded-full bg-cta text-black font-bold text-xl hover:bg-cta/90 transition-all shadow-[0_0_30px_rgba(242,166,43,0.3)] transform hover:scale-105">
				Start Free Trial
			</a>
			<a href="/login" class="px-10 py-5 rounded-full bg-secondary/50 border border-accent/30 text-white font-bold text-xl hover:bg-secondary transition-all">
				Sign In Now
			</a>
		</div>
	</div>

	<div class="max-w-7xl mx-auto px-6 border-t border-white/10 pt-12 flex flex-col md:flex-row justify-between items-center gap-6">
		<div class="flex items-center gap-2">
			<div class="w-6 h-6 rounded-md bg-gradient-to-br from-accent to-secondary flex items-center justify-center">
				<svg xmlns="http://www.w3.org/-2000/svg" class="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
					<path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
				</svg>
			</div>
			<span class="text-lg font-bold">Decision<span class="text-accent font-serif italic">Intel</span></span>
		</div>
		
		<div class="flex items-center gap-8 text-sm text-text-secondary">
			<p>📞 +1 (800) 123-4567</p>
			<p>✉️ support@decisionintel.ai</p>
			<p>🏢 123 Innovation Drive, Tech City</p>
		</div>

		<div class="flex gap-4">
			<a href="/privacy" class="text-text-secondary hover:text-white transition-colors">Privacy</a>
			<a href="/terms" class="text-text-secondary hover:text-white transition-colors">Terms</a>
		</div>
	</div>
</section>
