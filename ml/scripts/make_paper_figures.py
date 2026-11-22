"""Column-width (3.4 in) figures for the IEEE paper, built from improved_results.json.

    python ml/scripts/make_paper_figures.py
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
import shap  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from sklearn.metrics import roc_auc_score, roc_curve  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from lightgbm import LGBMClassifier  # noqa: E402
from xgboost import XGBClassifier  # noqa: E402

import ml_service as svc  # noqa: E402
from train_improved_models import POST_CONTACT_COLUMNS, SEED, base_models, preprocessor  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT / "docs" / "paper" / "figures"
RES = json.loads((ROOT / "ml" / "reports" / "improved" / "improved_results.json").read_text())

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7})
W = 3.4
SHORT = {"Logistic Regression": "LR", "Random Forest": "RF", "XGBoost": "XGB",
         "LightGBM": "LGBM", "CatBoost": "CatB", "Stacking (RF+XGB+LGBM+Cat)": "Stack",
         "XGBoost (Optuna-tuned)": "XGB-T", "LightGBM (Optuna-tuned)": "LGBM-T"}


def save(fig, name):
    fig.savefig(OUT / name, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def architecture():
    fig, ax = plt.subplots(figsize=(W, 3.0))
    ax.set_xlim(-0.2, 10.2)
    ax.set_ylim(-0.1, 10.4)
    ax.axis("off")

    def box(x, y, w, h, title, sub, fc, size=7):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.15",
                                    fc=fc, ec="#333333", lw=0.6))
        ax.text(x + w / 2, y + h * 0.63, title, ha="center", va="center", fontsize=size, weight="bold")
        ax.text(x + w / 2, y + h * 0.27, sub, ha="center", va="center", fontsize=5.6 if size == 7 else 4.6)

    def arrow(x1, y1, x2, y2, label=""):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", lw=0.6, color="#333"))
        if label:
            ax.text((x1 + x2) / 2 + 0.15, (y1 + y2) / 2, label, fontsize=5.2, va="center")

    box(2.5, 9.2, 5, 1.0, "Admissions / Marketing Staff", "review leads, plan campaigns", "#ffffff")
    box(1.0, 7.5, 8, 1.0, "SvelteKit Frontend", "dashboards: scores, explanations, segments, scenarios", "#e8eefc")
    box(1.0, 5.8, 8, 1.0, "FastAPI Backend", "authentication, validation, REST services", "#e6f5ef")
    box(0.0, 3.6, 2.4, 1.4, "Conversion Model", "leakage-free\nXGBoost (served)", "#f1ecfb", 5.3)
    box(2.55, 3.6, 2.4, 1.4, "SHAP Explainer", "per-lead feature\nattributions", "#f1ecfb", 5.3)
    box(5.1, 3.6, 2.4, 1.4, "K-Means Segments", "four engagement\ngroups", "#f1ecfb", 5.3)
    box(7.65, 3.6, 2.4, 1.4, "Admission Assistant", "grounded chatbot over\nscores and SHAP", "#fbeee6", 5.3)
    box(0.0, 1.6, 4.9, 1.2, "SQLite Store", "leads, predictions, datasets, scenarios", "#eef6e9")
    box(5.1, 1.6, 4.9, 1.2, "Channel Analytics & Scenarios", "constant-efficiency what-if planning", "#fdf5e3")
    box(1.5, 0.0, 7, 1.0, "Decision-Support Dashboard", "human review of all outputs", "#dfe3ea")
    arrow(5, 9.2, 5, 8.5, "HTTPS")
    arrow(5, 7.5, 5, 6.8, "REST")
    for x in (1.2, 3.75, 6.3, 8.85):
        arrow(5, 5.8, x, 5.0)
    arrow(1.2, 3.6, 1.2, 2.8)
    arrow(6.3, 3.6, 6.3, 2.8)
    arrow(5, 1.6, 5, 1.0)
    save(fig, "fig1_architecture.png")


def lead_auc():
    full, lf = RES["lead"]
    names = [r["model"] for r in full["rows"]]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(W, 2.1))
    a = [r["test"]["roc_auc"] for r in full["rows"]]
    b = [next(r for r in lf["rows"] if r["model"] == n)["test"]["roc_auc"] for n in names]
    ax.bar(x - 0.2, a, 0.4, label="Full features", color="#4c72b0")
    ax.bar(x + 0.2, b, 0.4, label="Leakage-free features", color="#dd8452")
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[n] for n in names], rotation=30, ha="right")
    ax.set_ylim(min(b) - 0.04, 1.0)
    ax.set_ylabel("ROC-AUC (held-out)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False, ncol=2)
    ax.grid(axis="y", alpha=0.3, lw=0.4)
    save(fig, "fig2_lead_auc.png")


def lead_roc_and_shap():
    frame = svc.read_dataset()
    numeric, categorical, _ = svc.resolve_features(frame, include_post_contact=True)
    num = [c for c in numeric if c not in POST_CONTACT_COLUMNS]
    cat = [c for c in categorical if c not in POST_CONTACT_COLUMNS]
    x = frame[num + cat]
    y = frame[svc.TARGET_COLUMN].astype(int)
    x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.2, stratify=y, random_state=SEED)
    lf = RES["lead"][1]
    params = lf["tuned_params"]
    models = base_models(2)
    chosen = {"LR": models["Logistic Regression"], "RF": models["Random Forest"],
              "XGB": models["XGBoost"]}
    if "LightGBM" in params:
        chosen["LGBM-T"] = LGBMClassifier(**params["LightGBM"], subsample_freq=1,
                                          random_state=SEED, n_jobs=-1, verbose=-1)
    if "XGBoost" in params:
        chosen["XGB-T"] = XGBClassifier(**params["XGBoost"], random_state=SEED, n_jobs=-1)
    fig, ax = plt.subplots(figsize=(W, 2.6))
    fitted = {}
    for name, model in chosen.items():
        pipe = Pipeline([("pre", preprocessor(num, cat)), ("model", model)]).fit(x_tr, y_tr)
        fitted[name] = pipe
        p = pipe.predict_proba(x_te)[:, 1]
        fpr, tpr, _ = roc_curve(y_te, p)
        ax.plot(fpr, tpr, lw=0.9, label=f"{name} (AUC={roc_auc_score(y_te, p):.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=0.5)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.legend(loc="lower right", frameon=False)
    ax.grid(alpha=0.3, lw=0.4)
    save(fig, "fig3_lead_roc_leakage_free.png")

    # SHAP on the tuned XGBoost (fallback: default XGBoost), aggregated to source features
    pipe = fitted.get("XGB-T", fitted["XGB"])
    pre, model = pipe.named_steps["pre"], pipe.named_steps["model"]
    xt = pre.transform(x_te)
    sv = shap.TreeExplainer(model).shap_values(xt)
    names = pre.get_feature_names_out()
    source = []
    for n in names:
        kind, rest = n.split("__", 1)
        if kind == "num":
            source.append(rest)
        else:
            source.append(next(c for c in sorted(cat, key=len, reverse=True) if rest.startswith(c)))
    imp = {}
    for j, s in enumerate(source):
        imp[s] = imp.get(s, 0) + float(np.abs(sv[:, j]).mean())
    top = sorted(imp.items(), key=lambda kv: kv[1])[-10:]
    fig, ax = plt.subplots(figsize=(W, 2.4))
    ax.barh([t[0] for t in top], [t[1] for t in top], color="#4c72b0")
    ax.set_xlabel("Mean |SHAP value| (log-odds)")
    ax.grid(axis="x", alpha=0.3, lw=0.4)
    save(fig, "fig4_shap_leakage_free.png")
    (OUT / "shap_top_features.json").write_text(json.dumps(top[::-1], indent=1))


def student_f1():
    suites = RES["student"][:3]
    labels = ["No balancing", "Class weights", "SMOTE"]
    classes = RES["student_classes"]
    fig, ax = plt.subplots(figsize=(W, 2.1))
    x = np.arange(len(classes))
    for i, (s, lab) in enumerate(zip(suites, labels)):
        best = max(s["rows"], key=lambda r: r["test"]["f1"])
        ax.bar(x + (i - 1) * 0.26, best["test"]["f1_per_class"], 0.26,
               label=f"{lab} ({SHORT[best['model']]})")
    ax.set_xticks(x)
    ax.set_xticklabels(classes)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Per-class F1 (held-out)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False, ncol=3, fontsize=6)
    ax.grid(axis="y", alpha=0.3, lw=0.4)
    save(fig, "fig5_student_f1.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture()
    lead_auc()
    lead_roc_and_shap()
    student_f1()
