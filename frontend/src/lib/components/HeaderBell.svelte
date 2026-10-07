<script lang="ts">
	import OutlineIcon from './OutlineIcon.svelte';
	import type { HeaderNotice } from '$lib/dashboard-header';

	/**
	 * Common notification bell for the signed-in shell.
	 *
	 * Owns its own open state and outside-click/Escape handling, so any
	 * header that drops it in gets the same behaviour. The panel is a plain
	 * list rendered from `items`; the shell decides what to pass.
	 */

	let {
		items = [],
		allHref = '#',
		allLabel = 'View all notifications'
	}: { items?: HeaderNotice[]; allHref?: string; allLabel?: string } = $props();

	let open = $state(false);
	let root = $state<HTMLDivElement | null>(null);
	const unread = $derived(items.filter(item => item.unread).length);

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
		root?.querySelector<HTMLButtonElement>('.hbell-trigger')?.focus();
	}
</script>

<svelte:window onclick={onWindowClick} onkeydown={onKeydown} />

<div class="hbell" bind:this={root}>
	<button
		type="button"
		class="hbell-trigger"
		aria-haspopup="dialog"
		aria-expanded={open}
		aria-label={unread ? `Notifications, ${unread} unread` : 'Notifications'}
		onclick={toggle}
	>
		<OutlineIcon name="notifications" size={19} />
		{#if unread}<span class="hbell-dot" aria-hidden="true">{unread}</span>{/if}
	</button>

	{#if open}
		<div
			class="hbell-panel"
			role="dialog"
			aria-label="Notifications"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<header class="hbell-head">
				<p class="hbell-title">Notifications</p>
				{#if unread}<span class="hbell-count">{unread} new</span>{/if}
			</header>

			{#if items.length}
				<ul class="hbell-list">
					{#each items as item}
						<li>
							<a class="hbell-item" class:unread={item.unread} href={item.href ?? allHref}>
								<span class="hbell-icon"><OutlineIcon name={item.icon ?? 'notifications'} size={16} /></span>
								<span class="hbell-body">
									<span class="hbell-item-title">{item.title}</span>
									<span class="hbell-item-detail">{item.detail}</span>
								</span>
								<span class="hbell-when">{item.when}</span>
							</a>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="hbell-empty">You are all caught up.</p>
			{/if}

			<footer class="hbell-foot">
				<a class="hbell-all" href={allHref}>{allLabel}</a>
			</footer>
		</div>
	{/if}
</div>

<style>
	.hbell { position: relative; flex: none; }

	.hbell-trigger {
		position: relative;
		display: grid;
		place-items: center;
		width: 2.375rem;
		height: 2.375rem;
		flex: none;
		border-radius: var(--di-radius-sm);
		border: 1px solid var(--di-border-strong);
		background-color: var(--di-surface);
		color: var(--di-accent-ink);
		cursor: pointer;
		transition:
			color 160ms ease,
			border-color 160ms ease,
			background-color 160ms ease,
			box-shadow 160ms ease;
	}

	.hbell-trigger:hover,
	.hbell-trigger[aria-expanded='true'] {
		color: var(--di-accent);
		border-color: var(--di-accent);
		background-color: var(--di-accent-soft);
		box-shadow: 0 8px 18px -12px var(--di-accent-glow);
	}

	.hbell-trigger:focus-visible {
		outline: 2px solid var(--di-accent);
		outline-offset: 3px;
	}

	.hbell-dot {
		position: absolute;
		top: -0.3rem;
		right: -0.3rem;
		min-width: 1.1rem;
		height: 1.1rem;
		padding: 0 .25rem;
		display: grid;
		place-items: center;
		border-radius: 999px;
		background-image: var(--di-accent-sheen);
		color: #FFFFFF;
		font-size: .625rem;
		font-weight: 700;
		line-height: 1;
		border: 2px solid var(--di-surface);
	}

	.hbell-panel {
		position: absolute;
		top: calc(100% + .6rem);
		right: 0;
		z-index: 60;
		width: min(22rem, calc(100vw - 2rem));
		padding: .4rem;
		background-color: var(--di-surface);
		border: 1px solid var(--di-border-strong);
		border-radius: var(--di-radius);
		box-shadow: var(--di-shadow-lift);
		animation: hbell-in 160ms ease-out;
	}

	@keyframes hbell-in {
		from { opacity: 0; translate: 0 -6px; }
		to { opacity: 1; translate: 0 0; }
	}

	.hbell-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: .5rem;
		padding: .5rem .6rem .625rem;
		border-bottom: 1px solid var(--di-border);
	}

	.hbell-title {
		margin: 0;
		font-size: .75rem;
		font-weight: 700;
		letter-spacing: .12em;
		text-transform: uppercase;
		color: var(--di-accent-ink);
	}

	.hbell-count {
		padding: .1rem .45rem;
		border-radius: 999px;
		background-image: var(--di-accent-sheen);
		color: #FFFFFF;
		font-size: .625rem;
		font-weight: 700;
		letter-spacing: .02em;
	}

	.hbell-list {
		list-style: none;
		margin: 0;
		padding: .25rem 0;
		max-height: 19rem;
		overflow-y: auto;
	}

	.hbell-item {
		display: flex;
		align-items: flex-start;
		gap: .6rem;
		padding: .5rem .6rem;
		border-radius: var(--di-radius-sm);
		text-decoration: none;
		color: var(--di-text);
		transition: background-color 140ms ease;
	}

	.hbell-item:hover { background-color: var(--di-accent-soft); }

	.hbell-icon {
		display: grid;
		place-items: center;
		width: 1.85rem;
		height: 1.85rem;
		flex: none;
		border-radius: 9px;
		background-color: var(--di-accent-soft);
		border: 1px solid var(--di-accent-line);
		color: var(--di-accent-ink);
	}

	.hbell-item.unread .hbell-icon { background-image: var(--di-accent-sheen); color: #FFFFFF; border-color: transparent; }

	.hbell-body { display: grid; gap: .1rem; min-width: 0; flex: 1; }

	.hbell-item-title {
		font-size: .8125rem;
		font-weight: 650;
		color: var(--di-text);
	}

	.hbell-item-detail {
		font-size: .75rem;
		line-height: 1.5;
		color: var(--di-muted);
	}

	.hbell-when { flex: none; font-size: .625rem; color: var(--di-muted); padding-top: .1rem; }

	.hbell-empty {
		margin: 0;
		padding: 1.25rem .75rem;
		text-align: center;
		font-size: .8125rem;
		color: var(--di-muted);
	}

	.hbell-foot { padding: .25rem .25rem .15rem; border-top: 1px solid var(--di-border); margin-top: .1rem; }

	.hbell-all {
		display: block;
		padding: .5rem;
		border-radius: var(--di-radius-sm);
		text-align: center;
		font-size: .8125rem;
		font-weight: 650;
		color: var(--di-accent-ink);
		text-decoration: none;
		transition: background-color 140ms ease, color 140ms ease;
	}

	.hbell-all:hover { background-color: var(--di-accent-soft); color: var(--di-accent); }

	@media (prefers-reduced-motion: reduce) {
		.hbell-panel { animation: none; }
	}
</style>
