<script lang="ts">
    import { tick } from 'svelte';
    import { page } from '$app/state';
    import OutlineIcon from '$lib/components/OutlineIcon.svelte';
    import {
        clearHistory, leadFromPath, loadHistory, loadWelcome, sendMessage, toBlocks,
        type AssistantMessage, type AssistantWelcome
    } from '$lib/assistant';

    let { userName = '' }: { userName?: string } = $props();

    const MAX_LENGTH = 1000;
    let open = $state(false);
    let loaded = $state(false);
    let loading = $state(false);
    let sending = $state(false);
    let error = $state('');
    let draft = $state('');
    let welcome = $state<AssistantWelcome | null>(null);
    let messages = $state<AssistantMessage[]>([]);
    let lastFailed = $state<string | null>(null);
    let confirmClear = $state(false);
    let lastLead = $state<string | undefined>(undefined);

    let scroller: HTMLDivElement | undefined = $state();
    let input: HTMLTextAreaElement | undefined = $state();
    let launcher: HTMLButtonElement | undefined = $state();

    const pageLead = $derived(leadFromPath(page.url.pathname));
    const activeLead = $derived(pageLead ?? lastLead);
    const lastAssistant = $derived([...messages].reverse().find(m => m.role === 'assistant'));
    const LEAD_QUESTIONS = ['Why did this lead get its score?', 'Suggest follow-up actions for this lead'];
    const isManager = $derived(welcome?.role === 'admission_manager' || welcome?.role === 'marketing_manager');
    const suggestions = $derived.by(() => {
        if (sending) return [];
        const base = lastAssistant?.suggestions?.length ? lastAssistant.suggestions : (welcome?.suggestions ?? []);
        // On a lead's page, managers always get the lead questions first, unless
        // the latest answer was already about this lead.
        const lead = isManager && pageLead && lastAssistant?.card?.lead_id !== pageLead ? LEAD_QUESTIONS : [];
        return [...new Set([...lead, ...base])].slice(0, 4);
    });

    async function ensureLoaded() {
        if (loaded || loading) return;
        loading = true;
        error = '';
        try {
            const [w, history] = await Promise.all([loadWelcome(pageLead), loadHistory()]);
            welcome = w;
            messages = history;
            lastLead = [...history].reverse().find(m => m.card)?.card?.lead_id;
            loaded = true;
        } catch (e) {
            error = (e as Error).message;
        } finally {
            loading = false;
            await scrollToEnd();
        }
    }

    async function toggle() {
        open = !open;
        if (open) {
            await ensureLoaded();
            await tick();
            input?.focus();
        } else {
            launcher?.focus();
        }
    }

    async function close() {
        open = false;
        confirmClear = false;
        await tick();
        launcher?.focus();
    }

    async function scrollToEnd() {
        await tick();
        scroller?.scrollTo({ top: scroller.scrollHeight, behavior: 'smooth' });
    }

    async function send(text: string) {
        const message = text.trim().slice(0, MAX_LENGTH);
        if (!message || sending) return;
        error = '';
        lastFailed = null;
        sending = true;
        const optimistic: AssistantMessage = { id: `local-${Date.now()}`, role: 'user', text: message, created_at: Date.now() / 1000 };
        messages = [...messages, optimistic];
        draft = '';
        resize();
        await scrollToEnd();
        try {
            const reply = await sendMessage(message, { path: page.url.pathname, ...(activeLead ? { lead_id: activeLead } : {}) });
            messages = [...messages, reply];
            if (reply.card?.lead_id) lastLead = reply.card.lead_id;
        } catch (e) {
            messages = messages.filter(m => m.id !== optimistic.id);
            error = (e as Error).message;
            lastFailed = message;
        } finally {
            sending = false;
            await scrollToEnd();
            input?.focus();
        }
    }

    async function clearAll() {
        try {
            await clearHistory();
            messages = [];
            lastLead = undefined;
            confirmClear = false;
        } catch (e) {
            error = (e as Error).message;
        }
    }

    function onKeydown(event: KeyboardEvent) {
        if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
            event.preventDefault();
            send(draft);
        }
    }

    function resize() {
        if (!input) return;
        input.style.height = 'auto';
        input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
    }

    const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
    const time = (seconds: number) => new Date(seconds * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const bandClass = (band: string) => band === 'High' ? 'band-high' : band === 'Medium' ? 'band-medium' : 'band-low';
</script>

<svelte:window onkeydown={event => { if (open && event.key === 'Escape') close(); }} />

{#if open}
    <div class="assistant-panel" role="dialog" aria-modal="false" aria-labelledby="assistant-title">
        <header class="assistant-head">
            <span class="assistant-avatar" aria-hidden="true"><OutlineIcon name="sparkle" size={18} strokeWidth={1.8} /></span>
            <div class="assistant-heading">
                <h2 id="assistant-title">Admission Assistant</h2>
                <p>{welcome?.llm_enabled ? 'AI-written answers from Decision-Intel data' : 'Answers from Decision-Intel data'}</p>
            </div>
            {#if messages.length}
                {#if confirmClear}
                    <button type="button" class="head-text-button danger" onclick={clearAll}>Clear chat</button>
                    <button type="button" class="head-text-button" onclick={() => (confirmClear = false)}>Keep</button>
                {:else}
                    <button type="button" class="head-text-button" onclick={() => (confirmClear = true)}>Clear</button>
                {/if}
            {/if}
            <button type="button" class="icon-button" aria-label="Close assistant" onclick={close}>
                <OutlineIcon name="close" size={18} />
            </button>
        </header>

        <div class="assistant-body" bind:this={scroller} aria-live="polite" aria-busy={sending || loading}>
            {#if loading && !loaded}
                <p class="assistant-status">Loading your conversation…</p>
            {/if}

            {#if welcome}
                <article class="msg msg-assistant">
                    <p>{welcome.text}</p>
                    {#if pageLead}<p class="msg-hint">You're viewing a lead. Ask “Why did this lead get its score?”</p>{/if}
                </article>
            {/if}

            {#each messages as message (message.id)}
                {#if message.role === 'user'}
                    <article class="msg msg-user"><p>{message.text}</p><time>{time(message.created_at)}</time></article>
                {:else}
                    <article class="msg msg-assistant">
                        {#if message.card}
                            {@const card = message.card}
                            <div class="lead-card">
                                <div class="lead-card-top">
                                    <div class="lead-card-id">
                                        <span class="label">Lead</span>
                                        <span class="value" title={card.display_id}>{card.name ?? card.display_id}</span>
                                    </div>
                                    <span class="band {bandClass(card.band)}">{card.band}</span>
                                </div>
                                <div class="prob">
                                    <div class="prob-row"><span>Conversion probability</span><strong>{percent(card.probability)}</strong></div>
                                    <div class="prob-track" role="img" aria-label="Conversion probability {percent(card.probability)}">
                                        <span style="width: {Math.max(2, card.probability * 100)}%"></span>
                                    </div>
                                </div>
                                {#if card.segment}<p class="lead-card-meta">Segment: {card.segment}</p>{/if}
                                {#if message.kind !== 'lead_followup' && (card.positive.length || card.negative.length)}
                                    <ul class="factors" aria-label="Top SHAP factors">
                                        {#each card.positive as factor}
                                            <li class="up"><span class="arrow" aria-hidden="true">▲</span><span class="factor-text">{factor.text}</span><span class="impact">+{factor.impact.toFixed(2)}</span></li>
                                        {/each}
                                        {#each card.negative as factor}
                                            <li class="down"><span class="arrow" aria-hidden="true">▼</span><span class="factor-text">{factor.text}</span><span class="impact">{factor.impact.toFixed(2)}</span></li>
                                        {/each}
                                    </ul>
                                {/if}
                                <p class="lead-card-source">{card.source === 'stored' ? 'Stored prediction' : 'Live prediction'} · SHAP values in log-odds</p>
                            </div>
                        {/if}
                        {#each toBlocks(message.text) as block}
                            {#if block.type === 'p'}<p>{block.text}</p>
                            {:else}<ul>{#each block.items as item}<li>{item}</li>{/each}</ul>{/if}
                        {/each}
                        {#if message.notice}<p class="notice"><OutlineIcon name="alert" size={14} />{message.notice}</p>{/if}
                        {#if message.links?.length}
                            <div class="links">
                                {#each message.links as link}<a href={link.href} onclick={() => { if (window.innerWidth < 640) close(); }}>{link.label}<OutlineIcon name="arrow-right" size={13} /></a>{/each}
                            </div>
                        {/if}
                        <time>{time(message.created_at)}{message.engine === 'llm' ? ' · AI-written' : ''}</time>
                    </article>
                {/if}
            {/each}

            {#if sending}
                <div class="msg msg-assistant typing" aria-label="Assistant is typing"><span></span><span></span><span></span></div>
            {/if}

            {#if error}
                <div class="assistant-error" role="alert">
                    <p>{error}</p>
                    {#if lastFailed}<button type="button" onclick={() => send(lastFailed ?? '')}>Try again</button>{/if}
                    {#if !loaded}<button type="button" onclick={ensureLoaded}>Retry</button>{/if}
                </div>
            {/if}
        </div>

        {#if suggestions.length && loaded}
            <div class="suggestions" aria-label="Suggested questions">
                {#each suggestions as suggestion}
                    <button type="button" onclick={() => send(suggestion)}>{suggestion}</button>
                {/each}
            </div>
        {/if}

        <form class="composer" onsubmit={event => { event.preventDefault(); send(draft); }}>
            <label class="sr-only" for="assistant-input">Message the Admission Assistant</label>
            <textarea id="assistant-input" bind:this={input} bind:value={draft} rows="1" maxlength={MAX_LENGTH}
                placeholder={activeLead ? 'Ask about this lead or Decision-Intel…' : 'Ask a question…'}
                oninput={resize} onkeydown={onKeydown} disabled={!loaded}></textarea>
            <button type="submit" class="send" aria-label="Send message" disabled={!draft.trim() || sending || !loaded}>
                <OutlineIcon name="arrow-right" size={18} strokeWidth={2} />
            </button>
        </form>
        <p class="composer-foot">
            {#if draft.length > MAX_LENGTH - 200}<span>{draft.length}/{MAX_LENGTH}</span>{/if}
            Lead scores are marketing estimates, not admission decisions.
        </p>
    </div>
{/if}

<button type="button" class="assistant-launcher" class:is-open={open} bind:this={launcher} onclick={toggle}
    aria-expanded={open} aria-label={open ? 'Close Admission Assistant' : `Open Admission Assistant${userName ? ` for ${userName}` : ''}`}>
    <OutlineIcon name={open ? 'close' : 'sparkle'} size={24} strokeWidth={1.8} />
</button>

<style>
    .assistant-launcher {
        position: fixed;
        right: calc(20px + env(safe-area-inset-right, 0px));
        bottom: calc(20px + env(safe-area-inset-bottom, 0px));
        z-index: 70;
        width: 56px; height: 56px;
        display: grid; place-items: center;
        border: 0; border-radius: 50%;
        color: var(--di-on-accent);
        background: var(--di-accent-sheen);
        box-shadow: var(--di-shadow-lift), 0 0 0 4px var(--di-accent-glow);
        cursor: pointer;
        transition: transform .18s ease, box-shadow .18s ease;
    }
    .assistant-launcher:hover { transform: translateY(-2px); }
    .assistant-launcher:focus-visible { outline: 3px solid var(--di-accent-ink); outline-offset: 3px; }

    .assistant-panel {
        position: fixed;
        right: calc(20px + env(safe-area-inset-right, 0px));
        bottom: calc(88px + env(safe-area-inset-bottom, 0px));
        z-index: 69;
        width: min(400px, calc(100vw - 32px));
        height: min(640px, calc(100dvh - 120px));
        display: flex; flex-direction: column;
        background: var(--di-surface);
        color: var(--di-text);
        border: 1px solid var(--di-border-strong);
        border-radius: var(--di-radius-lg);
        box-shadow: var(--di-shadow-lift);
        overflow: hidden;
        animation: rise .18s ease-out;
    }
    @keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

    .assistant-head {
        display: flex; align-items: center; gap: 10px;
        padding: 14px 14px 12px 16px;
        border-bottom: 1px solid var(--di-border);
        background: var(--di-surface-muted);
    }
    .assistant-avatar {
        flex: 0 0 34px; height: 34px; display: grid; place-items: center;
        border-radius: 50%; color: var(--di-on-accent); background: var(--di-accent-sheen);
    }
    .assistant-heading { flex: 1; min-width: 0; }
    .assistant-heading h2 { margin: 0; font-size: .95rem; font-weight: 700; color: var(--di-text); }
    .assistant-heading p { margin: 1px 0 0; font-size: .72rem; color: var(--di-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .icon-button, .head-text-button {
        border: 1px solid transparent; background: transparent; color: var(--di-muted);
        border-radius: 10px; cursor: pointer;
    }
    .icon-button { width: 34px; height: 34px; display: grid; place-items: center; }
    .head-text-button { padding: 6px 9px; font-size: .75rem; font-weight: 600; }
    .head-text-button.danger { color: var(--di-red-ink); background: var(--di-red-soft); }
    .icon-button:hover, .head-text-button:hover { color: var(--di-text); border-color: var(--di-border); }
    .icon-button:focus-visible, .head-text-button:focus-visible { outline: 2px solid var(--di-accent-ink); outline-offset: 1px; }

    .assistant-body {
        flex: 1; min-height: 0; overflow-y: auto;
        padding: 16px; display: flex; flex-direction: column; gap: 12px;
        overscroll-behavior: contain;
    }
    .assistant-status { margin: 0; font-size: .8rem; color: var(--di-muted); text-align: center; }

    .msg { max-width: 88%; display: flex; flex-direction: column; gap: 6px; font-size: .86rem; line-height: 1.5; }
    .msg p, .msg ul { margin: 0; }
    .msg ul { padding-left: 18px; display: flex; flex-direction: column; gap: 4px; }
    .msg time { font-size: .68rem; color: var(--di-muted); }
    .msg-user { align-self: flex-end; align-items: flex-end; }
    .msg-user p {
        padding: 9px 13px; border-radius: 16px 16px 4px 16px;
        background: var(--di-accent-fill); color: var(--di-on-accent);
        white-space: pre-wrap; overflow-wrap: anywhere;
    }
    .msg-assistant {
        align-self: flex-start; padding: 11px 13px;
        border-radius: 16px 16px 16px 4px;
        background: var(--di-surface-muted); border: 1px solid var(--di-border);
        overflow-wrap: anywhere;
    }
    .msg-hint { font-size: .78rem; color: var(--di-accent-ink); }

    .lead-card {
        display: flex; flex-direction: column; gap: 9px;
        padding: 11px; border-radius: var(--di-radius-sm);
        background: var(--di-surface); border: 1px solid var(--di-border);
    }
    .lead-card-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
    .lead-card-id { display: flex; flex-direction: column; min-width: 0; }
    .lead-card-id .label { font-size: .64rem; letter-spacing: .06em; text-transform: uppercase; color: var(--di-muted); }
    .lead-card-id .value { font-size: .78rem; font-weight: 600; font-family: ui-monospace, Consolas, monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .band { flex: none; padding: 3px 9px; border-radius: 999px; font-size: .7rem; font-weight: 700; }
    .band-high { color: var(--di-green-ink); background: var(--di-green-soft); }
    .band-medium { color: var(--di-gold-ink); background: var(--di-gold-soft); }
    .band-low { color: var(--di-muted); background: var(--di-surface-muted); border: 1px solid var(--di-border); }
    .prob-row { display: flex; justify-content: space-between; font-size: .76rem; color: var(--di-muted); margin-bottom: 5px; }
    .prob-row strong { color: var(--di-text); font-variant-numeric: tabular-nums; }
    .prob-track { height: 7px; border-radius: 999px; background: var(--di-surface-muted); border: 1px solid var(--di-border); overflow: hidden; }
    .prob-track span { display: block; height: 100%; border-radius: inherit; background: var(--di-accent-sheen); }
    .lead-card-meta, .lead-card-source { font-size: .72rem; color: var(--di-muted); }
    .factors { list-style: none; padding: 0 !important; gap: 5px !important; }
    .factors li { display: grid; grid-template-columns: 14px 1fr auto; gap: 7px; align-items: baseline; font-size: .76rem; }
    .factors .arrow { font-size: .62rem; }
    .factors .up .arrow, .factors .up .impact { color: var(--di-green-ink); }
    .factors .down .arrow, .factors .down .impact { color: var(--di-red-ink); }
    .factors .impact { font-variant-numeric: tabular-nums; font-weight: 600; }
    .factor-text { min-width: 0; }

    .notice {
        display: flex; gap: 6px; align-items: flex-start;
        font-size: .74rem !important; color: var(--di-muted);
        padding: 7px 9px; border-radius: 10px; background: var(--di-surface); border: 1px dashed var(--di-border-strong);
    }
    .links { display: flex; flex-wrap: wrap; gap: 6px; }
    .links a {
        display: inline-flex; align-items: center; gap: 4px;
        padding: 4px 9px; border-radius: 999px; font-size: .74rem; font-weight: 600;
        color: var(--di-accent-ink); background: var(--di-accent-soft); text-decoration: none;
    }
    .links a:hover { text-decoration: underline; }
    .links a:focus-visible { outline: 2px solid var(--di-accent-ink); outline-offset: 1px; }

    .typing { flex-direction: row; gap: 5px; padding: 13px 15px; }
    .typing span { width: 7px; height: 7px; border-radius: 50%; background: var(--di-muted); animation: blink 1.2s infinite ease-in-out; }
    .typing span:nth-child(2) { animation-delay: .15s; }
    .typing span:nth-child(3) { animation-delay: .3s; }
    @keyframes blink { 0%, 80%, 100% { opacity: .25; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-3px); } }

    .assistant-error {
        display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
        padding: 9px 11px; border-radius: 12px; font-size: .8rem;
        color: var(--di-red-ink); background: var(--di-red-soft);
    }
    .assistant-error p { margin: 0; flex: 1 1 160px; }
    .assistant-error button { border: 1px solid currentColor; background: transparent; color: inherit; border-radius: 8px; padding: 3px 9px; cursor: pointer; font-weight: 600; }

    .suggestions {
        display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 14px 2px;
    }
    .suggestions button {
        max-width: 100%; padding: 6px 11px; border-radius: 999px; cursor: pointer; text-align: left;
        font-size: .76rem; color: var(--di-accent-ink);
        background: var(--di-surface); border: 1px solid var(--di-accent-line);
    }
    .suggestions button:hover { background: var(--di-accent-soft); }
    .suggestions button:focus-visible { outline: 2px solid var(--di-accent-ink); outline-offset: 1px; }

    .composer { display: flex; align-items: flex-end; gap: 8px; padding: 10px 14px 4px; }
    .composer textarea {
        flex: 1; resize: none; min-height: 40px; max-height: 120px;
        padding: 9px 12px; border-radius: 12px; font: inherit; font-size: .86rem;
        color: var(--di-text); background: var(--di-surface-muted); border: 1px solid var(--di-border);
    }
    .composer textarea::placeholder { color: var(--di-muted); }
    .composer textarea:focus { outline: 2px solid var(--di-accent-ink); outline-offset: 0; border-color: transparent; }
    .send {
        flex: none; width: 40px; height: 40px; display: grid; place-items: center;
        border: 0; border-radius: 12px; cursor: pointer;
        color: var(--di-on-accent); background: var(--di-accent-fill);
    }
    .send:disabled { opacity: .45; cursor: not-allowed; }
    .send:focus-visible { outline: 2px solid var(--di-accent-ink); outline-offset: 2px; }
    .composer-foot { margin: 0; padding: 2px 16px 12px; font-size: .66rem; color: var(--di-muted); display: flex; gap: 8px; }
    .composer-foot span { font-variant-numeric: tabular-nums; color: var(--di-text); }
    .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

    @media (max-width: 639px) {
        .assistant-panel {
            right: 0; bottom: 0; left: 0; top: 0;
            width: 100%; height: 100dvh; border-radius: 0; border: 0;
            padding: env(safe-area-inset-top, 0px) env(safe-area-inset-right, 0px) env(safe-area-inset-bottom, 0px) env(safe-area-inset-left, 0px);
        }
        .assistant-launcher.is-open { display: none; }
        .msg { max-width: 94%; }
    }
    @media (prefers-reduced-motion: reduce) {
        .assistant-panel, .typing span { animation: none; }
        .assistant-launcher { transition: none; }
    }
</style>
