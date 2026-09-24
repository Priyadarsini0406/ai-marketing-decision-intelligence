<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { api } from '$lib/api';
    import type { ECharts, EChartsOption } from 'echarts';

    type MetricModel = { name: string; accuracy: number; precision: number; recall: number; f1: number; roc_auc: number };
    type ModelPerformance = { available: boolean; selected_model: string | null; evaluated_at: string | null; target_column?: string | null; random_state?: number | null; thresholds?: { priority_high?: number; priority_medium?: number; decision?: number } | null; models: MetricModel[]; source?: { evaluation?: string | null; metadata?: string | null } | null };

    let data = $state<ModelPerformance | null>(null);
    let error = $state('');
    let busy = $state(false);
    let selected = $state('');

    const pct = (value?: number | null) => value == null ? '—' : `${(value * 100).toFixed(2)}%`;
    const selectedRow = $derived(
        data?.models.find((m) => m.name === selected) ??
        data?.models.find((m) => m.name === data?.selected_model) ??
        data?.models[0]
    );
    const evaluatedLabel = $derived(data?.evaluated_at ? new Date(data.evaluated_at).toLocaleString() : null);

    async function load() {
        busy = true;
        error = '';
        try {
            const result = await api('/admin/ml/model-performance');
            data = result;
            const availableModels = result?.models ?? [];
            if (result?.selected_model && !availableModels.some((m: MetricModel) => m.name === selected)) {
                selected = result.selected_model;
            }
        } catch (e) {
            error = (e as Error).message || 'Model performance data is currently unavailable.';
        } finally {
            busy = false;
        }
    }

    const onVisibility = () => { if (document.visibilityState === 'visible') load(); };

    let element = $state<HTMLDivElement>();
    let chart: ECharts | undefined;
    let resizeObserver: ResizeObserver | undefined;

    function buildOption(): EChartsOption {
        const models = data?.models ?? [];
        const palette = ['#A47BE0', '#F2A62B', '#71C9B0'];
        const series = [
            { name: 'Accuracy', values: models.map((m) => m.accuracy * 100) },
            { name: 'F1 Score', values: models.map((m) => m.f1 * 100) },
            { name: 'ROC-AUC', values: models.map((m) => m.roc_auc * 100) },
        ];
        return {
            color: palette,
            backgroundColor: 'transparent',
            animation: false,
            textStyle: { color: '#C9C5CE', fontFamily: 'Inter, sans-serif' },
            aria: { enabled: true },
            tooltip: { trigger: 'axis', confine: true, backgroundColor: '#191320', borderColor: '#68517E', textStyle: { color: '#FFFFFF' }, valueFormatter: (value) => `${Number(value).toFixed(2)}%` },
            legend: { type: 'scroll', bottom: 0, textStyle: { color: '#C9C5CE' } },
            grid: { left: 12, right: 20, top: 30, bottom: 70, containLabel: true },
            xAxis: { type: 'category', data: models.map((m) => m.name), axisLine: { lineStyle: { color: '#FFFFFF20' } }, axisTick: { show: false }, axisLabel: { color: '#C9BED6', fontSize: 11, interval: 0, rotate: models.length > 4 ? 20 : 0 } },
            yAxis: { type: 'value', max: 100, axisLabel: { color: '#BDB2CD', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#FFFFFF0D', type: 'dashed' } } },
            series: series.map((item, index) => ({
                name: item.name,
                type: 'bar',
                data: item.values.map((value) => Math.round(value * 100) / 100),
                barMaxWidth: 42,
                itemStyle: { borderRadius: [5, 5, 0, 0] },
                emphasis: { focus: 'series', itemStyle: { shadowBlur: 12, shadowColor: palette[index] + '60' } },
            })),
        };
    }

    async function updateChart() {
        if (!element || !data?.available) return;
        try {
            const echarts = await import('echarts');
            if (!chart) chart = echarts.init(element, undefined, { renderer: 'svg' });
            chart.setOption(buildOption(), { notMerge: true });
            chart.resize();
        } catch {
            // Chart is optional; the table below always shows the values.
        }
    }

    $effect(() => {
        if (data) updateChart();
    });

    onMount(() => {
        load();
        document.addEventListener('visibilitychange', onVisibility);
        if (element) {
            resizeObserver = new ResizeObserver(() => chart?.resize());
            resizeObserver.observe(element);
        }
    });

    onDestroy(() => {
        document.removeEventListener('visibilitychange', onVisibility);
        resizeObserver?.disconnect();
        chart?.dispose();
        chart = undefined;
    });
</script>

<svelte:head><title>Model Performance | DecisionIntel</title></svelte:head>

<div class="mp-page">
    <header class="mp-head">
        <div>
            <h1>Model Performance</h1>
            <p>Monitor and compare the performance of Decision-Intel's lead conversion models.</p>
        </div>
        <div class="mp-actions">
            {#if data?.available}<span class="mp-status"><i class="dot"></i>Model evaluation available</span>{/if}
            <button onclick={load} disabled={busy}>{busy ? 'Refreshing…' : 'Refresh'}</button>
        </div>
    </header>

    {#if error}
        <section class="mp-state" role="alert">
            <h2>Model performance data is currently unavailable.</h2>
            <p>{error}</p>
            <button onclick={load} disabled={busy}>Retry</button>
        </section>
    {:else if !data}
        <div aria-busy="true" aria-label="Loading model performance">
            <div class="grid mp-cards">{#each [1, 2, 3, 4] as _}<div class="skeleton card-skeleton"></div>{/each}</div>
            <div class="skeleton table-skeleton"></div>
            <div class="skeleton chart-skeleton"></div>
        </div>
    {:else if !data.available}
        <section class="mp-state">
            <h2>No model evaluation data available yet.</h2>
            <p>Train the lead conversion model to generate evaluation metrics.</p>
            <button onclick={load} disabled={busy}>Refresh</button>
        </section>
    {:else}
        <section class="grid mp-cards">
            <div class="stat-card">
                <p class="stat-label">Selected Model</p>
                <strong class="stat-value stat-model">{selectedRow?.name ?? '—'}</strong>
                {#if selectedRow?.name === data?.selected_model}<span class="badge">Selected Model</span>{/if}
            </div>
            <div class="stat-card"><p class="stat-label">Accuracy</p><strong class="stat-value">{pct(selectedRow?.accuracy)}</strong></div>
            <div class="stat-card"><p class="stat-label">F1 Score</p><strong class="stat-value">{pct(selectedRow?.f1)}</strong></div>
            <div class="stat-card"><p class="stat-label">ROC-AUC</p><strong class="stat-value">{pct(selectedRow?.roc_auc)}</strong></div>
        </section>

        <section class="panel">
            <div class="panel-title"><h2>Model comparison</h2><p>All models evaluated on the same held-out test set.</p></div>
            <div class="mp-table-wrap">
                <table class="mp-table">
                    <thead>
                        <tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1 Score</th><th>ROC-AUC</th><th>Status</th></tr>
                    </thead>
                    <tbody>
                        {#each data.models as model}
                            <tr class:selected-row={model.name === selectedRow?.name} tabindex="0" onclick={() => selected = model.name}
                                onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selected = model.name; } }}
                                aria-label={`Select ${model.name} for details`}>
                                <td class="model-cell">{model.name}</td>
                                <td>{pct(model.accuracy)}</td>
                                <td>{pct(model.precision)}</td>
                                <td>{pct(model.recall)}</td>
                                <td>{pct(model.f1)}</td>
                                <td>{pct(model.roc_auc)}</td>
                                <td>{#if model.name === data?.selected_model}<span class="badge">Selected Model</span>{:else}—{/if}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </section>

        <section class="panel">
            <div class="panel-title"><h2>Model comparison chart</h2><p>Values are percentages from the API response.</p></div>
            <div bind:this={element} class="mp-chart" style:height="340px" role="img" aria-label="Grouped bar chart comparing model accuracy, F1 score, and ROC-AUC"></div>
        </section>

        {#if selectedRow}
            <section class="panel">
                <div class="panel-title"><h2>Model details</h2></div>
                <div class="details-name">{selectedRow.name}{#if selectedRow.name === data?.selected_model}<span class="badge">Selected Model</span>{/if}</div>
                <div class="grid details-grid">
                    <div><p class="stat-label">Accuracy</p><strong class="detail-value">{pct(selectedRow.accuracy)}</strong></div>
                    <div><p class="stat-label">Precision</p><strong class="detail-value">{pct(selectedRow.precision)}</strong></div>
                    <div><p class="stat-label">Recall</p><strong class="detail-value">{pct(selectedRow.recall)}</strong></div>
                    <div><p class="stat-label">F1 Score</p><strong class="detail-value">{pct(selectedRow.f1)}</strong></div>
                    <div><p class="stat-label">ROC-AUC</p><strong class="detail-value">{pct(selectedRow.roc_auc)}</strong></div>
                    <div><p class="stat-label">Status</p><strong class="detail-value">{selectedRow.name === data?.selected_model ? 'Selected' : 'Candidate'}</strong></div>
                </div>
                {#if evaluatedLabel}
                    <p class="details-meta">Last evaluation: {evaluatedLabel}</p>
                {/if}
            </section>
        {/if}

        <p class="mp-source">Metrics read from the training pipeline output ({data.source?.evaluation ?? 'evaluation report'} and {data.source?.metadata ?? 'model metadata'}). Re-run training to update these values.</p>
    {/if}
</div>

<style>
    .mp-page { min-width: 0; }
    .mp-page h1 { font-size: 30px; font-weight: 700; margin-bottom: 8px; }
    .mp-page h2 { font-size: 19px; font-weight: 600; margin-bottom: 12px; }
    .mp-page p { color: #b6aec4; margin: 0; }

    .mp-head { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 18px; }
    .mp-head p { margin-top: 8px; max-width: 560px; }
    .mp-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 14px; }
    .mp-status { display: inline-flex; align-items: center; gap: 8px; font-size: 12px; color: #9ddeB0; border: 1px solid #71C9B033; background: #71C9B00d; border-radius: 999px; padding: 6px 12px; white-space: nowrap; }
    .mp-status .dot { width: 8px; height: 8px; border-radius: 50%; background: #71c9b0; box-shadow: 0 0 8px #71c9b080; }
    .mp-page button { background: #f2a62b; color: #171020; border-radius: 9px; padding: 10px 18px; font-weight: 600; cursor: pointer; }
    .mp-page button:disabled { opacity: .5; cursor: wait; }
    .mp-page button:focus-visible { outline: 2px solid #c7a4f0; outline-offset: 4px; }

    .mp-cards { grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr)); gap: 18px; margin: 24px 0; }
    .stat-card { background: #191420; border: 1px solid #ffffff12; border-radius: 14px; padding: 22px; min-width: 0; }
    .stat-label { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: #9b93ab; margin: 0 0 10px; }
    .stat-value { display: block; font-size: clamp(20px, 3vw, 30px); font-weight: 700; color: #f3edf9; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; overflow-wrap: anywhere; }
    .stat-model { font-size: clamp(17px, 2.4vw, 24px); margin-bottom: 6px; }

    .badge { display: inline-block; font-size: 11px; font-weight: 600; color: #e4c9ff; background: #38274e; border: 1px solid #a47be044; border-radius: 999px; padding: 3px 10px; margin-top: 8px; }

    .panel { background: #191420; border: 1px solid #ffffff12; border-radius: 14px; padding: 24px; margin: 24px 0; min-width: 0; }
    .panel-title { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; }
    .panel-title h2 { margin-bottom: 0; }
    .panel-title p { font-size: 13px; }

    .mp-table-wrap { overflow: auto; border-radius: 10px; }
    .mp-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }
    .mp-table th, .mp-table td { padding: 13px 14px; border-bottom: 1px solid #ffffff12; white-space: nowrap; font-variant-numeric: tabular-nums; }
    .mp-table th { background: #241b30; color: #cfc6dd; font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }
    .mp-table td { color: #d6cee2; }
    .mp-table tbody tr { cursor: pointer; transition: background-color 180ms ease; }
    .mp-table tbody tr:hover { background: #a47be012; }
    .mp-table tbody tr.selected-row { background: #38274e33; box-shadow: inset 3px 0 0 #a47be0; }
    .mp-table tbody tr:focus-visible { outline: 2px solid #c7a4f0; outline-offset: -2px; }
    .mp-table .model-cell { font-weight: 600; color: #f3edf9; }
    .mp-table .badge { margin-top: 0; }

    .mp-chart { width: 100%; min-width: 0; }

    .details-name { display: flex; align-items: center; gap: 12px; font-size: 20px; font-weight: 700; color: #f3edf9; margin-bottom: 16px; }
    .details-grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr)); gap: 14px; }
    .details-grid > div { background: #100c18; border: 1px solid #ffffff0f; border-radius: 10px; padding: 14px; }
    .details-grid .stat-label { margin-bottom: 6px; }
    .detail-value { font-size: 20px; font-weight: 700; color: #f3edf9; font-variant-numeric: tabular-nums; }
    .details-meta { font-size: 12px; color: #9b93ab; margin-top: 16px; }

    .mp-source { font-size: 12px; color: #9b93ab; margin-top: 4px; }

    .mp-state { background: #191420; border: 1px solid #ffffff12; border-radius: 14px; padding: 40px 24px; text-align: center; margin: 24px 0; }
    .mp-state h2 { margin-bottom: 8px; }
    .mp-state p { margin-bottom: 22px; }

    .skeleton { position: relative; overflow: hidden; background: #191420; border: 1px solid #ffffff0d; border-radius: 14px; }
    .skeleton::after { content: ''; position: absolute; inset: 0; transform: translateX(-100%); background: linear-gradient(90deg, transparent, #ffffff0a, transparent); animation: shimmer 1.4s infinite; }
    .card-skeleton { height: 130px; }
    .table-skeleton { height: 240px; margin: 24px 0; }
    .chart-skeleton { height: 300px; }

    @keyframes shimmer { to { transform: translateX(100%); } }

    @media (prefers-reduced-motion: reduce) {
        .skeleton::after { animation: none; }
        .mp-table tbody tr { transition: none; }
    }

    @media (max-width: 640px) {
        .mp-head { flex-direction: column; }
        .panel { padding: 18px; }
    }
</style>