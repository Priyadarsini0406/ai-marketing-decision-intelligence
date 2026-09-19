"""Populate channel analytics and illustrative budgets from stored campaign leads."""
import json
import math
from collections import defaultdict

from database.connection import Base, SessionLocal, engine
from database.models import BudgetSimulation, ChannelMetric, Lead


def populate(db):
    channels = defaultdict(lambda: {'spend': 0.0, 'conversions': 0, 'rows': 0})
    for lead in db.query(Lead).all():
        if not lead.campaign_channel or lead.ad_spend is None or lead.conversion is None:
            continue
        if not math.isfinite(lead.ad_spend) or lead.ad_spend < 0:
            raise ValueError('Lead ad spend must be finite and nonnegative')
        group = channels[lead.campaign_channel]
        group['spend'] += lead.ad_spend
        group['conversions'] += int(lead.conversion)
        group['rows'] += 1
    if not channels:
        raise ValueError('Import campaign leads before generating analytics')
    for name, group in channels.items():
        metric = db.query(ChannelMetric).filter_by(channel_name=name).first()
        if metric is None:
            metric = ChannelMetric(channel_name=name)
            db.add(metric)
        metric.total_spend = round(group['spend'], 2)
        metric.total_conversions = group['conversions']
        metric.historical_cac = round(group['spend'] / group['conversions'], 2) if group['conversions'] else None
        metric.historical_conversion_rate = group['conversions'] / group['rows']

    eligible = {name: group for name, group in sorted(channels.items()) if group['spend'] > 0}
    if not eligible:
        raise ValueError('Positive historical spend is needed for budget scenarios')
    efficiency = {name: group['conversions'] / group['spend'] for name, group in eligible.items()}
    weights = {
        'Illustrative - equal allocation': {name: 1 for name in eligible},
        'Illustrative - historical spend mix': {name: group['spend'] for name, group in eligible.items()},
    }
    if sum(efficiency.values()) > 0:
        weights['Illustrative - conversion efficiency mix'] = efficiency
    scenarios = [(name, shares, 100000.0) for name, shares in weights.items()]
    # Deterministic what-if scenarios across budgets and channel emphasis.
    channel_names = list(eligible)
    for index in range(50 - len(scenarios)):
        focus = channel_names[index % len(channel_names)]
        multiplier = 2 + (index // len(channel_names)) % 4
        shares = {channel: multiplier if channel == focus else 1 for channel in eligible}
        budget = float(25000 + (index // len(channel_names)) * 25000)
        name = f'Illustrative - scenario {index + 1:02d} - {focus} emphasis - budget {budget:,.0f}'
        scenarios.append((name, shares, budget))
    for name, shares, budget in scenarios:
        total = sum(shares.values())
        allocations = {channel: round(budget * share / total, 2) for channel, share in shares.items()}
        last = next(reversed(allocations))
        allocations[last] = round(allocations[last] + budget - sum(allocations.values()), 2)
        conversions = sum(amount * efficiency[channel] for channel, amount in allocations.items())
        scenario = db.query(BudgetSimulation).filter_by(scenario_name=name).first()
        if scenario is None:
            scenario = BudgetSimulation(scenario_name=name)
            db.add(scenario)
        scenario.allocations = allocations
        scenario.predicted_conversions = round(conversions, 2)
        scenario.predicted_cpa = round(budget / conversions, 2) if conversions else None
    db.flush()
    return {'channels': len(channels), 'scenarios': len(scenarios),
            'source_rows': sum(group['rows'] for group in channels.values())}


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    with SessionLocal.begin() as db:
        print(json.dumps(populate(db), indent=2))
