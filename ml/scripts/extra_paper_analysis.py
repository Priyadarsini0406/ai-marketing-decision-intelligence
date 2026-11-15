"""Extra analyses for the 8-page paper: calibration, capacity (top-k) analysis,
confusion matrix, CV error bars, channel conversion, K-Means segment quality,
budget-allocation example, and the workflow diagram.

    python ml/scripts/extra_paper_analysis.py
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
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from scipy.optimize import linprog  # noqa: E402
from sklearn.calibration import calibration_curve  # noqa: E402
from sklearn.metrics import brier_score_loss, confusion_matrix, roc_auc_score, silhouette_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from xgboost import XGBClassifier  # noqa: E402

import ml_service as svc  # noqa: E402
from train_improved_models import POST_CONTACT_COLUMNS, SEED, preprocessor  # noqa: E402

warnings.filterwarnings("ignore")
FIG = ROOT / "docs" / "paper" / "figures"
RES = json.loads((ROOT / "ml" / "reports" / "improved" / "improved_results.json").read_text())
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "legend.fontsize": 7})
W = 3.4
SHORT = {"Logistic Regression": "LR", "Random Forest": "RF", "XGBoost": "XGB",
         "LightGBM": "LGBM", "CatBoost": "CatB", "XGBoost (Optuna-tuned)": "XGB-T",
         "LightGBM (Optuna-tuned)": "LGBM-T"}
out: dict = {}


def save(fig, name):
    fig.savefig(FIG / name, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


# ------------------------------------------------------------------ lead models
frame = svc.read_dataset()
numeric, categorical, _ = svc.resolve_features(frame, include_post_contact=True)
y = frame[svc.TARGET_COLUMN].astype(int)


def fit_eval(num, cat, params):
    x = frame[num + cat]
    x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.2, stratify=y, random_state=SEED)
    pipe = Pipeline([("pre", preprocessor(num, cat)),
                     ("model", XGBClassifier(**params, random_state=SEED, n_jobs=-1))]).fit(x_tr, y_tr)
    return pipe.predict_proba(x_te)[:, 1], y_te.to_numpy()


num_lf = [c for c in numeric if c not in POST_CONTACT_COLUMNS]
cat_lf = [c for c in categorical if c not in POST_CONTACT_COLUMNS]
p_full, y_te = fit_eval(numeric, categorical, RES["lead"][0]["tuned_params"]["XGBoost"])
p_lf, _ = fit_eval(num_lf, cat_lf, RES["lead"][1]["tuned_params"]["XGBoost"])

# calibration
fig, ax = plt.subplots(figsize=(W, 2.5))
for p, lab in ((p_full, "Full features"), (p_lf, "Leakage-free")):
    frac, mean = calibration_curve(y_te, p, n_bins=10, strategy="quantile")
    ax.plot(mean, frac, "o-", ms=3, lw=0.9, label=f"{lab} (Brier={brier_score_loss(y_te, p):.3f})")
ax.plot([0, 1], [0, 1], "k--", lw=0.5, label="Perfect calibration")
ax.set_xlabel("Mean predicted probability")
ax.set_ylabel("Observed conversion rate")
ax.legend(loc="upper left", frameon=False)
ax.grid(alpha=0.3, lw=0.4)
save(fig, "fig_calibration.png")
out["brier"] = {"full": float(brier_score_loss(y_te, p_full)), "leakage_free": float(brier_score_loss(y_te, p_lf))}

# capacity / top-k
base = float(y_te.mean())
topk = []
for k in (0.10, 0.20, 0.30, 0.40):
    n = int(round(k * len(p_lf)))
    idx = np.argsort(-p_lf)[:n]
    prec = float(y_te[idx].mean())
    topk.append({"k": k, "n": n, "precision": prec, "recall": float(y_te[idx].sum() / y_te.sum()),
                 "lift": prec / base})
out["topk_leakage_free"] = topk
out["test_base_rate"] = base

# confusion matrix (leakage-free tuned XGBoost, threshold 0.5)
cm = confusion_matrix(y_te, (p_lf >= 0.5).astype(int))
out["confusion_leakage_free"] = cm.tolist()
fig, ax = plt.subplots(figsize=(2.4, 2.1))
ax.imshow(cm / cm.sum(axis=1, keepdims=True), cmap="Blues", vmin=0, vmax=1)
for i in range(2):
    for j in range(2):
        r = cm[i, j] / cm[i].sum()
        ax.text(j, i, f"{cm[i, j]}\n({r:.1%})", ha="center", va="center", fontsize=7,
                color="white" if r > 0.6 else "black")
ax.set_xticks([0, 1], ["Not converted", "Converted"])
ax.set_yticks([0, 1], ["Not converted", "Converted"])
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
save(fig, "fig_confusion.png")

# CV error bars
full, lf = RES["lead"]
rows = [r for r in lf["rows"] if "cv" in r]
x = np.arange(len(rows))
fig, ax = plt.subplots(figsize=(W, 2.0))
for off, suite, lab, col in ((-0.2, full, "Full features", "#4c72b0"), (0.2, lf, "Leakage-free", "#dd8452")):
    vals = [next(r for r in suite["rows"] if r["model"] == m["model"])["cv"]["roc_auc"] for m in rows]
    ax.bar(x + off, [v["mean"] for v in vals], 0.4, yerr=[v["std"] for v in vals], capsize=2,
           color=col, label=lab, error_kw={"lw": 0.6})
ax.set_xticks(x, [SHORT[r["model"]] for r in rows])
ax.set_ylim(0.84, 1.0)
ax.set_ylabel("5-fold CV ROC-AUC")
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
ax.grid(axis="y", alpha=0.3, lw=0.4)
save(fig, "fig_cv_errorbars.png")

# channel conversion by lead source
src = frame.groupby("Lead Source")[svc.TARGET_COLUMN].agg(["mean", "size"]).sort_values("size", ascending=False)
src = src[src["size"] >= 50].head(8).sort_values("mean")
out["lead_source"] = {k: {"rate": float(v["mean"]), "n": int(v["size"])} for k, v in src.iterrows()}
fig, ax = plt.subplots(figsize=(W, 2.1))
ax.barh([f"{i} (n={int(r['size'])})" for i, r in src.iterrows()], src["mean"], color="#55a868")
ax.axvline(y.mean(), color="k", ls="--", lw=0.6)
ax.text(y.mean() + 0.01, -0.6, f"overall {y.mean():.1%}", fontsize=6)
ax.set_xlabel("Conversion rate")
ax.set_xlim(0, 1)
ax.grid(axis="x", alpha=0.3, lw=0.4)
save(fig, "fig_lead_source.png")

# K-Means segments with the platform's own function
pipe, _ = svc.load_pipeline()  # the served, leakage-free pipeline
served = [*svc.resolve_features(frame)[0], *svc.resolve_features(frame)[1]]
seg = svc.fit_segments(pipe, frame[served])
values, _ = svc.segment_features(pipe, frame[served])
scaled = seg["scaler"].transform(svc.segment_space(values))
labels = seg["kmeans"].labels_
rng = np.random.default_rng(SEED)
sample = rng.choice(len(scaled), size=min(4000, len(scaled)), replace=False)
out["silhouette"] = float(silhouette_score(scaled[sample], labels[sample]))
segs = []
for c in range(seg["k"]):
    m = labels == c
    segs.append({"name": seg["names"][c], "leads": int(m.sum()),
                 "visits": float(frame.loc[m, "TotalVisits"].median()),
                 "pages": float(frame.loc[m, "Page Views Per Visit"].median()),
                 "time": float(frame.loc[m, "Total Time Spent on Website"].median()),
                 "conv": float(y[m].mean()), "prob": seg["profile"][c]["mean_probability"]})
out["segments"] = sorted(segs, key=lambda s: ["Low Engagement", "Casual Browsers", "Engaged Prospects", "High Intent"].index(s["name"]))

# budget allocation example (same logic as backend/api/workspace.py::simulate)
camp = pd.read_excel(ROOT / "data" / "Marketing_Campaign_Data.xlsx", sheet_name="DATASET")
g = camp.groupby("Channel")[["Spend ($)", "Conversions"]].sum()
eff = (g["Conversions"] / g["Spend ($)"]).to_dict()
B = 100_000.0
names = list(eff)


def summarize(alloc):
    conv = sum(alloc[c] * eff[c] for c in names)
    return {"alloc": {c: round(alloc[c], 0) for c in names}, "conversions": conv, "cpa": B / conv}


scen = {"Equal split": summarize({c: B / len(names) for c in names}),
        "Efficiency-weighted": summarize({c: B * eff[c] / sum(eff.values()) for c in names})}
for cap in (0.4, 1.0):
    sol = linprog([-eff[c] for c in names], A_eq=[np.ones(len(names))], b_eq=[B],
                  bounds=[(0, B * cap)] * len(names), method="highs")
    scen[f"LP optimum (cap {int(cap * 100)}%)"] = summarize(dict(zip(names, sol.x)))
out["budget"] = {"budget": B, "efficiency": eff, "campaigns": int(len(camp)), "scenarios": scen}

# workflow diagram
steps = ["1. Import leads (CSV) and campaign spend", "2. Validate schema; drop identifiers and constants",
         "3. Leakage audit: remove post-contact attributes", "4. Impute, scale, one-hot encode (shared pipeline)",
         "5. Train and tune models (5-fold CV, Optuna)", "6. Score leads; TreeSHAP attributions",
         "7. K-Means engagement segments", "8. Channel analytics and budget scenarios (LP)",
         "9. Persist to SQLite; dashboard for human review"]
fig, ax = plt.subplots(figsize=(W, 3.3))
ax.set_xlim(0, 10)
ax.set_ylim(0, len(steps) * 1.1)
ax.axis("off")
for i, s in enumerate(steps):
    yy = (len(steps) - 1 - i) * 1.1
    ax.add_patch(FancyBboxPatch((0.3, yy + 0.1), 9.4, 0.7, boxstyle="round,pad=0.02,rounding_size=0.25",
                                fc="#f1ecfb" if i in (2, 4) else "#ffffff", ec="#333", lw=0.6))
    ax.text(5, yy + 0.45, s, ha="center", va="center", fontsize=6.6)
    if i:
        ax.annotate("", (5, yy + 0.8), (5, yy + 1.2), arrowprops=dict(arrowstyle="-|>", lw=0.6))
save(fig, "fig_workflow.png")

(FIG / "extra_results.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k not in ("budget",)}, indent=1))
print(json.dumps(out["budget"]["scenarios"], indent=1))
