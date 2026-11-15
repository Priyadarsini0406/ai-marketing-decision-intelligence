"""Improved experiments for the Decision-Intel paper.

    python ml/scripts/train_improved_models.py

Lead conversion (Leads X Education):
  * Two feature sets: FULL (as served today) and LEAKAGE-FREE, which removes
    sales-assigned, post-contact columns (Tags, Lead Quality, Lead Profile,
    Asymmetrique indices/scores) that are not known when a lead first arrives.
  * Models: LR, RF, XGBoost, LightGBM, CatBoost, tuned XGBoost/LightGBM (Optuna)
    and a stacking ensemble.
  * 5-fold stratified CV on the training split (mean +/- std) plus the held-out
    20% test split.

Student outcome (3-class):
  * Same model family, plus imbalance handling (class weights vs. SMOTE).
  * Early-warning variant that uses only enrolment + 1st-semester information.

Outputs: ml/reports/improved/  (results JSON, markdown report, figures)
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "ml" / "scripts"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import optuna  # noqa: E402
import pandas as pd  # noqa: E402
from catboost import CatBoostClassifier  # noqa: E402
from imblearn.over_sampling import SMOTE  # noqa: E402
from imblearn.pipeline import Pipeline as ImbPipeline  # noqa: E402
from lightgbm import LGBMClassifier  # noqa: E402
from sklearn.base import clone  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.ensemble import RandomForestClassifier, StackingClassifier  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: E402
from xgboost import XGBClassifier  # noqa: E402

import ml_service as svc  # noqa: E402

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

SEED = 42
OUT = PROJECT_ROOT / "ml" / "reports" / "improved"
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
OPTUNA_TRIALS = 20

POST_CONTACT_COLUMNS = [
    "Tags", "Lead Quality", "Lead Profile",
    "Asymmetrique Activity Index", "Asymmetrique Profile Index",
    "Asymmetrique Activity Score", "Asymmetrique Profile Score",
]

STUDENT_DATA = PROJECT_ROOT / "old_data.csv"
STUDENT_CATEGORICAL = [
    "Marital status", "Application mode", "Course", "Daytime/evening attendance\t",
    "Previous qualification", "Nacionality", "Mother's qualification",
    "Father's qualification", "Mother's occupation", "Father's occupation",
    "Displaced", "Educational special needs", "Debtor", "Tuition fees up to date",
    "Gender", "Scholarship holder", "International",
]


# --------------------------------------------------------------------------- helpers
def preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), numeric),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore", min_frequency=5,
                                               sparse_output=False))]), categorical),
    ])


def base_models(n_classes: int, balanced: bool = False) -> dict:
    cw = "balanced" if balanced else None
    multi = n_classes > 2
    return {
        "Logistic Regression": LogisticRegression(max_iter=5000, class_weight=cw, random_state=SEED),
        "Random Forest": RandomForestClassifier(n_estimators=300, class_weight=cw,
                                                n_jobs=-1, random_state=SEED),
        "XGBoost": XGBClassifier(n_estimators=400, max_depth=4, learning_rate=0.08,
                                 subsample=0.9, colsample_bytree=0.9, random_state=SEED,
                                 n_jobs=-1, eval_metric="mlogloss" if multi else "logloss"),
        "LightGBM": LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                                   class_weight=cw, random_state=SEED, n_jobs=-1, verbose=-1),
        "CatBoost": CatBoostClassifier(iterations=300, depth=6, learning_rate=0.1,
                                       auto_class_weights="Balanced" if balanced else None,
                                       random_seed=SEED, verbose=0, thread_count=-1),
    }


def stacking(models: dict) -> StackingClassifier:
    return StackingClassifier(
        estimators=[("rf", clone(models["Random Forest"])),
                    ("xgb", clone(models["XGBoost"])),
                    ("lgbm", clone(models["LightGBM"])),
                    ("cat", clone(models["CatBoost"]))],
        final_estimator=LogisticRegression(max_iter=5000),
        cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED),
        stack_method="predict_proba", n_jobs=1,
    )


def test_metrics(pipe, x_test, y_test, n_classes: int) -> dict:
    proba = pipe.predict_proba(x_test)
    pred = pipe.predict(x_test)
    if n_classes == 2:
        auc = roc_auc_score(y_test, proba[:, 1])
        avg = "binary"
    else:
        auc = roc_auc_score(y_test, proba, multi_class="ovr", average="macro")
        avg = "macro"
    out = {
        "accuracy": accuracy_score(y_test, pred),
        "balanced_accuracy": balanced_accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, average=avg, zero_division=0),
        "recall": recall_score(y_test, pred, average=avg, zero_division=0),
        "f1": f1_score(y_test, pred, average=avg, zero_division=0),
        "roc_auc": auc,
    }
    if n_classes > 2:
        out["f1_per_class"] = f1_score(y_test, pred, average=None).tolist()
    return {k: (float(v) if not isinstance(v, list) else v) for k, v in out.items()}


def cv_metrics(pipe, x, y, n_classes: int) -> dict:
    scoring = ({"f1": "f1", "roc_auc": "roc_auc", "accuracy": "accuracy"} if n_classes == 2 else
               {"f1": "f1_macro", "roc_auc": "roc_auc_ovr", "accuracy": "accuracy"})
    res = cross_validate(pipe, x, y, cv=CV, scoring=scoring, n_jobs=1)
    return {k: {"mean": float(res[f"test_{k}"].mean()), "std": float(res[f"test_{k}"].std())}
            for k in scoring}


def tune(kind: str, pre, x, y, n_classes: int):
    """Optuna search (3-fold CV on training data only)."""
    scoring = "roc_auc" if n_classes == 2 else "f1_macro"
    inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)

    def build(trial):
        if kind == "XGBoost":
            return XGBClassifier(
                n_estimators=trial.suggest_int("n_estimators", 200, 900, step=100),
                max_depth=trial.suggest_int("max_depth", 3, 8),
                learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                subsample=trial.suggest_float("subsample", 0.6, 1.0),
                colsample_bytree=trial.suggest_float("colsample_bytree", 0.5, 1.0),
                min_child_weight=trial.suggest_int("min_child_weight", 1, 10),
                reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 10, log=True),
                tree_method="hist", random_state=SEED, n_jobs=-1)
        return LGBMClassifier(
            n_estimators=trial.suggest_int("n_estimators", 200, 900, step=100),
            num_leaves=trial.suggest_int("num_leaves", 15, 127),
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            subsample=trial.suggest_float("subsample", 0.6, 1.0), subsample_freq=1,
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.5, 1.0),
            min_child_samples=trial.suggest_int("min_child_samples", 5, 60),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 10, log=True),
            class_weight="balanced" if n_classes > 2 else None,
            random_state=SEED, n_jobs=-1, verbose=-1)

    def objective(trial):
        pipe = Pipeline([("pre", clone(pre)), ("model", build(trial))])
        return cross_validate(pipe, x, y, cv=inner, scoring=scoring)["test_score"].mean()

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED))
    study.optimize(objective, n_trials=OPTUNA_TRIALS, callbacks=[
        lambda st, tr: print(f"    {kind} trial {tr.number + 1}/{OPTUNA_TRIALS} "
                             f"score={tr.value:.4f} best={st.best_value:.4f}", flush=True)])
    return build(optuna.trial.FixedTrial(study.best_params)), study.best_params


def run_suite(title, x, y, numeric, categorical, n_classes, balanced=False,
              smote=False, do_tune=True, do_cv=True):
    print(f"\n=== {title}  rows={len(x)} num={len(numeric)} cat={len(categorical)}", flush=True)
    x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.2, stratify=y, random_state=SEED)
    pre = preprocessor(numeric, categorical)
    models = base_models(n_classes, balanced)
    models["Stacking (RF+XGB+LGBM+Cat)"] = stacking(models)
    tuned_params = {}
    if do_tune:
        for kind in ("XGBoost", "LightGBM"):
            t0 = time.time()
            est, params = tune(kind, pre, x_tr, y_tr, n_classes)
            models[f"{kind} (Optuna-tuned)"] = est
            tuned_params[kind] = params
            print(f"  tuned {kind} in {time.time() - t0:.0f}s", flush=True)

    rows, rocs = [], {}
    for name, model in models.items():
        t0 = time.time()
        steps = [("pre", clone(pre))]
        if smote:
            steps.append(("smote", SMOTE(random_state=SEED)))
        steps.append(("model", model))
        pipe = (ImbPipeline if smote else Pipeline)(steps)
        row = {"model": name}
        if do_cv and not name.startswith("Stacking"):
            row["cv"] = cv_metrics(pipe, x_tr, y_tr, n_classes)
        pipe.fit(x_tr, y_tr)
        row["test"] = test_metrics(pipe, x_te, y_te, n_classes)
        if n_classes == 2:
            rocs[name] = roc_curve(y_te, pipe.predict_proba(x_te)[:, 1])[:2]
        rows.append(row)
        print(f"  {name:32s} F1={row['test']['f1']:.4f} AUC={row['test']['roc_auc']:.4f} "
              f"({time.time() - t0:.0f}s)", flush=True)
    return {"title": title, "rows": rows, "tuned_params": tuned_params,
            "n_train": len(x_tr), "n_test": len(x_te)}, rocs


# --------------------------------------------------------------------------- figures
def plot_bars(suites: list[dict], metric: str, fname: str, ylabel: str):
    names = [r["model"] for r in suites[0]["rows"]]
    width = 0.8 / len(suites)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for i, s in enumerate(suites):
        vals = [next(r for r in s["rows"] if r["model"] == n)["test"][metric] for n in names]
        bars = ax.bar(np.arange(len(names)) + i * width, vals, width, label=s["title"])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.004, f"{v:.3f}", ha="center",
                    fontsize=6.5, rotation=90)
    ax.set_xticks(np.arange(len(names)) + width * (len(suites) - 1) / 2)
    ax.set_xticklabels(names, rotation=25, ha="right", fontsize=8)
    lo = min(r["test"][metric] for s in suites for r in s["rows"])
    ax.set_ylim(max(0, lo - 0.08), 1.0)
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=300)
    plt.close(fig)


def plot_roc(rocs: dict, fname: str, title: str):
    fig, ax = plt.subplots(figsize=(5.5, 5))
    for name, (fpr, tpr) in rocs.items():
        ax.plot(fpr, tpr, lw=1.3, label=name)
    ax.plot([0, 1], [0, 1], "k--", lw=0.8)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=300)
    plt.close(fig)


# --------------------------------------------------------------------------- report
def table(suite: dict, n_classes: int) -> str:
    has_cv = "cv" in suite["rows"][0]
    head = "Model | Acc | Bal.Acc | Prec | Rec | F1 | ROC-AUC"
    if has_cv:
        head += " | CV F1 (mean±std) | CV AUC (mean±std)"
    if n_classes > 2:
        head += " | F1 Dropout / Enrolled / Graduate"
    lines = [f"### {suite['title']}  (train={suite['n_train']}, test={suite['n_test']})", "",
             head, " | ".join(["---"] * (head.count("|") + 1))]
    for r in suite["rows"]:
        t = r["test"]
        cells = [r["model"]] + [f"{t[k]:.4f}" for k in
                                ("accuracy", "balanced_accuracy", "precision", "recall", "f1", "roc_auc")]
        if has_cv and "cv" not in r:
            cells += ["held-out only", "held-out only"]
        elif has_cv:
            cells += [f"{r['cv']['f1']['mean']:.4f} ± {r['cv']['f1']['std']:.4f}",
                      f"{r['cv']['roc_auc']['mean']:.4f} ± {r['cv']['roc_auc']['std']:.4f}"]
        if n_classes > 2:
            cells.append(" / ".join(f"{v:.3f}" for v in t["f1_per_class"]))
        lines.append(" | ".join(cells))
    if suite["tuned_params"]:
        lines += ["", "Optuna best parameters:", "```",
                  json.dumps(suite["tuned_params"], indent=1), "```"]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.time()

    # ---------------- lead conversion
    lead = svc.read_dataset()
    numeric, categorical, _ = svc.resolve_features(lead, include_post_contact=True)
    y_lead = lead[svc.TARGET_COLUMN].astype(int)
    full, full_rocs = run_suite("Lead - full features", lead[numeric + categorical], y_lead,
                                numeric, categorical, 2)
    num_lf = [c for c in numeric if c not in POST_CONTACT_COLUMNS]
    cat_lf = [c for c in categorical if c not in POST_CONTACT_COLUMNS]
    lf, lf_rocs = run_suite("Lead - leakage-free features", lead[num_lf + cat_lf], y_lead,
                            num_lf, cat_lf, 2)
    plot_bars([full, lf], "roc_auc", "lead_auc_comparison.png", "ROC-AUC (held-out)")
    plot_bars([full, lf], "f1", "lead_f1_comparison.png", "F1 (held-out)")
    plot_roc(full_rocs, "lead_roc_full.png", "ROC - lead conversion (full features)")
    plot_roc(lf_rocs, "lead_roc_leakage_free.png", "ROC - lead conversion (leakage-free)")

    # ---------------- student outcome
    stu = pd.read_csv(STUDENT_DATA, sep=";")
    stu.columns = [c.lstrip("﻿") for c in stu.columns]
    classes = sorted(stu["Target"].unique())
    y_stu = stu["Target"].map({c: i for i, c in enumerate(classes)})
    feats = [c for c in stu.columns if c != "Target"]
    s_cat = [c for c in STUDENT_CATEGORICAL if c in feats]
    s_num = [c for c in feats if c not in s_cat]
    stu_base, _ = run_suite("Student - no imbalance handling", stu[feats], y_stu, s_num, s_cat, 3,
                            do_tune=False)
    stu_cw, _ = run_suite("Student - class weights", stu[feats], y_stu, s_num, s_cat, 3,
                          balanced=True, do_tune=True)
    stu_sm, _ = run_suite("Student - SMOTE", stu[feats], y_stu, s_num, s_cat, 3,
                          smote=True, do_tune=False)
    early = [c for c in feats if "2nd sem" not in c]
    stu_early, _ = run_suite("Student - early warning (1st sem only, class weights)",
                             stu[early], y_stu, [c for c in s_num if c in early], s_cat, 3,
                             balanced=True, do_tune=False)
    plot_bars([stu_base, stu_cw, stu_sm], "f1", "student_macro_f1_comparison.png",
              "Macro F1 (held-out)")

    results = {"lead": [full, lf], "student": [stu_base, stu_cw, stu_sm, stu_early],
               "student_classes": classes, "post_contact_columns": POST_CONTACT_COLUMNS}
    (OUT / "improved_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    md = ["# Decision-Intel - Improved Experiments", "",
          f"Seed {SEED}; stratified 80/20 split; 5-fold stratified CV on the training split; "
          f"(stacking: held-out only, 3-fold internal stacking CV); Optuna TPE, {OPTUNA_TRIALS} trials, 3-fold inner CV on training data only.", "",
          "Leakage-free set removes post-contact columns: " + ", ".join(POST_CONTACT_COLUMNS), "",
          "## Lead conversion", "", table(full, 2), table(lf, 2),
          "## Student outcome", f"Classes: {classes}", "",
          table(stu_base, 3), table(stu_cw, 3), table(stu_sm, 3), table(stu_early, 3),
          f"\nTotal runtime: {(time.time() - started) / 60:.1f} min\n"]
    (OUT / "improved_report.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nSaved to {OUT}  ({(time.time() - started) / 60:.1f} min)")


if __name__ == "__main__":
    main()
