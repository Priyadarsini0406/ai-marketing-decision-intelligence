<script lang="ts">
	import OutlineIcon from './OutlineIcon.svelte';
	import ThemeToggle from '$lib/ThemeToggle.svelte';
	import HeaderBell from './HeaderBell.svelte';
	import HeaderProfile from './HeaderProfile.svelte';
	import { roleInitial, roleLabel, shellLinks, shellNotices, type ShellRole } from '$lib/dashboard-header';

	/**
	 * The one header every signed-in shell renders.
	 *
	 * Student, manager and admin all mount this with the same markup, so
	 * title, theme toggle, notification bell and the S / M / A account menu
	 * sit in the same place and behave identically in all three. The role
	 * only changes the letter, the label and where the menu links point.
	 *
	 * There is deliberately no profile block pinned to the bottom of the
	 * sidebar: the account lives in the top-right header only.
	 */
	let {
		role,
		title,
		name,
		email,
		onlogout,
		onopennav
	}: {
		role: ShellRole;
		title: string;
		name: string;
		email: string;
		onlogout: () => void;
		onopennav: () => void;
	} = $props();

	const links = $derived(shellLinks(role));
	const notices = $derived(shellNotices(role));
</script>

<header class="di-header">
	<div class="di-header-lead">
		<button type="button" class="di-header-burger" aria-label="Open navigation" onclick={onopennav}>
			<OutlineIcon name="menu" size={20} />
		</button>
		<div class="di-header-titles">
			<h2 class="di-header-title">{title}</h2>
			<p class="di-header-crumb">Decision-Intel / {title}</p>
		</div>
	</div>

	<div class="di-header-actions">
		<ThemeToggle />
		<HeaderBell items={notices} allHref={links.notifications} allLabel="View all notifications" />
		<HeaderProfile
			initial={roleInitial(role)}
			{name}
			{email}
			roleLabel={roleLabel(role)}
			{links}
			{onlogout}
		/>
	</div>
</header>

<style>
	.di-header {
		position: relative;
		z-index: 40;
		height: 5rem;
		flex: none;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding-inline: 1rem;
		border-bottom: 1px solid var(--di-border);
		background-color: var(--di-navbar-bg);
		backdrop-filter: blur(14px) saturate(1.3);
		-webkit-backdrop-filter: blur(14px) saturate(1.3);
	}

	@media (min-width: 48rem) {
		.di-header { padding-inline: 2rem; }
	}

	.di-header-lead {
		display: flex;
		align-items: center;
		gap: .75rem;
		min-width: 0;
	}

	.di-header-titles { min-width: 0; }

	.di-header-title {
		margin: 0;
		font-size: 1.125rem;
		font-weight: 700;
		letter-spacing: -.01em;
		color: var(--di-text);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.di-header-crumb {
		display: none;
		margin: .125rem 0 0;
		font-size: .75rem;
		color: var(--di-muted);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	@media (min-width: 30rem) {
		.di-header-crumb { display: block; }
	}

	.di-header-burger {
		display: inline-grid;
		place-items: center;
		width: 2.375rem;
		height: 2.375rem;
		flex: none;
		border-radius: var(--di-radius-sm);
		border: 1px solid var(--di-border-strong);
		background-color: var(--di-surface);
		color: var(--di-accent-ink);
		cursor: pointer;
		transition: color 160ms ease, border-color 160ms ease, background-color 160ms ease;
	}

	.di-header-burger:hover {
		color: var(--di-accent);
		border-color: var(--di-accent);
		background-color: var(--di-accent-soft);
	}

	.di-header-burger:focus-visible {
		outline: 2px solid var(--di-accent);
		outline-offset: 3px;
	}

	@media (min-width: 48rem) {
		.di-header-burger { display: none; }
	}

	.di-header-actions {
		display: flex;
		align-items: center;
		gap: .625rem;
		flex: none;
	}
</style>
