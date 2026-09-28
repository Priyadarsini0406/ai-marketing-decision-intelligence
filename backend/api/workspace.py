"""Marketing workspace analytics and model inference."""
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import math
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from api.auth import current_user
from database.connection import get_db
from database.models import Lead, ChannelMetric, BudgetSimulation, MLPrediction
from database.models import UserPreference
from typing import Literal

router = APIRouter(prefix="/workspace", tags=["marketing workspace"], dependencies=[Depends(current_user)])

class Preferences(BaseModel):
    currency: Literal['USD', 'INR', 'EUR', 'GBP'] = 'USD'
    compact: bool = False

@router.get('/settings')
def settings(user=Depends(current_user), db: Session = Depends(get_db)):
    record = db.get(UserPreference, user.id)
    return record.values if record else Preferences().model_dump()

@router.put('/settings')
def save_settings(data: Preferences, user=Depends(current_user), db: Session = Depends(get_db)):
    record = db.get(UserPreference, user.id)
    if record is None:
        record = UserPreference(user_id=user.id)
        db.add(record)
    record.values = data.model_dump()
    db.commit()
    return record.values

@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    leads = db.query(Lead).all()
    groups = defaultdict(lambda: {"leads": 0, "conversions": 0, "spend": 0.0})
    for lead in leads:
        group = groups[lead.campaign_channel or "Unknown"]
        group["leads"] += 1
        group["conversions"] += int(bool(lead.conversion))
        group["spend"] += lead.ad_spend or 0
    channels = [{"channel": name, **g, "conversion_rate": round(g["conversions"] / g["leads"], 4),
                 "cost_per_conversion": round(g["spend"] / g["conversions"], 2) if g["conversions"] else None}
                for name, g in sorted(groups.items())]
    funnel = [{"stage": "All leads", "count": len(leads)},
              {"stage": "Visited website", "count": sum((l.website_visits or 0) > 0 for l in leads)},
              {"stage": "Visited and converted", "count": sum((l.website_visits or 0) > 0 and bool(l.conversion) for l in leads)}]
    campaigns = defaultdict(lambda: {"leads": 0, "conversions": 0, "spend": 0.0})
    for lead in leads:
        g = campaigns[lead.campaign_type or "Unknown"]
        g["leads"] += 1; g["conversions"] += int(bool(lead.conversion)); g["spend"] += lead.ad_spend or 0
    recommendations = []
    ranked = sorted([c for c in channels if c["cost_per_conversion"] is not None], key=lambda c: c["cost_per_conversion"])
    if ranked:
        recommendations.append({"action": "Evaluate a small budget test", "channel": ranked[0]["channel"],
                                "evidence": f"Lowest observed cost per conversion: {ranked[0]['cost_per_conversion']}",
                                "qualification": "Historical association; validate with a controlled test."})
    unconverted = sum(not bool(l.conversion) for l in leads)
    if unconverted:
        recommendations.append({"action": "Review unconverted leads for follow-up", "channel": "All channels",
                                "evidence": f"{unconverted} leads have not converted", "qualification": "Check contact consent and recency before outreach."})
    cohorts = defaultdict(list)
    for lead in leads:
        age_band = 'Unknown' if lead.age is None else 'Under 25' if lead.age < 25 else '25-34' if lead.age < 35 else '35-44' if lead.age < 45 else '45-54' if lead.age < 55 else '55+'
        cohorts[(lead.campaign_channel or 'Unknown', lead.campaign_type or 'Unknown', age_band)].append(lead)
    breakdowns = []
    for (channel, campaign, age_band), members in sorted(cohorts.items()):
        converted = sum(l.conversion is True for l in members)
        known = sum(l.conversion is not None for l in members)
        spend = sum(l.ad_spend or 0 for l in members)
        breakdowns.append({'channel': channel, 'campaign_type': campaign, 'age_band': age_band,
                          'leads': len(members), 'known_outcomes': known, 'conversions': converted,
                          'conversion_rate': round(converted / known, 4) if known else None,
                          'spend': round(spend, 2), 'website_visitors': sum((l.website_visits or 0) > 0 for l in members),
                          'email_engaged': sum((l.email_clicks or 0) > 0 for l in members),
                          'repeat_buyers': sum((l.previous_purchases or 0) > 0 for l in members)})
    for channel in sorted(groups):
        members = [l for l in leads if (l.campaign_channel or 'Unknown') == channel]
        followups = sum(l.conversion is False and (l.email_clicks or 0) > 0 for l in members)
        if followups:
            recommendations.append({'action': 'Review engaged non-converters', 'channel': channel,
                                    'evidence': f'{followups} non-converters recorded email clicks',
                                    'qualification': 'Confirm recency and consent before testing a follow-up campaign.'})
        recommendations.append({'action': 'Review campaign mix', 'channel': channel,
                                'evidence': f'{len(members)} leads across {len(set(l.campaign_type for l in members))} campaign types',
                                'qualification': 'Use the cohort breakdown to compare outcomes; small cohorts are uncertain.'})
    prediction_rows = db.query(MLPrediction, Lead).join(Lead, MLPrediction.lead_id == Lead.id).order_by(Lead.customer_id).limit(50).all()
    prediction_preview = [{'lead_id': l.id, 'customer_id': l.customer_id, 'source': l.enquiry_source,
                           'probability': p.conversion_probability, 'score': p.lead_score,
                           'segment': p.segment_name,
                           'observed_conversion': l.conversion} for p, l in prediction_rows]
    # Aggregates over every stored score, so the UI never has to infer totals from the 50-row preview.
    scored = db.query(MLPrediction.conversion_probability, MLPrediction.lead_score).all()
    prediction_summary = {
        "scored": len(scored),
        "high": sum(svc.score_band(probability) == "High" for probability, _ in scored),
        "medium": sum(svc.score_band(probability) == "Medium" for probability, _ in scored),
        "low": sum(svc.score_band(probability) == "Low" for probability, _ in scored),
        "predicted_admissions": sum((probability or 0) >= 0.5 for probability, _ in scored),
        "mean_probability": round(sum(probability or 0 for probability, _ in scored) / len(scored), 4) if scored else None
    }
    scenarios = [{'scenario': s.scenario_name, 'allocations': s.allocations,
                  'estimated_conversions': s.predicted_conversions, 'estimated_cpa': s.predicted_cpa}
                 for s in db.query(BudgetSimulation).order_by(BudgetSimulation.scenario_name).limit(50)]
    return {"summary": {"leads": len(leads), "conversions": sum(bool(l.conversion) for l in leads),
                        "ad_spend": round(sum(l.ad_spend or 0 for l in leads), 2)},
            "channels": channels, "funnel": funnel,
            "campaigns": [{"campaign_type": name, **g} for name, g in sorted(campaigns.items())],
            "recommendations": recommendations, "cohorts": breakdowns,
            "prediction_preview": prediction_preview, "prediction_summary": prediction_summary,
            "saved_scenarios": scenarios}

@lru_cache(maxsize=2)
def load_model(stamp):
    import ml_service as svc
    return svc.load_pipeline()

@lru_cache(maxsize=2)
def load_segments(stamp):
    import ml_service as svc
    return svc.load_segments()

def model_and_frame(lead):
    """Resolve the lead's real feature vector and the trained XGBoost pipeline."""
    import ml_service as svc
    if not svc.MODEL_PATH.exists():
        raise HTTPException(409, "Train the lead conversion model before requesting predictions.")
    try:
        pipeline, contract = load_model(svc.MODEL_PATH.stat().st_mtime_ns)
        frame, frame_source = svc.frame_for_lead(lead, contract)
    except svc.PipelineError as error:
        raise HTTPException(409, str(error))
    return pipeline, contract, frame, frame_source

def live_segment(pipeline, frame):
    """The lead's real cluster, from the same fitted segmentation the import used."""
    import ml_service as svc
    try:
        artifact = load_segments(svc.SEGMENT_PATH.stat().st_mtime_ns)
        cluster, name = svc.assign_segments(artifact, pipeline, frame)
        return cluster[0], name[0]
    except (svc.PipelineError, FileNotFoundError):
        return None, None

@router.get("/prediction/{lead_id}")
def prediction(lead_id: str, explain: bool = False, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if lead is None: raise HTTPException(404, "Lead not found")
    import ml_service as svc
    pipeline, contract, frame, frame_source = model_and_frame(lead)
    probability = float(pipeline.predict_proba(frame)[0, 1])
    cluster, segment = live_segment(pipeline, frame)
    result = {"customer_id": lead.customer_id, "probability": probability,
              "score": svc.score_band(probability),
              "segment_cluster": cluster, "segment": segment,
              "model": contract.get("model", "lead_conversion_xgboost"),
              "feature_source": frame_source,
              "note": "Live XGBoost inference. The model is refit on all dataset rows, "
                      "so this is not an independent evaluation of the lead."}
    if explain:
        factor = svc.explain_frame(
            pipeline, frame, contract["numeric_features"], contract["categorical_features"], top_n=5
        )[0]
        result["factors"] = factor["top_positive"] + factor["top_negative"]
        result["top_positive"] = factor["top_positive"]
        result["top_negative"] = factor["top_negative"]
        result["base_value"] = factor["base_value"]
        result["explanation_method"] = factor["method"]
    return result

@router.get("/segments")
def segments(db: Session = Depends(get_db)):
    """Segment sizes and real averages, aggregated from the stored predictions.

    The clusters come from K-Means over the XGBoost pipeline's own imputed
    engagement features, so a segment describes measured behaviour rather than
    row order. No value here is randomised.
    """
    rows = db.query(MLPrediction.segment_cluster, MLPrediction.segment_name,
                    MLPrediction.conversion_probability, MLPrediction.lead_score,
                    Lead.website_visits, Lead.pages_per_visit, Lead.time_on_site,
                    Lead.conversion).join(Lead, MLPrediction.lead_id == Lead.id).all()
    if not rows: return []

    buckets = defaultdict(lambda: {"leads": 0, "probability": [], "high": 0,
                                   "visits": [], "pages": [], "time": [],
                                   "conversions": 0, "known": 0})
    for cluster, name, probability, score, visits, pages, time_on_site, conversion in rows:
        if cluster is None or not name: continue
        bucket = buckets[cluster]
        bucket["segment"] = name
        bucket["leads"] += 1
        bucket["probability"].append(float(probability or 0.0))
        bucket["high"] += int(score == "High")
        bucket["visits"].append(float(visits or 0.0))
        bucket["pages"].append(float(pages or 0.0))
        bucket["time"].append(float(time_on_site or 0.0))
        bucket["known"] += int(conversion is not None)
        bucket["conversions"] += int(conversion is True)

    def mean(values): return round(sum(values) / len(values), 4) if values else None

    return [{"segment_cluster": cluster, "segment": bucket["segment"], "leads": bucket["leads"],
             "average_probability": mean(bucket["probability"]),
             "high_score_leads": bucket["high"],
             "average_visits": mean(bucket["visits"]),
             "average_pages_per_visit": mean(bucket["pages"]),
             "average_time_on_site": mean(bucket["time"]),
             "known_outcomes": bucket["known"], "conversions": bucket["conversions"],
             "conversion_rate": round(bucket["conversions"] / bucket["known"], 4) if bucket["known"] else None}
            for cluster, bucket in sorted(buckets.items())]

class SimulationInput(BaseModel):
    budget: float = Field(gt=0, le=100000000, allow_inf_nan=False)
    mode: str = Field(pattern="^(equal|efficiency|optimized|custom)$")
    max_channel_share: float = Field(default=1, gt=0, le=1, allow_inf_nan=False)
    allocations: dict[str, float] = Field(default_factory=dict)

@router.post("/simulate")
def simulate(data: SimulationInput, db: Session = Depends(get_db)):
    channels = overview(db)["channels"]
    efficiency = {c["channel"]: c["conversions"] / c["spend"] for c in channels if c["spend"] > 0}
    if not efficiency: raise HTTPException(409, "Import leads with positive ad spend first.")
    if data.mode == "custom":
        if set(data.allocations) - set(efficiency) or any(not math.isfinite(v) or v < 0 for v in data.allocations.values()):
            raise HTTPException(422, "Allocations must use known channels and nonnegative finite amounts.")
        if not math.isclose(sum(data.allocations.values()), data.budget, abs_tol=.01, rel_tol=0):
            raise HTTPException(422, "Channel allocations must add up to the budget.")
        allocations = data.allocations
    elif data.mode == 'optimized':
        from scipy.optimize import linprog
        names = list(efficiency)
        solution = linprog([-efficiency[name] for name in names],
                           A_eq=[np.ones(len(names))], b_eq=[data.budget],
                           bounds=[(0, data.budget * data.max_channel_share)] * len(names), method='highs')
        if not solution.success:
            raise HTTPException(422, 'The channel cap is too small to allocate the full budget across available channels.')
        allocations = {name: round(float(value), 2) for name, value in zip(names, solution.x)}
        last = max(allocations, key=allocations.get)
        allocations[last] = round(allocations[last] + data.budget - sum(allocations.values()), 2)
    else:
        weights = {c: 1.0 for c in efficiency} if data.mode == "equal" else efficiency
        if sum(weights.values()) == 0: raise HTTPException(409, "No historical conversions available.")
        allocations = {c: round(data.budget * w / sum(weights.values()), 2) for c, w in weights.items()}
        last = next(reversed(allocations))
        allocations[last] = round(allocations[last] + data.budget - sum(allocations.values()), 2)
    conversions = sum(v * efficiency[c] for c, v in allocations.items())
    return {"allocations": allocations, "predicted_conversions": round(conversions, 2),
            "predicted_cpa": round(data.budget / conversions, 2) if conversions else None,
            "assumption": "Illustrative linear projection using historical conversion per spend; no saturation or causal uplift model."}
