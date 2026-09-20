import { managerLeads, managerFunnelStages, managerChannels, managerCampaigns, managerBudget, managerReports, managerSegments, managerRecommendations, whatIfScenario, shapDemo } from './manager-demo';

export type ReportRow = Record<string, string | number | null>;
export type ManagerReport = { type: string; label: string; description: string; rows: ReportRow[] };
const ratio = (numerator: number, denominator: number, scale = 1) => denominator ? Number((numerator / denominator * scale).toFixed(2)) : null;
const totalAdmissions = managerChannels.reduce((sum, item) => sum + item.admissions, 0);

const data: Record<string, ReportRow[]> = {
    lead: managerLeads.map(item => ({ ...item })),
    prediction: managerLeads.map(item => ({ student_id: item.id, student_name: item.student_name, course: item.course_interested, source: item.source, lead_status: item.lead_status, prediction: item.prediction, admission_probability_percent: item.probability })),
    funnel: managerFunnelStages.map((item, index) => {
        const previous = index ? managerFunnelStages[index - 1].count : 0;
        return { stage: item.name, students: item.count, share_of_enquiries_percent: ratio(item.count, managerFunnelStages[0].count, 100), retention_percent: index ? ratio(item.count, previous, 100) : null, drop_off_count: index ? previous - item.count : null, drop_off_percent: index ? ratio(previous - item.count, previous, 100) : null };
    }),
    channel: managerChannels.map(item => ({ channel: item.channel, leads: item.leads, applications: item.applications, admissions: item.admissions, admission_rate_percent: ratio(item.admissions, item.leads, 100), admission_share_percent: ratio(item.admissions, totalAdmissions, 100), spend_inr: item.spend, cost_per_lead_inr: ratio(item.spend, item.leads), cost_per_admission_inr: ratio(item.spend, item.admissions) })),
    campaign: managerCampaigns.map(item => ({ campaign: item.name, channel: item.channel, budget_inr: item.budget, spend_inr: item.spend, remaining_inr: item.budget - item.spend, budget_used_percent: ratio(item.spend, item.budget, 100), leads: item.leads, applications: item.applications, admissions: item.admissions, admission_rate_percent: ratio(item.admissions, item.leads, 100), cost_per_admission_inr: ratio(item.spend, item.admissions) })),
    budget: managerBudget.allocations.map(item => ({ channel: item.channel, allocation_inr: item.currentAmount, budget_share_percent: ratio(item.currentAmount, managerBudget.totalBudget, 100) }))
};

export const reportCatalog: ManagerReport[] = managerReports.map(item => ({ type: item.type, label: item.label, description: item.description, rows: data[item.type] }));

export function reportCsv(rows: ReportRow[]): string {
    if (!rows.length) return '';
    const columns = Object.keys(rows[0]);
    const escape = (value: ReportRow[string]) => {
        let text = value == null ? '' : String(value);
        // Keep text safe when opened in spreadsheet software; preserve numeric values.
        if (typeof value === 'string' && /^[\s]*[=+@-]/.test(text)) text = "'" + text;
        return '"' + text.replaceAll('"', '""') + '"';
    };
    return '\uFEFF' + [columns.map(escape).join(','), ...rows.map(row => columns.map(column => escape(row[column])).join(','))].join('\r\n');
}

export function fullReport() {
    return {
        generated_at: new Date().toISOString(), currency: 'INR', source: 'Supplied manager demo datasets',
        reports: Object.fromEntries(reportCatalog.map(report => [report.type, report.rows])),
        budget_summary: { total_budget_inr: managerBudget.totalBudget, spent_inr: managerBudget.spent, remaining_inr: managerBudget.remaining },
        segments: managerSegments, recommendations: managerRecommendations, scenario_comparison: whatIfScenario,
        explanation: shapDemo
    };
}

export type FullAnalytics = ReturnType<typeof fullReport>;
export type AnalyticsSection = { key: string; title: string; rows: Record<string, unknown>[] };

// All formats use the same snapshot and sections, independent of preview filters.
export function analyticsSections(snapshot: FullAnalytics): AnalyticsSection[] {
    return [
        { key: 'metadata', title: 'Report information', rows: [{ generated_at: snapshot.generated_at, currency: snapshot.currency, source: snapshot.source }] },
        ...reportCatalog.map(report => ({ key: report.type, title: report.label, rows: snapshot.reports[report.type] })),
        { key: 'budget_summary', title: 'Budget summary', rows: [snapshot.budget_summary] },
        { key: 'segments', title: 'Student segmentation', rows: snapshot.segments },
        { key: 'recommendations', title: 'AI recommendations', rows: snapshot.recommendations },
        { key: 'scenario_comparison', title: 'What-if scenario comparison', rows: Object.entries(snapshot.scenario_comparison).map(([scenario, values]) => ({ scenario, ...values })) },
        { key: 'explanation_summary', title: 'Explainable AI summary', rows: [{ summary: snapshot.explanation.summary }] },
        { key: 'explanation_factors', title: 'Explainable AI factors', rows: [...snapshot.explanation.positive.map(item => ({ direction: 'positive', ...item })), ...snapshot.explanation.negative.map(item => ({ direction: 'negative', ...item }))] }
    ];
}

export function fullReportCsv(snapshot: FullAnalytics): string {
    // One rectangular CSV: the section and record number identify each value.
    const rows: ReportRow[] = analyticsSections(snapshot).flatMap(section => section.rows.flatMap((row, index) =>
        Object.entries(row).map(([field, value]) => ({ section: section.key, record: index + 1, field, value: value == null ? null : typeof value === 'number' ? value : String(value) }))
    ));
    return reportCsv(rows);
}
