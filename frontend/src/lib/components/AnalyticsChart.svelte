<script lang="ts">
    import { onMount } from 'svelte';
    import type { ECharts, EChartsOption } from 'echarts';
    type Series = { name: string; values: (number | null)[] };
    let { title, categories, series, kind = 'bar', unit = '', description = '' }: {
        title: string; categories: string[]; series: Series[]; kind?: 'bar' | 'line' | 'donut' | 'funnel'; unit?: string; description?: string;
    } = $props();
    let element: HTMLDivElement;
    let ready = $state(false), error = $state(''), reduced = $state(false);
    let chart: ECharts | undefined;
    const hasData = $derived(categories.length > 0 && series.some(item => item.values.some(value => value != null && Number.isFinite(value))));
    const options = $derived.by((): EChartsOption => {
        const palette = ['#A47BE0', '#F2A62B', '#D983E8', '#71C9B0', '#7CA6E7', '#E99683'];
        const common: EChartsOption = {
            color: palette, backgroundColor: 'transparent', animation: !reduced, animationDuration: 650, animationDurationUpdate: reduced ? 0 : 350,
            textStyle: { color: '#C9C5CE', fontFamily: 'Inter, sans-serif' },
            aria: { enabled: true },
            tooltip: { trigger: kind === 'bar' || kind === 'line' ? 'axis' : 'item', confine: true, backgroundColor: '#191320', borderColor: '#68517E', textStyle: { color: '#FFFFFF' } },
            legend: { type: 'scroll', bottom: 0, textStyle: { color: '#C9C5CE' } }
        };
        if (kind === 'line') return { ...common,
            grid: { left: 15, right: 25, top: 35, bottom: 75, containLabel: true },
            xAxis: { type: 'category', data: categories, boundaryGap: categories.length === 1,
                axisLine: { lineStyle: { color: '#FFFFFF20' } }, axisTick: { show: false },
                axisLabel: { color: '#C9BED6', fontSize: 10, width: 100, overflow: 'truncate', hideOverlap: true } },
            yAxis: { type: 'value', name: unit, nameTextStyle: { color: '#BDB2CD' }, splitLine: { lineStyle: { color: '#FFFFFF0D', type: 'dashed' } }, axisLabel: { color: '#BDB2CD' } },
            series: series.map((item, index) => ({ name: item.name, type: 'line', data: item.values,
                smooth: 0.25, smoothMonotone: 'x', connectNulls: false, showSymbol: true, symbol: 'circle', symbolSize: 7,
                lineStyle: { width: 3, color: palette[index % palette.length], shadowBlur: 9, shadowColor: palette[index % palette.length] + '70' },
                itemStyle: { color: palette[index % palette.length], borderColor: '#21152F', borderWidth: 2 },
                areaStyle: { opacity: 1, color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: palette[index % palette.length] + '24' }, { offset: 1, color: palette[index % palette.length] + '00' }] } },
                emphasis: { focus: 'series', scale: 1.7, lineStyle: { width: 4 } }
            }))
        };
        if (kind === 'donut' || kind === 'funnel') return { ...common, series: [{
            name: series[0]?.name,
            ...(kind === 'donut' ? { type: 'pie' as const, radius: ['42%', '68%'], center: ['50%', '44%'] } : { type: 'funnel' as const, left: '12%', top: 10, bottom: 50, width: '76%', gap: 5, sort: 'none' as const }),
            data: categories.map((name, index) => ({ name, value: series[0]?.values[index] ?? 0 })),
            label: { show: kind === 'funnel', color: '#FFFFFF', formatter: '{b}: {c}' },
            itemStyle: { borderColor: '#171320', borderWidth: 2 },
            emphasis: { itemStyle: { shadowBlur: 18, shadowColor: '#A47BE060' }, label: { show: true, color: '#FFFFFF' } }
        }] };
        return { ...common,
            grid: { left: 12, right: 30, top: unit ? 35 : 15, bottom: 55, containLabel: true },
            xAxis: { type: 'value', name: unit, nameLocation: 'middle', nameGap: 28, splitLine: { lineStyle: { color: '#FFFFFF0D' } }, axisLabel: { color: '#BDB2CD' } },
            yAxis: { type: 'category', data: categories, inverse: true, axisTick: { show: false }, axisLine: { show: false }, axisLabel: { color: '#D1C7DD', width: 125, overflow: 'truncate', fontSize: 11 } },
            series: series.map((item, index) => ({ name: item.name, type: 'bar', data: item.values, barMaxWidth: 22,
                itemStyle: { borderRadius: [0, 5, 5, 0], color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: palette[index % palette.length] + '80' }, { offset: 1, color: palette[index % palette.length] }] } },
                emphasis: { focus: 'series', itemStyle: { shadowBlur: 12, shadowColor: palette[index % palette.length] + '60' } }
            }))
        };
    });
    onMount(() => {
        let disposed = false;
        const preference = matchMedia('(prefers-reduced-motion: reduce)');
        reduced = preference.matches;
        const change = () => reduced = preference.matches;
        preference.addEventListener('change', change);
        const resize = new ResizeObserver(() => chart?.resize());
        resize.observe(element);
        void import('echarts').then(module => {
            if (disposed) return;
            chart = module.init(element, undefined, { renderer: 'svg' }); ready = true;
        }).catch(() => error = 'Chart could not load. The values are available below.');
        return () => { disposed = true; resize.disconnect(); preference.removeEventListener('change', change); chart?.dispose(); };
    });
    $effect(() => { if (ready) chart?.setOption(options, { notMerge: true }); });
</script>

<section class="analytics-chart motion-card" aria-label={title}>
    <div class="chart-heading"><div><p class="chart-eyebrow">ANALYTICS</p><h2>{title}</h2></div><span class="chart-unit">{unit || 'Distribution'}</span></div>
    {#if description}<p class="chart-description">{description}</p>{/if}
    {#if !hasData}<p class="chart-empty">No data available for this chart.</p>{/if}
    {#if error}<p role="status">{error}</p>{/if}
    <div bind:this={element} class="chart-canvas" class:empty={!hasData} style:height={`${kind === 'bar' ? Math.max(290, Math.min(620, categories.length * (series.length > 1 ? 45 : 30) + 100)) : 330}px`} role="img" aria-label={`${title}. ${categories.length} categories. Exact values are available in View chart data.`}></div>
    <details><summary>View chart data</summary><div class="chart-table"><table><thead><tr><th>Category</th>{#each series as item}<th>{item.name}{unit ? ` (${unit})` : ''}</th>{/each}</tr></thead><tbody>{#each categories as category, index}<tr><th>{category}</th>{#each series as item}<td>{item.values[index] == null ? 'Unavailable' : item.values[index]?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>{/each}</tr>{/each}</tbody></table></div></details>
</section>
<style>
    .analytics-chart{min-width:0;padding:22px;border:1px solid #A47BE02B;border-radius:17px;background:linear-gradient(145deg,#20172B,#100E19);margin:20px 0;box-shadow:inset 0 1px 0 #FFFFFF05}.chart-heading{display:flex;justify-content:space-between;gap:12px;align-items:center}.chart-eyebrow{font-size:9px;letter-spacing:.18em;color:#A47BE0;margin:0 0 7px}h2{font-size:16px;font-weight:650;color:#F3EDF9}.chart-unit{font-size:10px;color:#F2C778;border:1px solid #F2A62B22;border-radius:6px;padding:5px 8px}.chart-description,.chart-empty{font-size:12px;color:#B3A5C1;line-height:1.6;margin-top:12px}.chart-canvas{width:100%;min-width:0;margin-top:15px}.chart-canvas.empty{display:none}summary{cursor:pointer;font-size:11px;color:#BFA0DC;padding-top:12px;border-top:1px solid #FFFFFF10}.chart-table{overflow:auto}table{width:100%;text-align:left;font-size:12px;border-collapse:collapse}th,td{padding:10px;border-bottom:1px solid #FFFFFF10;color:#C9C5CE}summary:focus-visible{outline:2px solid #A47BE0;outline-offset:4px}@media(max-width:600px){.analytics-chart{padding:14px}.chart-heading{align-items:start}h2{font-size:14px}}
</style>
