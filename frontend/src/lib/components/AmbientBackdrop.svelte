<script lang="ts">
	/**
	 * Shared ambient backdrop for the public site and the auth screens.
	 *
	 * Decorative only (`aria-hidden`, `pointer-events: none`) and painted as a
	 * fixed layer behind the page content. It layers four things, each tuned
	 * low enough that no panel, form field or heading has to fight it:
	 *
	 *   1. a soft purple/lavender wash (two wide radial blooms),
	 *   2. two very slow flowing wave/mesh bands along the lower edge,
	 *   3. a masked dot field plus a handful of tiny glowing points,
	 *   4. a minimal abstract analytics motif (bars + trend line).
	 *
	 * Every colour is a token, so the same markup reads as a deep violet
	 * atmosphere in the dark theme and a pale lavender one in light without
	 * any page having to know which theme is active.
	 *
	 * The SVG paint is applied through CSS classes rather than presentation
	 * attributes: `var()` is not reliably substituted inside attributes like
	 * `stop-color`/`fill`, and an unresolved value falls back to the initial
	 * colour (black), which would show up as dull dark bands.
	 */
	let { data = true }: { data?: boolean } = $props();

	// Unique per instance so two backdrops on one page cannot share gradients.
	const uid = $props.id();
</script>

<div class="ambient" aria-hidden="true">
	<div class="wash"></div>

	<svg class="waves" viewBox="0 0 1440 520" preserveAspectRatio="none" focusable="false">
		<defs>
			<linearGradient id="{uid}-wave" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" class="wave wave-top" />
				<stop offset="100%" class="wave wave-fade" />
			</linearGradient>
			<linearGradient id="{uid}-edge" x1="0" y1="0" x2="1" y2="0">
				<stop offset="0%" class="edge edge-fade" />
				<stop offset="18%" class="edge edge-solid" />
				<stop offset="82%" class="edge edge-solid" />
				<stop offset="100%" class="edge edge-fade" />
			</linearGradient>
		</defs>

		<!-- Back wave: a wide, slow swell that only reads as depth. -->
		<path
			d="M0 300 C 180 236 320 344 520 306 C 720 268 860 178 1080 214 C 1250 244 1360 300 1440 284 L1440 520 L0 520 Z"
			fill="url(#{uid}-wave)"
		/>
		<!-- Front wave: slightly lower and crisper, so the two layers parallax. -->
		<path
			d="M0 372 C 200 322 300 404 520 380 C 740 356 900 276 1120 306 C 1280 328 1380 372 1440 360 L1440 520 L0 520 Z"
			fill="url(#{uid}-wave)"
		/>
		<path
			d="M0 372 C 200 322 300 404 520 380 C 740 356 900 276 1120 306 C 1280 328 1380 372 1440 360"
			fill="none"
			stroke="url(#{uid}-edge)"
			stroke-width="1.25"
			stroke-linecap="round"
		/>
	</svg>

	<div class="dots"></div>

	<span class="spark spark-a"></span>
	<span class="spark spark-b"></span>
	<span class="spark spark-c"></span>

	{#if data}
		<svg class="data" viewBox="0 0 320 200" fill="none" focusable="false">
			<!-- baseline grid -->
			<path d="M0 160H320M0 110H320M0 60H320" class="data-grid" stroke-width="1" />
			<!-- bars -->
			<rect x="18" y="112" width="22" height="48" rx="6" class="data-bar" />
			<rect x="54" y="86" width="22" height="74" rx="6" class="data-bar" />
			<rect x="90" y="128" width="22" height="32" rx="6" class="data-bar" />
			<rect x="126" y="70" width="22" height="90" rx="6" class="data-bar" />
			<rect x="162" y="98" width="22" height="62" rx="6" class="data-bar" />
			<rect x="198" y="52" width="22" height="108" rx="6" class="data-bar-strong" />
			<rect x="234" y="80" width="22" height="80" rx="6" class="data-bar" />
			<rect x="270" y="38" width="22" height="122" rx="6" class="data-bar-strong" />
			<!-- trend line over the bars -->
			<path
				d="M29 104 L65 74 L101 118 L137 58 L173 90 L209 40 L245 68 L281 26"
				class="data-line"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
			<circle cx="281" cy="26" r="4.5" class="data-line" />
		</svg>
	{/if}
</div>

<style>
	.ambient {
		position: fixed;
		inset: 0;
		z-index: 0;
		overflow: hidden;
		pointer-events: none;
		user-select: none;

		/* Dark theme (the design of record): a violet atmosphere. */
		--di-amb-wash-a: rgba(164, 123, 224, 0.20);
		--di-amb-wash-b: rgba(124, 58, 237, 0.13);
		--di-amb-wave: #A47BE0;
		--di-amb-line: rgba(200, 165, 240, 0.55);
		--di-amb-dot: rgba(201, 170, 245, 0.9);
		--di-amb-dot-field: rgba(164, 123, 224, 0.30);
		--di-amb-data-bar: rgba(164, 123, 224, 0.22);
		--di-amb-data-bar-strong: rgba(196, 160, 245, 0.34);
		--di-amb-data-line: rgba(164, 123, 224, 0.18);
		--di-amb-data-line-strong: rgba(201, 170, 245, 0.55);
	}

	/* Light theme: the same composition, remapped to a pale lavender so the
	   page reads as a lit surface rather than a blank sheet. */
	:global(html.di-light) .ambient {
		--di-amb-wash-a: rgba(109, 40, 217, 0.13);
		--di-amb-wash-b: rgba(91, 33, 182, 0.09);
		--di-amb-wave: #6D28D9;
		--di-amb-line: rgba(91, 33, 182, 0.30);
		--di-amb-dot: rgba(109, 40, 217, 0.5);
		--di-amb-dot-field: rgba(91, 33, 182, 0.16);
		--di-amb-data-bar: rgba(109, 40, 217, 0.10);
		--di-amb-data-bar-strong: rgba(91, 33, 182, 0.16);
		--di-amb-data-line: rgba(91, 33, 182, 0.10);
		--di-amb-data-line-strong: rgba(109, 40, 217, 0.34);
	}

	/* ---- 1. Soft wash ---------------------------------------------- */

	.wash {
		position: absolute;
		inset: -12%;
		background:
			radial-gradient(58rem 40rem at 10% -6%, var(--di-amb-wash-a) 0%, transparent 62%),
			radial-gradient(50rem 36rem at 96% 6%, var(--di-amb-wash-b) 0%, transparent 60%),
			radial-gradient(44rem 32rem at 62% 104%, var(--di-amb-wash-b) 0%, transparent 62%);
	}

	/* ---- 2. Flowing waves ------------------------------------------ */

	/* Painted through CSS, not presentation attributes, so the tokens resolve
	   everywhere instead of falling back to black. */
	.wave { stop-color: var(--di-amb-wave); }
	.wave-top { stop-opacity: 0.55; }
	.wave-fade { stop-opacity: 0; }
	.edge { stop-color: var(--di-amb-line); }
	.edge-solid { stop-opacity: 0.9; }
	.edge-fade { stop-opacity: 0; }

	.waves {
		position: absolute;
		inset: auto 0 0 0;
		width: 100%;
		height: min(58vh, 30rem);
		opacity: 0.5;
	}

	/* ---- 3. Dot field + a few glowing points ----------------------- */

	.dots {
		position: absolute;
		inset: 0;
		background-image: radial-gradient(circle at center, var(--di-amb-dot-field) 1.1px, transparent 1.3px);
		background-size: 26px 26px;
		/* Fade the field out towards the edges and the lower half so it reads
		   as texture, not as a visible grid. */
		-webkit-mask-image: radial-gradient(120% 78% at 78% 4%, #000 0%, rgba(0, 0, 0, .45) 45%, transparent 78%);
		mask-image: radial-gradient(120% 78% at 78% 4%, #000 0%, rgba(0, 0, 0, .45) 45%, transparent 78%);
	}

	.spark {
		position: absolute;
		border-radius: 999px;
		background: var(--di-amb-dot);
		filter: blur(0.5px);
		box-shadow: 0 0 18px 6px var(--di-amb-dot-field);
	}

	.spark-a { top: 18%; left: 6%; width: 5px; height: 5px; }
	.spark-b { top: 62%; right: 11%; width: 4px; height: 4px; }
	.spark-c { top: 34%; right: 28%; width: 3px; height: 3px; }

	/* ---- 4. Abstract analytics motif -------------------------------- */

	.data {
		position: absolute;
		right: max(2rem, 5vw);
		bottom: min(14vh, 9rem);
		width: min(20rem, 34vw);
		height: auto;
		opacity: 0.5;
	}

	.data-grid { stroke: var(--di-amb-data-line); }
	.data-bar { fill: var(--di-amb-data-bar); }
	.data-bar-strong { fill: var(--di-amb-data-bar-strong); }
	.data-line { stroke: var(--di-amb-data-line-strong); fill: var(--di-amb-data-line-strong); }

	@media (max-width: 60rem) {
		.data { display: none; }
		.waves { height: min(42vh, 20rem); }
	}

	@media (prefers-reduced-motion: no-preference) {
		.spark { animation: ambient-drift 16s ease-in-out infinite alternate; }
		.spark-b { animation-duration: 21s; animation-delay: -4s; }
		.spark-c { animation-duration: 25s; animation-delay: -9s; }
		.dots { animation: ambient-fade 30s ease-in-out infinite alternate; }
	}

	@keyframes ambient-drift {
		from { transform: translate3d(0, 0, 0); }
		to { transform: translate3d(0, -14px, 0); }
	}

	@keyframes ambient-fade {
		from { opacity: 0.75; }
		to { opacity: 1; }
	}
</style>
