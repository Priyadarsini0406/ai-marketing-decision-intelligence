import { managerLeads, managerFunnelStages, managerChannels, managerCampaigns, managerBudget, managerReports, managerRecommendations, whatIfScenario } from './manager-demo';
import type { ModelSnapshot } from './ml-api';

export type ReportRow = Record<string, string | number | null>;
export type ManagerReport = { type: string; label: string; description: string; rows: ReportRow[] };
const ratio = (numerator: number, denominator: number, scale = 1) => denominator ? Number((numerator / denominator * scale).toFixed(2)) : null;
const totalAdmissions = managerChannels.reduce((sum, item) => sum + item.admissions, 0);

const observedOutcome = (value: boolean | null) => value === null ? null : value ? 'Converted' : 'Not converted';

// The prediction rows are the out-of-fold XGBoost scores stored in ml_predictions.
export function predictionReportRows(model: ModelSnapshot): ReportRow[] {
    return model.predictions.map(item => ({
        lead_id: item.customer_id ?? item.lead_id,
        source: item.source,
        conversion_probability: item.probability,
        lead_score: item.score,
        segment: item.segment,
        observed_outcome: observedOutcome(item.observed_conversion)
    }));
}

// Segment sizes and averages come from the K-Means fit over the model's features.
export function segmentReportRows(model: ModelSnapshot): ReportRow[] {
    return model.segments.map(item => ({
        segment_cluster: item.segment_cluster,
        segment: item.segment,
        leads: item.leads,
        average_probability: item.average_probability,
        high_score_leads: item.high_score_leads,
        average_visits: item.average_visits,
        average_pages_per_visit: item.average_pages_per_visit,
        average_time_on_site: item.average_time_on_site,
        known_outcomes: item.known_outcomes,
        conversions: item.conversions,
        conversion_rate: item.conversion_rate
    }));
}

const data: Record<string, ReportRow[]> = {
    lead: managerLeads.map(item => ({ ...item })),
    prediction: [],
    funnel: managerFunnelStages.map((item, index) => {
        const previous = index ? managerFunnelStages[index - 1].count : 0;
        return { stage: item.name, students: item.count, share_of_enquiries_percent: ratio(item.count, managerFunnelStages[0].count, 100), retention_percent: index ? ratio(item.count, previous, 100) : null, drop_off_count: index ? previous - item.count : null, drop_off_percent: index ? ratio(previous - item.count, previous, 100) : null };
    }),
    channel: managerChannels.map(item => ({ channel: item.channel, leads: item.leads, applications: item.applications, admissions: item.admissions, admission_rate_percent: ratio(item.admissions, item.leads, 100), admission_share_percent: ratio(item.admissions, totalAdmissions, 100), spend_inr: item.spend, cost_per_lead_inr: ratio(item.spend, item.leads), cost_per_admission_inr: ratio(item.spend, item.admissions) })),
    campaign: managerCampaigns.map(item => ({ campaign: item.name, channel: item.channel, budget_inr: item.budget, spend_inr: item.spend, remaining_inr: item.budget - item.spend, budget_used_percent: ratio(item.spend, item.budget, 100), leads: item.leads, applications: item.applications, admissions: item.admissions, admission_rate_percent: ratio(item.admissions, item.leads, 100), cost_per_admission_inr: ratio(item.spend, item.admissions) })),
    budget: managerBudget.allocations.map(item => ({ channel: item.channel, allocation_inr: item.currentAmount, budget_share_percent: ratio(item.currentAmount, managerBudget.totalBudget, 100) }))
};

export function buildReportCatalog(model: ModelSnapshot): ManagerReport[] {
    const rows: Record<string, ReportRow[]> = { ...data, prediction: predictionReportRows(model) };
    return managerReports.map(item => ({ type: item.type, label: item.label, description: item.description, rows: rows[item.type] ?? [] }));
}

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

export function fullReport(model: ModelSnapshot) {
    const catalog = buildReportCatalog(model);
    return {
        generated_at: new Date().toISOString(), currency: 'INR', source: 'Supplied manager demo datasets and live XGBoost model output',
        reports: Object.fromEntries(catalog.map(report => [report.type, report.rows])),
        budget_summary: { total_budget_inr: managerBudget.totalBudget, spent_inr: managerBudget.spent, remaining_inr: managerBudget.remaining },
        segments: segmentReportRows(model), recommendations: managerRecommendations, scenario_comparison: whatIfScenario,
        explanation: model.explanation
    };
}

export type FullAnalytics = ReturnType<typeof fullReport>;
export type AnalyticsSection = { key: string; title: string; rows: Record<string, unknown>[] };

// All formats use the same snapshot and sections, independent of preview filters.
export function analyticsSections(snapshot: FullAnalytics): AnalyticsSection[] {
    const explanation = snapshot.explanation;
    return [
        { key: 'metadata', title: 'Report information', rows: [{ generated_at: snapshot.generated_at, currency: snapshot.currency, source: snapshot.source }] },
        // managerReports fixes the section labels and order; the rows come from
        // the snapshot, so nothing here is rebuilt or re-seeded.
        ...managerReports.map(report => ({ key: report.type, title: report.label, rows: snapshot.reports[report.type] ?? [] })),
        { key: 'budget_summary', title: 'Budget summary', rows: [snapshot.budget_summary] },
        { key: 'segments', title: 'Student segmentation', rows: snapshot.segments },
        { key: 'recommendations', title: 'AI recommendations', rows: snapshot.recommendations },
        { key: 'scenario_comparison', title: 'What-if scenario comparison', rows: Object.entries(snapshot.scenario_comparison).map(([scenario, values]) => ({ scenario, ...values })) },
        { key: 'explanation_summary', title: 'Explainable AI summary', rows: [{ lead: explanation?.lead ?? 'No lead scored', method: explanation?.method ?? null, base_log_odds: explanation?.baseValue ?? null }] },
        { key: 'explanation_factors', title: 'Explainable AI factors', rows: (explanation?.factors ?? []).map(factor => ({ direction: factor.shap_value >= 0 ? 'positive' : 'negative', feature: factor.feature, category: factor.category, value: factor.value, shap_value: factor.shap_value })) }
    ];
}

export function fullReportCsv(snapshot: FullAnalytics): string {
    // One rectangular CSV: the section and record number identify each value.
    const rows: ReportRow[] = analyticsSections(snapshot).flatMap(section => section.rows.flatMap((row, index) =>
        Object.entries(row).map(([field, value]) => ({ section: section.key, record: index + 1, field, value: value == null ? null : typeof value === 'number' ? value : String(value) }))
    ));
    return reportCsv(rows);
}
