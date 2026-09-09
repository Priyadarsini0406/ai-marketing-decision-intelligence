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
    prediction_preview = [{'customer_id': l.customer_id, 'channel': l.campaign_channel,
                           'probability': p.conversion_probability, 'score': p.lead_score,
                           'observed_conversion': l.conversion} for p, l in prediction_rows]
    scenarios = [{'scenario': s.scenario_name, 'allocations': s.allocations,
                  'estimated_conversions': s.predicted_conversions, 'estimated_cpa': s.predicted_cpa}
                 for s in db.query(BudgetSimulation).order_by(BudgetSimulation.scenario_name).limit(50)]
    return {"summary": {"leads": len(leads), "conversions": sum(bool(l.conversion) for l in leads),
                        "ad_spend": round(sum(l.ad_spend or 0 for l in leads), 2)},
            "channels": channels, "funnel": funnel,
            "campaigns": [{"campaign_type": name, **g} for name, g in sorted(campaigns.items())],
            "recommendations": recommendations, "cohorts": breakdowns,
            "prediction_preview": prediction_preview, "saved_scenarios": scenarios}

@lru_cache(maxsize=2)
def load_model(stamp):
    import joblib
    return joblib.load(Path(__file__).resolve().parents[1] / "artifacts/conversion_model.joblib")

def model_and_frame(lead):
    import pandas as pd
    from train_model import FEATURES, COLUMNS
    path = Path(__file__).resolve().parents[1] / "artifacts/conversion_model.joblib"
    if not path.exists():
        raise HTTPException(409, "Train the conversion model before requesting predictions.")
    model = load_model(path.stat().st_mtime_ns)
    row = {feature: getattr(lead, COLUMNS[feature]) for feature in FEATURES}
    if any(value is None for value in row.values()):
        raise HTTPException(422, "This lead is missing required model features.")
    return model, pd.DataFrame([row])

@router.get("/prediction/{lead_id}")
def prediction(lead_id: str, explain: bool = False, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if lead is None: raise HTTPException(404, "Lead not found")
    model, frame = model_and_frame(lead)
    probability = float(model.predict_proba(frame)[0, 1])
    result = {"customer_id": lead.customer_id, "probability": probability,
              "score": "High" if probability >= .7 else "Medium" if probability >= .4 else "Low",
              "note": "Current model inference. Imported training leads are not an independent evaluation."}
    if explain:
        import shap
        encoded = model.named_steps["encode"].transform(frame)
        explainer = shap.TreeExplainer(model.named_steps["classifier"])
        values = np.asarray(explainer.shap_values(encoded)).reshape(-1)
        names = model.named_steps["encode"].get_feature_names_out()
        result["factors"] = sorted([{"feature": str(name), "log_odds_contribution": float(value)}
                                    for name, value in zip(names, values)], key=lambda r: abs(r["log_odds_contribution"]), reverse=True)
        result["base_log_odds"] = float(np.asarray(explainer.expected_value).reshape(-1)[0])
    return result

@router.get("/segments")
def segments(db: Session = Depends(get_db)):
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    leads = db.query(Lead).order_by(Lead.customer_id).all()
    if not leads: return []
    features = np.array([[l.website_visits or 0, l.email_clicks or 0, l.previous_purchases or 0, l.loyalty_points or 0] for l in leads], dtype=float)
    count = min(4, len(np.unique(features, axis=0)))
    labels = KMeans(n_clusters=count, random_state=42, n_init=10).fit_predict(StandardScaler().fit_transform(features))
    return [{"segment": f"Behavior cluster {i + 1}", "leads": int(sum(labels == i)),
             "average_visits": round(float(features[labels == i, 0].mean()), 2),
             "average_email_clicks": round(float(features[labels == i, 1].mean()), 2),
             "average_purchases": round(float(features[labels == i, 2].mean()), 2),
             "average_loyalty_points": round(float(features[labels == i, 3].mean()), 2)} for i in range(count)]

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
