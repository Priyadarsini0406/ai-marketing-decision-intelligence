<script lang="ts">
    let { rows, empty = 'No stored records available.' }: { rows: Record<string, unknown>[]; empty?: string } = $props();
    function display(value: unknown) { return value == null ? '—' : typeof value === 'object' ? JSON.stringify(value) : String(value); }
</script>
{#if rows.length}<div class="overflow-auto rounded-xl border border-white/10"><table class="w-full text-left text-sm"><thead><tr>{#each Object.keys(rows[0]) as key}<th class="p-3 whitespace-nowrap bg-white/5">{key.replaceAll('_', ' ')}</th>{/each}</tr></thead><tbody>{#each rows as row}<tr>{#each Object.values(row) as value}<td class="p-3 border-t border-white/10 whitespace-nowrap">{display(value)}</td>{/each}</tr>{/each}</tbody></table></div>{:else}<p class="p-6 rounded-xl bg-white/5 text-text-secondary">{empty}</p>{/if}
