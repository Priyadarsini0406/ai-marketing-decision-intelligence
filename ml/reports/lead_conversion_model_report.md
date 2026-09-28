# Decision-Intel Lead Conversion Model

Dataset: `Leads X Education.csv` (9240 rows, positive rate 0.3854)
Target: `Converted`
Estimator: `xgboost.XGBClassifier`

## Held-out performance (stratified 20% test split)

Model | Accuracy | Balanced | Precision | Recall | F1 | ROC-AUC
--- | --- | --- | --- | --- | --- | ---
XGBoost | 0.9318 | 0.9291 | 0.9069 | 0.9171 | 0.9120 | 0.9792
Logistic Regression | 0.9232 | 0.9178 | 0.9048 | 0.8947 | 0.8997 | 0.9712
Random Forest | 0.9291 | 0.9250 | 0.9086 | 0.9073 | 0.9079 | 0.9732
Gradient Boosting | 0.9318 | 0.9304 | 0.9014 | 0.9242 | 0.9126 | 0.9784

Majority-class baseline accuracy: 0.6147

## Confusion matrix (XGBoost)

```
[[1069, 67], [59, 653]]
```

## Features

Numeric (5): `TotalVisits`, `Total Time Spent on Website`, `Page Views Per Visit`, `Asymmetrique Activity Score`, `Asymmetrique Profile Score`

Categorical (24): `Lead Origin`, `Lead Source`, `Do Not Email`, `Do Not Call`, `Last Activity`, `Country`, `Specialization`, `How did you hear about X Education`, `What is your current occupation`, `What matters most to you in choosing a course`, `Search`, `Newspaper Article`, `X Education Forums`, `Newspaper`, `Digital Advertisement`, `Through Recommendations`, `Tags`, `Lead Quality`, `Lead Profile`, `City`, `Asymmetrique Activity Index`, `Asymmetrique Profile Index`, `A free copy of Mastering The Interview`, `Last Notable Activity`

Excluded identifiers: `Prospect ID`, `Lead Number`

Excluded constant columns: `Magazine`, `Receive More Updates About Our Courses`, `Update me on Supply Chain Content`, `Get updates on DM Content`, `I agree to pay the amount through cheque`

## Environment

- Python 3.14.7
- xgboost 3.4.1
- scikit-learn 1.9.1
- pandas 3.0.5