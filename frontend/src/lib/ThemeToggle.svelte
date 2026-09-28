<script lang="ts">
	import { isLight, theme, toggleTheme } from '$lib/theme.svelte';

	const label = $derived(isLight() ? 'Switch to dark theme' : 'Switch to light theme');
</script>

<button
	type="button"
	class="di-theme-toggle"
	aria-label={label}
	title={label}
	onclick={toggleTheme}
>
	{#if theme.current === 'light'}
		<!-- sun shown in light mode: click for dark -->
		<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false">
			<circle cx="12" cy="12" r="4.2" fill="currentColor" />
			<g stroke="currentColor" stroke-width="1.7" stroke-linecap="round">
				<path d="M12 2.6v2.3M12 19.1v2.3M2.6 12h2.3M19.1 12h2.3" />
				<path d="M5.4 5.4l1.6 1.6M17 17l1.6 1.6M18.6 5.4L17 7M7 17l-1.6 1.6" />
			</g>
		</svg>
	{:else}
		<!-- moon shown in dark mode: click for light -->
		<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false">
			<path
				d="M20.2 14.6A8.6 8.6 0 0 1 9.4 3.8a8.6 8.6 0 1 0 10.8 10.8Z"
				fill="currentColor"
			/>
		</svg>
	{/if}
	<span class="di-theme-toggle__label">{theme.current === 'light' ? 'Light' : 'Dark'}</span>
</button>

<style>
	.di-theme-toggle {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		min-height: 2.25rem;
		/* "Dark" and "Light" are different widths; pinning the box keeps the
		   surrounding nav from shifting when the theme is toggled. */
		min-width: 5rem;
		justify-content: center;
		padding: 0.4rem 0.7rem;
		border-radius: 999px;
		border: 1px solid var(--di-border-strong);
		background: var(--di-surface);
		color: var(--di-text);
		font-size: 0.78rem;
		font-weight: 600;
		line-height: 1;
		cursor: pointer;
		transition: border-color 180ms ease, background-color 180ms ease, color 180ms ease;
	}

	.di-theme-toggle:hover {
		border-color: var(--di-accent);
		color: var(--di-accent-ink);
	}

	.di-theme-toggle:focus-visible {
		outline: 2px solid var(--di-accent);
		outline-offset: 2px;
	}

	.di-theme-toggle__label {
		display: none;
	}

	@media (min-width: 30rem) {
		.di-theme-toggle__label {
			display: inline;
		}
	}
</style>
