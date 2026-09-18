<script lang="ts">
    import { page } from '$app/state';
    import PlaceholderPage from '$lib/components/PlaceholderPage.svelte';
    const titles: Record<string, string> = { leads: 'Student Leads', prediction: 'Admission Prediction', 'explainable-ai': 'Explainable AI', segmentation: 'Student Segmentation', funnel: 'Admission Funnel', attribution: 'Channel Attribution', campaigns: 'Campaign Analytics', 'budget-optimization': 'Budget Optimization', 'what-if': 'What-If Simulator', recommendations: 'AI Recommendations', reports: 'Reports & Analytics', notifications: 'Notifications', profile: 'Profile', settings: 'Settings' };
    let title = $derived(titles[page.params.manager ?? ''] ?? 'Decision-Intel Module');
</script>
<PlaceholderPage {title} />
