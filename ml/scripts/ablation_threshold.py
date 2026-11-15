"""Leakage ablation (one post-contact column group at a time) and threshold sweep.
Merges results into docs/paper/figures/extra_results.json.

    python ml/scripts/ablation_threshold.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ml" / "scripts"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from xgboost import XGBClassifier  # noqa: E402

import ml_service as svc  # noqa: E402
from train_improved_models import POST_CONTACT_COLUMNS, SEED, base_models, preprocessor  # noqa: E402

warnings.filterwarnings("ignore")
FIG = ROOT / "docs" / "paper" / "figures"
RES = json.loads((ROOT / "ml" / "reports" / "improved" / "improved_results.json").read_text())
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "legend.fontsize": 7})

frame = svc.read_dataset()
numeric, categorical, _ = svc.resolve_features(frame, include_post_contact=True)
y = frame[svc.TARGET_COLUMN].astype(int)
GROUPS = {"Tags": ["Tags"], "Lead Quality": ["Lead Quality"], "Lead Profile": ["Lead Profile"],
          "Asymmetrique (4 cols)": [c for c in POST_CONTACT_COLUMNS if c.startswith("Asymmetrique")]}


def auc_for(keep: list[str]) -> float:
    num = [c for c in numeric if c in keep]
    cat = [c for c in categorical if c in keep]
    x_tr, x_te, y_tr, y_te = train_test_split(frame[num + cat], y, test_size=0.2, stratify=y, random_state=SEED)
    pipe = Pipeline([("pre", preprocessor(num, cat)), ("model", base_models(2)["XGBoost"])]).fit(x_tr, y_tr)
    return float(roc_auc_score(y_te, pipe.predict_proba(x_te)[:, 1]))


free = [c for c in numeric + categorical if c not in POST_CONTACT_COLUMNS]
base_auc = auc_for(free)
ablation = [{"added": "None (leakage-free)", "auc": base_auc, "gain": 0.0}]
for name, cols in GROUPS.items():
    a = auc_for(free + cols)
    ablation.append({"added": f"+ {name}", "auc": a, "gain": a - base_auc})
full_auc = auc_for(numeric + categorical)
ablation.append({"added": "All seven (full set)", "auc": full_auc, "gain": full_auc - base_auc})
print(json.dumps(ablation, indent=1))

# threshold sweep on the leakage-free tuned XGBoost
num = [c for c in numeric if c in free]
cat = [c for c in categorical if c in free]
x_tr, x_te, y_tr, y_te = train_test_split(frame[num + cat], y, test_size=0.2, stratify=y, random_state=SEED)
pipe = Pipeline([("pre", preprocessor(num, cat)),
                 ("model", XGBClassifier(**RES["lead"][1]["tuned_params"]["XGBoost"], random_state=SEED, n_jobs=-1))]).fit(x_tr, y_tr)
p = pipe.predict_proba(x_te)[:, 1]
ts = np.linspace(0.05, 0.95, 91)
P = [precision_score(y_te, p >= t, zero_division=0) for t in ts]
Rc = [recall_score(y_te, p >= t) for t in ts]
F = [f1_score(y_te, p >= t) for t in ts]
bi = int(np.argmax(F))
fig, ax = plt.subplots(figsize=(3.4, 2.2))
ax.plot(ts, P, lw=1, label="Precision")
ax.plot(ts, Rc, lw=1, label="Recall")
ax.plot(ts, F, lw=1, label="F1")
ax.axvline(0.5, color="grey", ls=":", lw=0.7)
ax.axvline(ts[bi], color="k", ls="--", lw=0.6)
ax.text(ts[bi] + 0.01, 0.30, f"max F1 at {ts[bi]:.2f}", fontsize=6)
ax.set_xlabel("Decision threshold")
ax.set_ylabel("Score")
ax.set_ylim(0, 1.02)
ax.legend(loc="lower left", frameon=False, ncol=3)
ax.grid(alpha=0.3, lw=0.4)
fig.savefig(FIG / "fig_threshold.png", dpi=300, bbox_inches="tight")
thr = {"best_threshold": float(ts[bi]), "best_f1": float(F[bi]), "p_at_best": float(P[bi]), "r_at_best": float(Rc[bi]),
       "p_at_05": float(P[45]), "r_at_05": float(Rc[45]), "f1_at_05": float(F[45])}
print(thr)

path = FIG / "extra_results.json"
data = json.loads(path.read_text())
data["ablation"] = ablation
data["threshold"] = thr
path.write_text(json.dumps(data, indent=1))
