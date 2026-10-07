<script lang="ts">
	import OutlineIcon from './OutlineIcon.svelte';
	import type { ShellLinks } from '$lib/dashboard-header';

	/**
	 * Circular initial avatar + account dropdown for the signed-in shell.
	 *
	 * `initial` is the role letter (S / M / A) so the three workspaces stay
	 * instantly recognisable, with the person's name carried in the menu.
	 * Logout is the only red item and is deliberately given its own
	 * separated, filled row so it never reads as a quiet link.
	 */
	let {
		initial,
		name,
		email,
		roleLabel,
		links,
		onlogout
	}: {
		initial: string;
		name: string;
		email: string;
		roleLabel: string;
		links: ShellLinks;
		onlogout: () => void;
	} = $props();

	let open = $state(false);
	let root = $state<HTMLDivElement | null>(null);

	// No stopPropagation here: the click has to keep bubbling so the sibling
	// header dropdown's outside-click handler can see it and close. This
	// component ignores clicks that land inside its own root.
	function toggle() {
		open = !open;
	}

	function onWindowClick(event: MouseEvent) {
		if (open && root && !root.contains(event.target as Node)) open = false;
	}

	function onKeydown(event: KeyboardEvent) {
		if (event.key !== 'Escape' || !open) return;
		open = false;
		root?.querySelector<HTMLButtonElement>('.hprofile-trigger')?.focus();
	}
</script>

<svelte:window onclick={onWindowClick} onkeydown={onKeydown} />

<div class="hprofile" bind:this={root}>
	<button
		type="button"
		class="hprofile-trigger"
		aria-haspopup="menu"
		aria-expanded={open}
		aria-label={`Account menu for ${name}`}
		onclick={toggle}
	>
		<span class="hprofile-avatar">{initial}</span>
		<span class="hprofile-meta">
			<span class="hprofile-name">{name}</span>
			<span class="hprofile-role">{roleLabel}</span>
		</span>
		<span class="hprofile-caret"><OutlineIcon name="chevron-down" size={15} /></span>
	</button>

	{#if open}
		<div
			class="hprofile-menu"
			role="menu"
			aria-label="Account"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<div class="hprofile-head">
				<span class="hprofile-head-avatar">{initial}</span>
				<span class="hprofile-head-text">
					<span class="hprofile-head-role">{roleLabel}</span>
					<span class="hprofile-head-name">{name}</span>
					<span class="hprofile-head-mail">{email}</span>
				</span>
			</div>

			<a class="hprofile-item" role="menuitem" href={links.profile} onclick={() => (open = false)}>
				<OutlineIcon name="profile" size={18} />
				Profile
			</a>
			<a class="hprofile-item" role="menuitem" href={links.settings} onclick={() => (open = false)}>
				<OutlineIcon name="settings" size={18} />
				Settings
			</a>

			<div class="hprofile-sep" role="separator"></div>

			<button type="button" class="hprofile-item hprofile-danger" role="menuitem" onclick={onlogout}>
				<OutlineIcon name="logout" size={18} />
				Logout
			</button>
		</div>
	{/if}
</div>

<style>
	.hprofile { position: relative; flex: none; }

	.hprofile-trigger {
		display: flex;
		align-items: center;
		gap: .55rem;
		padding: .25rem .55rem .25rem .25rem;
		border-radius: 999px;
		border: 1px solid var(--di-border-strong);
		background-color: var(--di-surface);
		font: inherit;
		cursor: pointer;
		text-align: left;
		transition:
			border-color 160ms ease,
			background-color 160ms ease,
			box-shadow 160ms ease;
	}

	.hprofile-trigger:hover,
	.hprofile-trigger[aria-expanded='true'] {
		border-color: var(--di-accent);
		background-color: var(--di-accent-soft);
		box-shadow: 0 8px 18px -12px var(--di-accent-glow);
	}

	.hprofile-trigger:focus-visible {
		outline: 2px solid var(--di-accent);
		outline-offset: 3px;
	}

	.hprofile-avatar {
		display: grid;
		place-items: center;
		width: 2.125rem;
		height: 2.125rem;
		flex: none;
		border-radius: 999px;
		background-image: var(--di-accent-sheen);
		color: #FFFFFF;
		font-size: .8125rem;
		font-weight: 700;
		letter-spacing: .02em;
		box-shadow: 0 4px 10px -6px var(--di-accent-glow);
	}

	.hprofile-meta { display: none; min-width: 0; }

	.hprofile-name {
		display: block;
		font-size: .8125rem;
		font-weight: 650;
		color: var(--di-text);
		max-width: 9rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.hprofile-role {
		display: block;
		font-size: .625rem;
		font-weight: 600;
		letter-spacing: .1em;
		text-transform: uppercase;
		color: var(--di-accent-ink);
	}

	.hprofile-caret { display: inline-flex; flex: none; color: var(--di-muted); }

	@media (min-width: 30rem) {
		.hprofile-meta { display: block; }
		.hprofile-caret { display: inline-flex; }
	}

	@media (max-width: 29.99rem) {
		.hprofile-caret { display: none; }
		.hprofile-trigger { padding: .25rem; }
	}

	/* ---- Dropdown --------------------------------------------------- */

	.hprofile-menu {
		position: absolute;
		top: calc(100% + .6rem);
		right: 0;
		z-index: 60;
		width: 16.5rem;
		padding: .4rem;
		background-color: var(--di-surface);
		border: 1px solid var(--di-border-strong);
		border-radius: var(--di-radius);
		box-shadow: var(--di-shadow-lift);
		animation: hprofile-in 160ms ease-out;
	}

	@keyframes hprofile-in {
		from { opacity: 0; translate: 0 -6px; }
		to { opacity: 1; translate: 0 0; }
	}

	.hprofile-head {
		display: flex;
		align-items: center;
		gap: .7rem;
		padding: .6rem .6rem .7rem;
		margin-bottom: .25rem;
		border-bottom: 1px solid var(--di-border);
	}

	.hprofile-head-avatar {
		display: grid;
		place-items: center;
		width: 2.25rem;
		height: 2.25rem;
		flex: none;
		border-radius: 999px;
		background-image: var(--di-accent-sheen);
		color: #FFFFFF;
		font-size: .8125rem;
		font-weight: 700;
	}

	.hprofile-head-text { display: grid; gap: .05rem; min-width: 0; }

	.hprofile-head-role {
		font-size: .625rem;
		font-weight: 700;
		letter-spacing: .14em;
		text-transform: uppercase;
		color: var(--di-accent-ink);
	}

	.hprofile-head-name {
		font-size: .875rem;
		font-weight: 650;
		color: var(--di-text);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.hprofile-head-mail {
		font-size: .75rem;
		color: var(--di-muted);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.hprofile-item {
		display: flex;
		align-items: center;
		gap: .625rem;
		width: 100%;
		padding: .55rem .625rem;
		border: 1px solid transparent;
		border-radius: var(--di-radius-sm);
		font: inherit;
		font-size: .875rem;
		font-weight: 600;
		color: var(--di-text);
		background: none;
		cursor: pointer;
		text-align: left;
		text-decoration: none;
		transition: background-color 140ms ease, color 140ms ease;
	}

	.hprofile-item :global(svg) { color: var(--di-accent-ink); }

	.hprofile-item:hover {
		background-color: var(--di-accent-soft);
		color: var(--di-accent-ink);
	}

	.hprofile-sep {
		height: 1px;
		margin: .3rem .6rem;
		background-color: var(--di-border);
	}

	/* Logout stays unmistakably red: filled, not just tinted text. */
	.hprofile-danger {
		color: var(--di-red-ink);
		background-color: var(--di-red-soft);
		border-color: color-mix(in srgb, var(--di-red-ink) 28%, transparent);
		font-weight: 700;
	}

	.hprofile-danger :global(svg) { color: var(--di-red-ink); }

	.hprofile-danger:hover {
		color: #FFFFFF;
		background-color: var(--di-red-ink);
		border-color: var(--di-red-ink);
		box-shadow: 0 8px 18px -12px var(--di-red-ink);
	}

	.hprofile-danger:hover :global(svg) { color: #FFFFFF; }

	@media (prefers-reduced-motion: reduce) {
		.hprofile-menu { animation: none; }
	}
</style>
