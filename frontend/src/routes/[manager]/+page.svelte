<script lang="ts">
    import { page } from '$app/state';
    import PlaceholderPage from '$lib/components/PlaceholderPage.svelte';
    import ManagerAnalytics from '$lib/components/ManagerAnalytics.svelte';
    import ManagerPlanning from '$lib/components/ManagerPlanning.svelte';
    import ManagerReports from '$lib/components/ManagerReports.svelte';
    import ManagerAccount from '$lib/components/ManagerAccount.svelte';
    const planningRoutes = { 'budget-optimization': 'budget', 'what-if': 'simulator', 'ai-recommendations': 'recommendations', recommendations: 'recommendations' } as const;
    const planningView = $derived(planningRoutes[page.params.manager as keyof typeof planningRoutes]);
    const analyticsRoutes = { 'admission-funnel': 'funnel', funnel: 'funnel', 'channel-attribution': 'attribution', attribution: 'attribution', 'campaign-analytics': 'campaigns', campaigns: 'campaigns' } as const;
    const analyticsView = $derived(analyticsRoutes[page.params.manager as keyof typeof analyticsRoutes]);
    const titles: Record<string, string> = { leads: 'Student Leads', prediction: 'Admission Prediction', 'explainable-ai': 'Explainable AI', segmentation: 'Student Segmentation', funnel: 'Admission Funnel', attribution: 'Channel Attribution', campaigns: 'Campaign Analytics', 'budget-optimization': 'Budget Optimization', 'what-if': 'What-If Simulator', recommendations: 'AI Recommendations', reports: 'Reports & Analytics', notifications: 'Notifications', profile: 'Profile', settings: 'Settings' };
    let title = $derived(titles[page.params.manager ?? ''] ?? 'Decision-Intel Module');
</script>
{#if analyticsView}
    {#key analyticsView}<ManagerAnalytics view={analyticsView} />{/key}
{:else if planningView}
    {#key planningView}<ManagerPlanning view={planningView} />{/key}
{:else if page.params.manager === 'reports'}
    <ManagerReports />
{:else if page.params.manager === 'profile' || page.params.manager === 'settings'}
    {#key page.params.manager}<ManagerAccount view={page.params.manager} />{/key}
{:else}
    <PlaceholderPage {title} />
{/if}
