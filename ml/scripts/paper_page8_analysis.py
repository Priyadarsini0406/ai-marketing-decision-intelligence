"""PR curves, SHAP dependence plot, error analysis by lead origin and training times.
Merges into docs/paper/figures/extra_results.json.

    python ml/scripts/paper_page8_analysis.py [path/to/improved_run.log]
"""
from __future__ import annotations

import json
import re
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
import shap  # noqa: E402
from sklearn.metrics import average_precision_score, precision_recall_curve  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from lightgbm import LGBMClassifier  # noqa: E402
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
num = [c for c in numeric if c not in POST_CONTACT_COLUMNS]
cat = [c for c in categorical if c not in POST_CONTACT_COLUMNS]
y = frame[svc.TARGET_COLUMN].astype(int)
x_tr, x_te, y_tr, y_te = train_test_split(frame[num + cat], y, test_size=0.2, stratify=y, random_state=SEED)
params = RES["lead"][1]["tuned_params"]
models = {"LR": base_models(2)["Logistic Regression"], "RF": base_models(2)["Random Forest"],
          "XGB-T": XGBClassifier(**params["XGBoost"], random_state=SEED, n_jobs=-1),
          "LGBM-T": LGBMClassifier(**params["LightGBM"], subsample_freq=1, random_state=SEED, n_jobs=-1, verbose=-1)}
out = {"average_precision": {}}
fig, ax = plt.subplots(figsize=(3.4, 2.3))
fitted = {}
for name, model in models.items():
    pipe = Pipeline([("pre", preprocessor(num, cat)), ("model", model)]).fit(x_tr, y_tr)
    fitted[name] = pipe
    p = pipe.predict_proba(x_te)[:, 1]
    pr, rc, _ = precision_recall_curve(y_te, p)
    ap = average_precision_score(y_te, p)
    out["average_precision"][name] = float(ap)
    ax.plot(rc, pr, lw=0.9, label=f"{name} (AP={ap:.3f})")
ax.axhline(y_te.mean(), color="k", ls="--", lw=0.5)
ax.set_xlabel("Recall")
ax.set_ylabel("Precision")
ax.set_ylim(0.3, 1.02)
ax.legend(loc="lower left", frameon=False)
ax.grid(alpha=0.3, lw=0.4)
fig.savefig(FIG / "fig_pr.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# SHAP dependence for time on site
pipe = fitted["XGB-T"]
pre, model = pipe.named_steps["pre"], pipe.named_steps["model"]
xt = pre.transform(x_te)
sv = shap.TreeExplainer(model).shap_values(xt)
names = list(pre.get_feature_names_out())
j = names.index("num__Total Time Spent on Website")
raw = x_te["Total Time Spent on Website"].to_numpy()
fig, ax = plt.subplots(figsize=(3.4, 2.1))
ax.scatter(raw, sv[:, j], s=3, alpha=0.4, color="#4c72b0", linewidths=0)
ax.axhline(0, color="k", lw=0.5)
ax.set_xlabel("Total time spent on website (s)")
ax.set_ylabel("SHAP value (log-odds)")
ax.grid(alpha=0.3, lw=0.4)
fig.savefig(FIG / "fig_shap_time.png", dpi=300, bbox_inches="tight")
plt.close(fig)
# where the contribution turns positive
order = np.argsort(raw)
cross = raw[order][np.argmax(np.convolve(sv[order, j], np.ones(25) / 25, mode="same") > 0)]
out["shap_time_crossover_s"] = float(cross)

# error analysis by lead origin (threshold 0.5)
p = pipe.predict_proba(x_te)[:, 1]
pred = (p >= 0.5).astype(int)
te = x_te.assign(y=y_te.to_numpy(), pred=pred)
rows = []
for origin, g in te.groupby("Lead Origin"):
    if len(g) < 30:
        continue
    rows.append({"origin": origin, "n": int(len(g)), "conv": float(g["y"].mean()),
                 "acc": float((g["y"] == g["pred"]).mean()),
                 "fnr": float(((g["y"] == 1) & (g["pred"] == 0)).sum() / max(1, (g["y"] == 1).sum())),
                 "fpr": float(((g["y"] == 0) & (g["pred"] == 1)).sum() / max(1, (g["y"] == 0).sum()))})
out["error_by_origin"] = sorted(rows, key=lambda r: -r["n"])

# per-model wall time (fit + 5-fold CV) from the experiment log, leakage-free suite
log = Path(sys.argv[1]) if len(sys.argv) > 1 else None
times = {}
if log and log.exists():
    txt = log.read_text(encoding="utf-8", errors="ignore")
    block = txt.split("=== Lead - leakage-free features")[1].split("===")[0]
    for m in re.finditer(r"^\s+(.+?)\s+F1=[\d.]+ AUC=[\d.]+ \((\d+)s\)", block, re.M):
        times[m.group(1).strip()] = int(m.group(2))
    t = re.findall(r"tuned (\w+) in (\d+)s", block)
    out["tuning_seconds"] = {k: int(v) for k, v in t}
out["model_seconds"] = times

path = FIG / "extra_results.json"
data = json.loads(path.read_text())
data.update(out)
path.write_text(json.dumps(data, indent=1))
print(json.dumps(out, indent=1))
