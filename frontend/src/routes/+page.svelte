<script lang="ts">
	import { onMount } from 'svelte';
	import { fly, scale } from 'svelte/transition';
	import OutlineIcon from '$lib/components/OutlineIcon.svelte';
import ThemeToggle from '$lib/ThemeToggle.svelte';

	let visible = $state(false);

	let pipelineVisible = $state(false);
	let institutionsVisible = $state(false);

	const PIPELINE = [
		{ title: 'Connect data', icon: 'clipboard', copy: 'Import historical admission campaigns, student enquiries, and engagement metrics.' },
		{ title: 'Predict', icon: 'sparkle', copy: 'XGBoost and Random Forest models predict admission conversion probability.' },
		{ title: 'Explain', icon: 'help', copy: 'SHAP values decode the AI, showing exactly why a student is likely to enroll.' },
		{ title: 'Optimize budget', icon: 'briefcase', copy: 'AI-driven recommendations reallocate your budget across channels for maximum impact.' }
	];

	const FEATURES = [
		{ title: 'Admission Conversion Prediction', icon: 'chart', copy: 'Identify which student enquiries are most likely to convert. Compare Logistic Regression, Random Forest, and XGBoost to deliver the most accurate prediction models.' },
		{ title: 'Explainable Admission Prediction', icon: 'sparkle', copy: 'Never trust a black box again. For every prediction, the platform explains why using SHAP values, so your admission team understands the reasoning.' },
		{ title: 'Marketing Channel Attribution', icon: 'users', copy: 'Understand which channels drive admissions. Analyze Google Ads, Instagram, Facebook, education portals, referrals, and walk-in enquiries.' },
		{ title: 'Budget Optimization', icon: 'briefcase', copy: 'Optimize your admission marketing budget across channels using AI-driven recommendations and What-If simulation scenarios.' }
	];

	const VOICES = [
		{ initials: 'JS', name: 'John Smith', role: 'Director of Admissions, Tech University', quote: 'Decision-Intel helped us identify which marketing channels drive the most qualified student enquiries. Our admission team now prioritizes follow-ups based on data, not guesswork.' },
		{ initials: 'AD', name: 'Amanda Doe', role: 'VP of Admissions', quote: 'The SHAP explanations completely changed how we approach student counselling. We now understand exactly which factors influence prospective students to enroll.' },
		{ initials: 'MK', name: 'Michael Kim', role: 'Admission Manager', quote: 'Finally, an admission intelligence platform that is not a black box. Knowing a student lead has a 95% admission probability lets our team focus resources where they matter most.' }
	];

	onMount(() => {
		visible = true;

		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.target.id === 'pipeline' && entry.isIntersecting) pipelineVisible = true;
					if (entry.target.id === 'institutions' && entry.isIntersecting) institutionsVisible = true;
				});
			},
			{ threshold: 0.2 }
		);

		const pipelineEl = document.getElementById('pipeline');
		const institutionsEl = document.getElementById('institutions');

		if (pipelineEl) observer.observe(pipelineEl);
		if (institutionsEl) observer.observe(institutionsEl);

		return () => observer.disconnect();
	});
</script>

<svelte:head>
	<title>DecisionIntel | Explainable AI for Student Admissions</title>
	<meta name="description" content="Decision-Intel uses explainable AI, admission prediction, and marketing intelligence to help institutions convert student enquiries." />
</svelte:head>

<div class="landing">
	<div class="di-glow" aria-hidden="true"></div>

	<!-- Navbar -->
	<header class="navbar">
		<div class="shell navbar-inner">
			<a href="/" class="brand">
				<span class="di-brand-mark"><OutlineIcon name="cap" size={20} strokeWidth={1.8} /></span>
				<span class="di-brand-name">Decision<em>Intel</em></span>
			</a>
			<nav class="nav" aria-label="Primary">
				<a href="#features">Features</a>
				<a href="#pipeline">How it works</a>
				<a href="#institutions">Institutions</a>
			</nav>
		<div class="nav-actions">
			<ThemeToggle />
			<a href="/login" class="nav-login">Log in</a>
			<a href="/register" class="di-btn di-btn-primary nav-cta">Get started</a>
		</div>

		</div>
	</header>

	<!-- Hero -->
	<section class="hero">
		<div class="shell hero-inner">
			{#if visible}
				<div in:fly={{ y: 30, duration: 900, delay: 100 }} class="badge">
					<OutlineIcon name="sparkle" size={15} />
					Powered by Explainable AI &amp; Marketing Intelligence
				</div>

				<h1 in:fly={{ y: 30, duration: 900, delay: 250 }}>
					Turn Student Enquiries into<br />
					<em>Smarter Admission Decisions</em>
				</h1>

				<p in:fly={{ y: 30, duration: 900, delay: 450 }} class="lede">
					Decision-Intel uses AI-powered prediction, explainability, and marketing intelligence to help educational
					institutions improve admission lead conversion and make data-driven marketing decisions.
				</p>

				<div in:fly={{ y: 30, duration: 900, delay: 650 }} class="hero-actions">
					<a href="/register" class="di-btn di-btn-primary hero-cta">Create a student account</a>
					<a href="/login" class="di-btn di-btn-secondary hero-secondary">Sign in</a>
				</div>
			{/if}
		</div>

		{#if visible}
			<div in:fly={{ x: -40, duration: 1200, delay: 900 }} class="float float-left">
				<div class="float-head">
					<span class="dot dot-green"></span>
					Student lead scored
				</div>
				<p class="float-title">Sarah Jenkins</p>
				<p class="float-accent">94% admission probability</p>
			</div>

			<div in:fly={{ x: 40, duration: 1200, delay: 1100 }} class="float float-right">
				<div class="float-head">
					<span class="dot dot-purple"></span>
					AI budget insight
				</div>
				<p class="float-title">Shift +15% to Social</p>
				<p class="float-muted">Expected conversion improvement: +4.2%</p>
			</div>
		{/if}
	</section>

	<!-- Pipeline -->
	<section id="pipeline" class="section">
		<div class="shell">
			<div class="section-head">
				<h2>The <em>Intelligence</em> Pipeline</h2>
				<p>How we turn your raw admission data into actionable budget decisions.</p>
			</div>

			<div class="pipeline">
				{#if pipelineVisible}
					{#each PIPELINE as step, index}
						<article in:fly={{ y: 50, duration: 700, delay: index * 180 }} class="card pipeline-card">
							<span class="step-icon"><OutlineIcon name={step.icon} size={24} strokeWidth={1.6} /></span>
							<h3>{index + 1}. {step.title}</h3>
							<p>{step.copy}</p>
						</article>
					{/each}
				{/if}
			</div>
		</div>
	</section>

	<!-- Features -->
	<section id="features" class="section section-muted">
		<div class="shell">
			<div class="section-head">
				<h2>Built for <em>admission intelligence.</em></h2>
			</div>

			<div class="features">
				{#each FEATURES as feature}
					<article class="card feature">
						<span class="feature-icon"><OutlineIcon name={feature.icon} size={24} strokeWidth={1.6} /></span>
						<h3>{feature.title}</h3>
						<p>{feature.copy}</p>
					</article>
				{/each}
			</div>
		</div>
	</section>

	<!-- Showcase -->
	<section class="section">
		<div class="shell">
			<div class="section-head">
				<h2>See the <em>unseen.</em></h2>
				<p>High-fidelity data visualizations and explainable AI dashboards for admission intelligence.</p>
			</div>

			<div class="showcase">
				<figure class="shot">
					<div class="shot-glow" aria-hidden="true"></div>
					<img src="/graph_analytics.jpg" alt="Student segmentation analytics" loading="lazy" />
					<figcaption class="shot-tag">
						<strong>K-Means clustering active</strong>
						<span>Analyzing 8,000+ student patterns</span>
					</figcaption>
				</figure>

				<figure class="shot">
					<div class="shot-glow shot-glow-alt" aria-hidden="true"></div>
					<img src="/rl_optimization.jpg" alt="Budget optimization dashboard" loading="lazy" />
					<figcaption class="shot-tag shot-tag-alt">
						<strong>AI model training</strong>
						<span>Admission prediction accuracy: 91%</span>
					</figcaption>
				</figure>
			</div>
		</div>
	</section>

	<!-- Voices -->
	<section id="institutions" class="section section-muted">
		<div class="shell">
			<div class="section-head">
				<h2>Trusted by <em>educational institutions.</em></h2>
				<p>See how Decision-Intel is transforming admission decision-making.</p>
			</div>

			<div class="voices">
				{#if institutionsVisible}
					{#each VOICES as voice, index}
						<article in:scale={{ duration: 600, delay: index * 150, start: 0.95 }} class="card voice">
							<div class="voice-head">
								<span class="voice-avatar">{voice.initials}</span>
								<div>
									<h4>{voice.name}</h4>
									<p>{voice.role}</p>
								</div>
							</div>
							<blockquote>“{voice.quote}”</blockquote>
							<div class="stars" aria-label="Five out of five">★★★★★</div>
						</article>
					{/each}
				{/if}
			</div>
		</div>
	</section>

	<!-- Final CTA + footer -->
	<section class="closing">
		<div class="shell closing-inner">
			<h2>Ready to <em>optimize?</em></h2>
			<p>Start making data-driven admission decisions today.</p>
			<div class="hero-actions">
				<a href="/register" class="di-btn di-btn-primary hero-cta">Create a student account</a>
				<a href="/login" class="di-btn di-btn-secondary hero-secondary">Sign in</a>
			</div>
		</div>

		<footer class="shell footer">
			<a href="/" class="brand">
				<span class="di-brand-mark footer-mark"><OutlineIcon name="cap" size={16} strokeWidth={1.9} /></span>
				<span class="di-brand-name">Decision<em>Intel</em></span>
			</a>
			<div class="footer-contact">
				<p>+1 (800) 123-4567</p>
				<p>support@decisionintel.ai</p>
				<p>123 Innovation Drive, Tech City</p>
			</div>
			<div class="footer-links">
				<a href="/privacy">Privacy</a>
				<a href="/terms">Terms</a>
			</div>
		</footer>
	</section>
</div>

<style>
    .landing { position:relative; overflow-x:clip; }
    .shell { width:100%; max-width:80rem; margin-inline:auto; padding-inline:1.5rem; }

    /* ---- Navbar ---------------------------------------------------- */
    .navbar { position:fixed; top:0; left:0; right:0; z-index:50; border-bottom:1px solid var(--di-border); background-color:rgba(247,245,242,.86); backdrop-filter:blur(12px); }
    .navbar-inner { display:flex; align-items:center; justify-content:space-between; height:5rem; }
    .brand { display:flex; align-items:center; gap:.625rem; text-decoration:none; }
    .nav { display:none; gap:2rem; font-size:.875rem; font-weight:600; }
    .nav a { color:var(--di-muted); text-decoration:none; transition:color .15s ease; }
    .nav a:hover { color:var(--di-accent-ink); }
    .nav-actions { display:flex; align-items:center; gap:1rem; }
    .nav-login { font-size:.875rem; font-weight:600; color:var(--di-muted); text-decoration:none; }
    .nav-login:hover { color:var(--di-accent-ink); }
    .nav-cta { padding:.5rem 1.125rem; }

    /* ---- Hero ------------------------------------------------------ */
    .hero { position:relative; display:flex; align-items:center; justify-content:center; min-height:92vh; padding:7rem 0 5rem; }
    .hero-inner { position:relative; z-index:1; text-align:center; }
    .badge {
        display:inline-flex; align-items:center; gap:.5rem; margin-bottom:1.5rem; padding:.4375rem 1rem;
        border-radius:999px; border:1px solid var(--di-accent-line); background-color:var(--di-accent-soft);
        font-size:.8125rem; font-weight:600; color:var(--di-accent-ink);
    }
    .hero h1 { font-size:clamp(2.25rem,5.5vw,4.25rem); font-weight:800; line-height:1.08; letter-spacing:-.03em; margin:0 0 2rem; }
    .hero h1 em, .section-head em, .closing h2 em { font-family:Georgia,'Times New Roman',serif; font-style:italic; font-weight:400; color:var(--di-accent); }
    .lede { max-width:46rem; margin:0 auto 2.5rem; font-size:1.0625rem; line-height:1.75; color:var(--di-muted); }
    .hero-actions { display:flex; flex-direction:column; align-items:center; gap:1rem; }
    .hero-cta, .hero-secondary { padding:.875rem 1.75rem; font-size:1rem; }

    .float {
        display:none; position:absolute; z-index:1; padding:1.25rem 1.375rem;
        background-color:var(--di-surface); border:1px solid var(--di-border);
        border-radius:var(--di-radius); box-shadow:var(--di-shadow-lift);
    }
    .float-left { left:2.5rem; top:32%; animation:drift 7s ease-in-out infinite; }
    .float-right { right:2.5rem; top:50%; animation:drift 6s ease-in-out 1s infinite; }
    .float-head { display:flex; align-items:center; gap:.5rem; font-size:.6875rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:var(--di-muted); }
    .dot { width:.5rem; height:.5rem; border-radius:999px; }
    .dot-green { background-color:#256B4C; }
    .dot-purple { background-color:#6A31C4; }
    .float-title { margin:.5rem 0 0; font-size:1.125rem; font-weight:700; color:var(--di-text); }
    .float-accent { margin:.125rem 0 0; font-size:.875rem; font-weight:600; color:var(--di-accent-ink); }
    .float-muted { margin:.125rem 0 0; font-size:.875rem; color:var(--di-muted); }

    @keyframes drift { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-10px); } }

    /* ---- Sections -------------------------------------------------- */
    .section { position:relative; padding:5.5rem 0; }
    .section-muted { background-color:var(--di-surface-muted); border-block:1px solid var(--di-border); }
    .section-head { max-width:44rem; margin:0 auto 3.5rem; text-align:center; }
    .section-head h2 { font-size:clamp(1.75rem,3.6vw,2.75rem); font-weight:800; letter-spacing:-.025em; line-height:1.15; margin:0 0 1rem; }
    .section-head p { font-size:1.0625rem; line-height:1.7; color:var(--di-muted); margin:0; }

    .card { padding:1.75rem; background-color:var(--di-surface); border:1px solid var(--di-border); border-radius:var(--di-radius); box-shadow:var(--di-shadow); text-align:center; }

    .pipeline { position:relative; display:grid; grid-template-columns:repeat(1,minmax(0,1fr)); gap:1.5rem; }
    .pipeline-card { transition:transform .25s ease, box-shadow .25s ease; }
    .pipeline-card:hover { transform:translateY(-4px); box-shadow:var(--di-shadow-lift); }
    .step-icon, .feature-icon {
        display:grid; place-items:center; width:3.5rem; height:3.5rem; margin:0 auto 1.125rem;
        border-radius:16px; background-color:var(--di-accent-soft);
        border:1px solid var(--di-accent-line); color:var(--di-accent-ink);
    }
    .pipeline-card h3, .feature h3 { font-size:1.125rem; font-weight:700; margin:0 0 .5rem; }
    .pipeline-card p, .feature p { font-size:.875rem; line-height:1.7; color:var(--di-muted); margin:0; }

    .features { display:grid; grid-template-columns:repeat(1,minmax(0,1fr)); gap:1.5rem; }
    .feature { text-align:left; transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease; }
    .feature:hover { transform:translateY(-4px); border-color:var(--di-accent-line); box-shadow:var(--di-shadow-lift); }
    .feature-icon { margin:0 0 1.25rem; }
    .feature h3 { font-size:1.25rem; }

    .showcase { display:grid; grid-template-columns:repeat(1,minmax(0,1fr)); gap:3rem; align-items:center; }
    .shot { position:relative; margin:0; }
    .shot-glow { position:absolute; inset:-.5rem; border-radius:1.25rem; background-image:var(--di-accent-sheen); opacity:.16; filter:blur(1.5rem); }
    .shot-glow-alt { background-image:var(--di-accent-sheen); }
    .shot img { position:relative; display:block; width:100%; border-radius:var(--di-radius); border:1px solid var(--di-border); box-shadow:var(--di-shadow-lift); }
    .shot-tag {
        position:absolute; left:-.75rem; bottom:-.75rem; display:grid; gap:.125rem; margin:0;
        padding:.875rem 1.125rem; background-color:var(--di-surface);
        border:1px solid var(--di-border); border-radius:var(--di-radius-sm); box-shadow:var(--di-shadow-lift);
    }
    .shot-tag strong { font-size:.8125rem; color:var(--di-accent-ink); }
    .shot-tag span { font-size:.75rem; color:var(--di-muted); }
    .shot-tag-alt { left:auto; right:-.75rem; top:-.75rem; bottom:auto; }
    .shot-tag-alt strong { color:var(--di-accent-ink); }

    .voices { display:grid; grid-template-columns:repeat(1,minmax(0,1fr)); gap:1.5rem; }
    .voice { text-align:left; }
    .voice-head { display:flex; align-items:center; gap:1rem; margin-bottom:1.25rem; }
    .voice-avatar {
        display:grid; place-items:center; width:3rem; height:3rem; flex:none; border-radius:999px;
        background-color:var(--di-accent-soft); border:1px solid var(--di-accent-line);
        font-size:.875rem; font-weight:700; color:var(--di-accent-ink);
    }
    .voice h4 { margin:0; font-size:1rem; font-weight:700; }
    .voice-head p { margin:.125rem 0 0; font-size:.75rem; color:var(--di-muted); }
    .voice blockquote { margin:0; font-size:.875rem; line-height:1.75; color:var(--di-muted); font-style:italic; }
    .stars { margin-top:1.25rem; color:#6A31C4; letter-spacing:.1em; }

    /* ---- Closing --------------------------------------------------- */
    .closing { position:relative; padding:5.5rem 0 0; background-color:var(--di-surface-muted); border-top:1px solid var(--di-border); }
    .closing-inner { text-align:center; padding-bottom:4.5rem; }
    .closing h2 { font-size:clamp(2rem,4.5vw,3.25rem); font-weight:800; letter-spacing:-.03em; margin:0 0 1rem; }
    .closing p { font-size:1.0625rem; color:var(--di-muted); margin:0 0 2.5rem; }

    .footer { display:flex; flex-direction:column; align-items:center; gap:1.5rem; padding-block:2rem; border-top:1px solid var(--di-border); }
    .footer-mark { width:1.75rem; height:1.75rem; border-radius:9px; }
    .footer-contact { display:flex; flex-wrap:wrap; justify-content:center; gap:1.5rem; font-size:.8125rem; color:var(--di-muted); }
    .footer-contact p { margin:0; }
    .footer-links { display:flex; gap:1.5rem; font-size:.8125rem; font-weight:600; }
    .footer-links a { color:var(--di-muted); text-decoration:none; }
    .footer-links a:hover { color:var(--di-accent-ink); }

    @media (min-width: 768px) {
        .nav { display:flex; }
        .pipeline { grid-template-columns:repeat(2,minmax(0,1fr)); }
        .features { grid-template-columns:repeat(2,minmax(0,1fr)); }
        .showcase { grid-template-columns:repeat(2,minmax(0,1fr)); }
        .voices { grid-template-columns:repeat(3,minmax(0,1fr)); }
        .footer { flex-direction:row; justify-content:space-between; }
    }

    @media (min-width: 1024px) {
        .hero-actions { flex-direction:row; }
        .pipeline { grid-template-columns:repeat(4,minmax(0,1fr)); }
        .float { display:block; }
    }

    @media (max-width: 640px) {
        .shell { padding-inline:1.125rem; }
        .section { padding:3.5rem 0; }
        .hero { min-height:auto; padding:6.5rem 0 3.5rem; }
    }
</style>
