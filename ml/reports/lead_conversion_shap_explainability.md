# Explainable Lead Conversion Prediction (Decision-Intel)

## Model used
- Model type: XGBClassifier
- Selected model during training: XGBoost
- Saved artifacts: `lead_conversion_model.pkl`, `lead_preprocessor.pkl`

## Preprocessing pipeline
- Numeric: median imputation + StandardScaler
- Categorical: 'Select' -> 'Not Selected', missing -> 'Missing', OneHotEncoder(handle_unknown='ignore')
- Input features: 18
- Transformed features: 153
- Train/test split (80/20 stratified, random_state=42) done before transformations; no leakage

## SHAP method
- Explainer: SHAP TreeExplainer on the trained model over the preprocessed feature space
- Values are for the positive (converted) class.

## Global feature importance (top 10)
- Total Time Spent on Website: 1.107412
- Asymmetrique Activity Score: 0.504318
- What is your current occupation_Missing: 0.397209
- Last Notable Activity_SMS Sent: 0.382818
- What is your current occupation_Working Professional: 0.296289
- Last Activity_SMS Sent: 0.286100
- Lead Origin_Lead Add Form: 0.276261
- Page Views Per Visit: 0.276155
- TotalVisits: 0.201304
- Last Activity_Olark Chat Conversation: 0.180120

## Individual explanations
### Representative lead - High tier (dataset row 1)
- Conversion probability: 0.7865
- Base value: 0.0598
- Important positive factors:
  - Asymmetrique Activity Score: 1.7078
  - Last Activity_SMS Sent: 0.6447
  - Page Views Per Visit: 0.5068
  - What is your current occupation_Missing: 0.2755
  - Lead Origin_Landing Page Submission: 0.1594
- Important negative factors:
  - Total Time Spent on Website: -0.4153
  - Specialization_Not Selected: -0.3951
  - City_Not Selected: -0.3788
  - Lead Source_Olark Chat: -0.3124
  - Last Notable Activity_SMS Sent: -0.2935
- Feature contributions:
  - Asymmetrique Activity Score: 1.7078
  - Last Activity_SMS Sent: 0.6447
  - Page Views Per Visit: 0.5068
  - Total Time Spent on Website: -0.4153
  - Specialization_Not Selected: -0.3951
  - City_Not Selected: -0.3788
  - Lead Source_Olark Chat: -0.3124
  - Last Notable Activity_SMS Sent: -0.2935
  - What is your current occupation_Missing: 0.2755
  - Lead Origin_Lead Add Form: -0.2152

### Representative lead - Medium tier (dataset row 0)
- Conversion probability: 0.6705
- Base value: 0.0598
- Important positive factors:
  - Total Time Spent on Website: 1.7437
  - Asymmetrique Activity Score: 0.8153
  - TotalVisits: 0.3289
  - Lead Source_Referral Sites: 0.3066
  - Last Notable Activity_Modified: 0.1881
- Important negative factors:
  - What is your current occupation_Missing: -0.9617
  - Last Activity_Page Visited on Website: -0.7144
  - Last Notable Activity_SMS Sent: -0.3502
  - Asymmetrique Profile Score: -0.2791
  - Page Views Per Visit: -0.2187
- Feature contributions:
  - Total Time Spent on Website: 1.7437
  - What is your current occupation_Missing: -0.9617
  - Asymmetrique Activity Score: 0.8153
  - Last Activity_Page Visited on Website: -0.7144
  - Last Notable Activity_SMS Sent: -0.3502
  - TotalVisits: 0.3289
  - Lead Source_Referral Sites: 0.3066
  - Asymmetrique Profile Score: -0.2791
  - Page Views Per Visit: -0.2187
  - Last Notable Activity_Modified: 0.1881

### Representative lead - Low tier (dataset row 2)
- Conversion probability: 0.3535
- Base value: 0.0598
- Important positive factors:
  - Last Notable Activity_SMS Sent: 0.8380
  - Last Activity_SMS Sent: 0.4935
  - City_Other Metro Cities: 0.1294
  - Specialization_Not Selected: 0.1167
  - What is your current occupation_Missing: 0.1105
- Important negative factors:
  - Total Time Spent on Website: -1.0021
  - TotalVisits: -0.6062
  - Lead Source_Direct Traffic: -0.2099
  - Lead Origin_Lead Add Form: -0.2004
  - What is your current occupation_Working Professional: -0.1851
- Feature contributions:
  - Total Time Spent on Website: -1.0021
  - Last Notable Activity_SMS Sent: 0.8380
  - TotalVisits: -0.6062
  - Last Activity_SMS Sent: 0.4935
  - Lead Source_Direct Traffic: -0.2099
  - Lead Origin_Lead Add Form: -0.2004
  - What is your current occupation_Working Professional: -0.1851
  - Lead Origin_Landing Page Submission: -0.1759
  - A free copy of Mastering The Interview_No: -0.1320
  - City_Other Metro Cities: 0.1294

## Limitations
- SHAP values explain model predictions, not causal effects.
- Excluded features (identifiers, constants, and post-hoc labels like Tags /
  Lead Quality / Lead Profile) would leak the outcome and are not modeled.