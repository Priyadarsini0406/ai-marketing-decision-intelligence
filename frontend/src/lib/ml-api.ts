// Typed access to the trained lead-conversion model. Every value these helpers
// return is produced by the XGBoost pipeline, its out-of-fold import scores, or
// the TreeSHAP explainer bound to that same model. Nothing here is seeded or
// generated client side.
import { api } from './api';

export type ScoreBand = 'High' | 'Medium' | 'Low';

export type ShapFactor = {
    feature: string;
    category: string | null;
    shap_value: number;
    value: string | number | null;
};

/** Live inference for one lead, plus SHAP factors when `explain` is set. */
export type LeadPrediction = {
    customer_id: string | null;
    probability: number;
    score: ScoreBand;
    segment_cluster: number | null;
    segment: string | null;
    model: string;
    feature_source: string;
    note: string;
    factors?: ShapFactor[];
    top_positive?: ShapFactor[];
    top_negative?: ShapFactor[];
    base_value?: number;
    explanation_method?: string;
};

/** The out-of-fold prediction stored for a lead by backend/train_model.py. */
export type StoredPrediction = {
    lead_id: string;
    conversion_probability: number;
    admission_probability: number;
    lead_score: ScoreBand;
    segment_cluster: number | null;
    segment: string | null;
    model: string;
    explanation_method: string | null;
    base_value: number | null;
    top_positive: ShapFactor[];
    top_negative: ShapFactor[];
};

/** One row of the stored-prediction preview shown on the manager pages. */
export type PredictionPreview = {
    lead_id: string;
    customer_id: string | null;
    source: string | null;
    probability: number;
    score: ScoreBand;
    segment: string | null;
    observed_conversion: boolean | null;
};

/** Aggregated real segmentation, clustered on the model's own features. */
export type SegmentSummary = {
    segment_cluster: number;
    segment: string;
    leads: number;
    average_probability: number | null;
    high_score_leads: number;
    average_visits: number | null;
    average_pages_per_visit: number | null;
    average_time_on_site: number | null;
    known_outcomes: number;
    conversions: number;
    conversion_rate: number | null;
};

/** Counts over every stored score, not just the preview rows. */
export type PredictionSummary = {
    scored: number;
    high: number;
    medium: number;
    low: number;
    predicted_admissions: number;
    mean_probability: number | null;
};

export type WorkspaceOverview = {
    summary: { leads: number; conversions: number; ad_spend: number };
    prediction_preview: PredictionPreview[];
    prediction_summary: PredictionSummary;
};

export type LeadOption = {
    id: string;
    customer_id: string | null;
    enquiry_source: string | null;
};

export const leadLabel = (lead: LeadOption | null | undefined) =>
    lead?.customer_id || lead?.id || 'Unknown lead';

export function listLeads(limit = 100, skip = 0): Promise<LeadOption[]> {
    return api(`/leads?skip=${skip}&limit=${limit}`) as Promise<LeadOption[]>;
}

export function workspaceOverview(): Promise<WorkspaceOverview> {
    return api('/workspace/overview') as Promise<WorkspaceOverview>;
}

export function predictLead(leadId: string, explain = false): Promise<LeadPrediction> {
    return api(`/workspace/prediction/${encodeURIComponent(leadId)}?explain=${explain}`) as Promise<LeadPrediction>;
}

export function storedPrediction(leadId: string): Promise<StoredPrediction> {
    return api(`/leads/${encodeURIComponent(leadId)}/prediction`) as Promise<StoredPrediction>;
}

export function listSegments(): Promise<SegmentSummary[]> {
    return api('/workspace/segments') as Promise<SegmentSummary[]>;
}

/** "Lead Source = Google" reads better than a bare feature name in a chart. */
export function factorLabel(factor: ShapFactor): string {
    return factor.category === null ? factor.feature : `${factor.feature} = ${factor.category}`;
}

export function factorValue(factor: ShapFactor): string {
    return factor.value === null ? 'not recorded' : String(factor.value);
}

export const asPercent = (value: number | null | undefined, digits = 1) =>
    value === null || value === undefined || Number.isNaN(Number(value))
        ? '—'
        : `${(Number(value) * 100).toFixed(digits)}%`;

export const bandClasses: Record<string, string> = {
    High: 'bg-green-500/15 text-green-300',
    Medium: 'bg-yellow-500/15 text-yellow-300',
    Low: 'bg-red-500/15 text-red-300'
};

/** Everything the report pages need from the model, in three requests. */
export type ModelSnapshot = {
    predictions: PredictionPreview[];
    segments: SegmentSummary[];
    explanation: {
        lead: string;
        method: string | null;
        baseValue: number | null;
        factors: ShapFactor[];
    } | null;
};

export const emptyModelSnapshot: ModelSnapshot = { predictions: [], segments: [], explanation: null };

export async function loadModelSnapshot(): Promise<ModelSnapshot> {
    const [overview, segments] = await Promise.all([workspaceOverview(), listSegments()]);
    const predictions = overview.prediction_preview ?? [];
    // One real explanation, for the first stored lead, keeps the Explainable AI
    // report sections grounded in an actual TreeSHAP run.
    let explanation: ModelSnapshot['explanation'] = null;
    const lead = predictions[0];
    if (lead) {
        const live = await predictLead(lead.lead_id, true);
        explanation = {
            lead: lead.customer_id ?? lead.lead_id,
            method: live.explanation_method ?? null,
            baseValue: live.base_value ?? null,
            factors: live.factors ?? []
        };
    }
    return { predictions, segments, explanation };
}
