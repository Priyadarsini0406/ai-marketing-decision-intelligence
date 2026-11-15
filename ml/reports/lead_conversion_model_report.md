# Decision-Intel Lead Conversion Model

Dataset: `Leads X Education.csv` (9240 rows, positive rate 0.3854)
Target: `Converted`
Estimator: `xgboost.XGBClassifier`

## Held-out performance (stratified 20% test split)

Model | Accuracy | Balanced | Precision | Recall | F1 | ROC-AUC
--- | --- | --- | --- | --- | --- | ---
XGBoost | 0.8182 | 0.8057 | 0.7709 | 0.7514 | 0.7610 | 0.8845
Logistic Regression | 0.7992 | 0.7806 | 0.7603 | 0.6994 | 0.7286 | 0.8698
Random Forest | 0.8041 | 0.7867 | 0.7644 | 0.7107 | 0.7365 | 0.8746
Gradient Boosting | 0.8198 | 0.8091 | 0.7680 | 0.7626 | 0.7653 | 0.8832

Majority-class baseline accuracy: 0.6147

## Confusion matrix (XGBoost)

```
[[977, 159], [177, 535]]
```

## Features

Numeric (3): `TotalVisits`, `Total Time Spent on Website`, `Page Views Per Visit`

Categorical (19): `Lead Origin`, `Lead Source`, `Do Not Email`, `Do Not Call`, `Last Activity`, `Country`, `Specialization`, `How did you hear about X Education`, `What is your current occupation`, `What matters most to you in choosing a course`, `Search`, `Newspaper Article`, `X Education Forums`, `Newspaper`, `Digital Advertisement`, `Through Recommendations`, `City`, `A free copy of Mastering The Interview`, `Last Notable Activity`

Excluded identifiers: `Prospect ID`, `Lead Number`

Excluded constant columns: `Magazine`, `Receive More Updates About Our Courses`, `Update me on Supply Chain Content`, `Get updates on DM Content`, `I agree to pay the amount through cheque`

## Environment

- Python 3.14.7
- xgboost 3.4.1
- scikit-learn 1.9.1
- pandas 3.0.5