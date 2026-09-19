# Page coverage

The app retains one `/login` form. Admin accounts enter `/admin`; marketing
accounts enter `/dashboard`. Every workspace endpoint requires an active login.
Admin-only user management, dataset management, and system configuration remain
protected by the existing role check. Regular users can upload CSV/ZIP datasets.

| Requested page | Route | Available behavior |
| --- | --- | --- |
| Landing | `/` | Public navigation and product introduction |
| Login | `/login` | Shared login with role-aware routing |
| Register | `/register` | Non-admin account registration |
| Dashboard | `/dashboard` | Live lead/conversion/spend totals, channel data, exports, feature links |
| Lead Management | `/dashboard/leads` | Search, pagination, add/edit leads, inspect stored predictions |
| Conversion Prediction | `/dashboard/prediction` | Score stored leads with the saved gradient boosting pipeline |
| Explainable AI | `/dashboard/explainability` | SHAP feature contributions and baseline in log-odds |
| Customer Segmentation | `/dashboard/segmentation` | Standardized behavioral K-means clusters and aggregate profiles |
| Funnel Analysis | `/dashboard/funnel` | Nested lead/website-visit/conversion cohorts |
| Multi-Channel Attribution | `/dashboard/attribution` | Conversion share by recorded channel |
| Campaign Analytics | `/dashboard/campaigns` | Campaign-type spend and conversion aggregates |
| Budget Optimization | `/dashboard/optimization` | Constrained linear optimization, equal and efficiency-weighted proposals |
| What-If Simulator | `/dashboard/simulator` | Custom allocations, budget validation, historical-efficiency estimates |
| AI Recommendations | `/dashboard/recommendations` | Evidence-based campaign recommendations |
| Reports | `/dashboard/reports` | Marketing summary and campaign tables, JSON export |
| Settings | `/dashboard/settings` | Per-user currency label and compact spacing preferences |

Admin pages remain `/admin/users`, `/admin/datasets`, `/admin/configuration`,
and `/admin/reports`. Existing `/dashboard/analytics` and `/dashboard/budget`
remain available for saved channel metrics and saved budget scenarios.

## Data and model boundaries

- New live predictions use the saved model. The original imported leads were
  used in training, so their current-model scores are not held-out evaluations.
  Existing stored out-of-fold probabilities remain separate. Editing a lead
  clears its stale stored prediction; use the prediction page to rescore it.
- SHAP explains the current model's log-odds, not causal effects.
- Segmentation fits up to four clusters on visits, email clicks, prior purchases,
  and loyalty, using standardization and a fixed seed. Labels are descriptive
  cluster numbers; segmentation does not overwrite stored lead predictions.
- The dataset has a single channel per lead, with no ordered touchpoint history.
  Attribution therefore uses that recorded channel. Multi-touch attribution and
  temporal funnel drop-off cannot be computed from the available data.
- Budget optimization uses linear programming to maximize historical-efficiency
  estimates under the budget and a per-channel cap. Equal and efficiency-weighted
  heuristics are also available. This is not an RL policy. What-if results assume linear response without saturation or uplift.
  The page calculates scenarios without overwriting the saved scenario inventory.
- Recommendations use deterministic evidence rules, not an LLM.
- Preferences do not exchange currency values. Monetary source values remain as
  imported; the preferred currency is a display label on the overview dashboard.
- Uploaded files remain reviewable datasets and do not automatically become leads
  or trigger model training. Use the documented import/training command.

## Verification

Backend integration tests cover authentication, lead creation/editing, duplicate
IDs, per-user preference isolation, analytics, segmentation, simulation validation,
and existing admin/upload workflows. Browser tests cover every workspace route,
shared registration/login, live prediction, SHAP, scenario controls, preferences,
and report downloads. Model SHAP contributions were also checked numerically
against the predicted probability on an imported lead.
