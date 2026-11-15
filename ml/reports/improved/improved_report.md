# Decision-Intel - Improved Experiments

Seed 42; stratified 80/20 split; 5-fold stratified CV on the training split; (stacking: held-out only, 3-fold internal stacking CV); Optuna TPE, 20 trials, 3-fold inner CV on training data only.

Leakage-free set removes post-contact columns: Tags, Lead Quality, Lead Profile, Asymmetrique Activity Index, Asymmetrique Profile Index, Asymmetrique Activity Score, Asymmetrique Profile Score

## Lead conversion

### Lead - full features  (train=7392, test=1848)

Model | Acc | Bal.Acc | Prec | Rec | F1 | ROC-AUC | CV F1 (mean±std) | CV AUC (mean±std)
--- | --- | --- | --- | --- | --- | --- | --- | ---
Logistic Regression | 0.9280 | 0.9234 | 0.9095 | 0.9031 | 0.9063 | 0.9714 | 0.8991 ± 0.0062 | 0.9746 ± 0.0034
Random Forest | 0.9324 | 0.9282 | 0.9140 | 0.9101 | 0.9120 | 0.9742 | 0.9091 ± 0.0046 | 0.9758 ± 0.0026
XGBoost | 0.9356 | 0.9327 | 0.9135 | 0.9199 | 0.9167 | 0.9800 | 0.9142 ± 0.0044 | 0.9806 ± 0.0026
LightGBM | 0.9361 | 0.9339 | 0.9114 | 0.9242 | 0.9177 | 0.9799 | 0.9132 ± 0.0072 | 0.9786 ± 0.0029
CatBoost | 0.9378 | 0.9352 | 0.9152 | 0.9242 | 0.9196 | 0.9797 | 0.9135 ± 0.0031 | 0.9806 ± 0.0026
Stacking (RF+XGB+LGBM+Cat) | 0.9356 | 0.9335 | 0.9101 | 0.9242 | 0.9171 | 0.9800 | held-out only | held-out only
XGBoost (Optuna-tuned) | 0.9351 | 0.9336 | 0.9066 | 0.9270 | 0.9167 | 0.9811 | 0.9186 ± 0.0047 | 0.9815 ± 0.0022
LightGBM (Optuna-tuned) | 0.9345 | 0.9336 | 0.9031 | 0.9298 | 0.9163 | 0.9808 | 0.9170 ± 0.0034 | 0.9810 ± 0.0025

Optuna best parameters:
```
{
 "XGBoost": {
  "n_estimators": 800,
  "max_depth": 6,
  "learning_rate": 0.010871004121020735,
  "subsample": 0.7669703848095651,
  "colsample_bytree": 0.7647788018228402,
  "min_child_weight": 1,
  "reg_lambda": 0.060259281300000266
 },
 "LightGBM": {
  "n_estimators": 600,
  "num_leaves": 15,
  "learning_rate": 0.013688329189968013,
  "subsample": 0.8481620475610542,
  "colsample_bytree": 0.5497267775979738,
  "min_child_samples": 5,
  "reg_lambda": 0.06266988450213364
 }
}
```

### Lead - leakage-free features  (train=7392, test=1848)

Model | Acc | Bal.Acc | Prec | Rec | F1 | ROC-AUC | CV F1 (mean±std) | CV AUC (mean±std)
--- | --- | --- | --- | --- | --- | --- | --- | ---
Logistic Regression | 0.7998 | 0.7811 | 0.7615 | 0.6994 | 0.7291 | 0.8693 | 0.7474 ± 0.0159 | 0.8926 ± 0.0052
Random Forest | 0.8057 | 0.7880 | 0.7678 | 0.7107 | 0.7381 | 0.8758 | 0.7646 ± 0.0165 | 0.8965 ± 0.0047
XGBoost | 0.8214 | 0.8094 | 0.7744 | 0.7570 | 0.7656 | 0.8859 | 0.7745 ± 0.0111 | 0.9040 ± 0.0030
LightGBM | 0.8139 | 0.7998 | 0.7690 | 0.7388 | 0.7536 | 0.8802 | 0.7714 ± 0.0110 | 0.8986 ± 0.0047
CatBoost | 0.8290 | 0.8179 | 0.7829 | 0.7697 | 0.7762 | 0.8861 | 0.7749 ± 0.0126 | 0.9020 ± 0.0052
Stacking (RF+XGB+LGBM+Cat) | 0.8171 | 0.8030 | 0.7742 | 0.7416 | 0.7575 | 0.8876 | held-out only | held-out only
XGBoost (Optuna-tuned) | 0.8247 | 0.8149 | 0.7725 | 0.7725 | 0.7725 | 0.8868 | 0.7799 ± 0.0122 | 0.9055 ± 0.0033
LightGBM (Optuna-tuned) | 0.8225 | 0.8140 | 0.7659 | 0.7767 | 0.7713 | 0.8874 | 0.7806 ± 0.0118 | 0.9057 ± 0.0030

Optuna best parameters:
```
{
 "XGBoost": {
  "n_estimators": 300,
  "max_depth": 4,
  "learning_rate": 0.029967309097101588,
  "subsample": 0.7824279936868144,
  "colsample_bytree": 0.8925879806965068,
  "min_child_weight": 2,
  "reg_lambda": 0.11400863701127326
 },
 "LightGBM": {
  "n_estimators": 400,
  "num_leaves": 15,
  "learning_rate": 0.01553238254904497,
  "subsample": 0.9353867075126997,
  "colsample_bytree": 0.587286079037248,
  "min_child_samples": 5,
  "reg_lambda": 2.104574244892657
 }
}
```

## Student outcome
Classes: ['Dropout', 'Enrolled', 'Graduate']

### Student - no imbalance handling  (train=3539, test=885)

Model | Acc | Bal.Acc | Prec | Rec | F1 | ROC-AUC | CV F1 (mean±std) | CV AUC (mean±std) | F1 Dropout / Enrolled / Graduate
--- | --- | --- | --- | --- | --- | --- | --- | --- | ---
Logistic Regression | 0.7706 | 0.6887 | 0.7177 | 0.6887 | 0.6975 | 0.8815 | 0.7031 ± 0.0102 | 0.8891 ± 0.0085 | 0.768 / 0.463 / 0.861
Random Forest | 0.7684 | 0.6655 | 0.7196 | 0.6655 | 0.6727 | 0.8885 | 0.6880 ± 0.0235 | 0.8872 ± 0.0103 | 0.783 / 0.381 / 0.854
XGBoost | 0.7684 | 0.6930 | 0.7126 | 0.6930 | 0.7002 | 0.8871 | 0.7160 ± 0.0149 | 0.8959 ± 0.0101 | 0.768 / 0.472 / 0.860
LightGBM | 0.7605 | 0.6866 | 0.7052 | 0.6866 | 0.6936 | 0.8808 | 0.7083 ± 0.0154 | 0.8921 ± 0.0090 | 0.757 / 0.469 / 0.854
CatBoost | 0.7718 | 0.6840 | 0.7160 | 0.6840 | 0.6923 | 0.8939 | 0.7068 ± 0.0176 | 0.8941 ± 0.0088 | 0.775 / 0.439 / 0.863
Stacking (RF+XGB+LGBM+Cat) | 0.7684 | 0.6966 | 0.7136 | 0.6966 | 0.7031 | 0.8939 | held-out only | held-out only | 0.775 / 0.478 / 0.856

### Student - class weights  (train=3539, test=885)

Model | Acc | Bal.Acc | Prec | Rec | F1 | ROC-AUC | CV F1 (mean±std) | CV AUC (mean±std) | F1 Dropout / Enrolled / Graduate
--- | --- | --- | --- | --- | --- | --- | --- | --- | ---
Logistic Regression | 0.7220 | 0.6993 | 0.6944 | 0.6993 | 0.6862 | 0.8788 | 0.7098 ± 0.0163 | 0.8865 ± 0.0087 | 0.744 / 0.498 / 0.817
Random Forest | 0.7605 | 0.7096 | 0.7138 | 0.7096 | 0.7095 | 0.8882 | 0.7225 ± 0.0233 | 0.8899 ± 0.0100 | 0.756 / 0.518 / 0.855
XGBoost | 0.7684 | 0.6930 | 0.7126 | 0.6930 | 0.7002 | 0.8871 | 0.7160 ± 0.0149 | 0.8959 ± 0.0101 | 0.768 / 0.472 / 0.860
LightGBM | 0.7435 | 0.6830 | 0.6860 | 0.6830 | 0.6841 | 0.8783 | 0.7197 ± 0.0179 | 0.8905 ± 0.0095 | 0.737 / 0.468 / 0.847
CatBoost | 0.7492 | 0.7159 | 0.7100 | 0.7159 | 0.7072 | 0.8878 | 0.7240 ± 0.0191 | 0.8911 ± 0.0105 | 0.757 / 0.520 / 0.845
Stacking (RF+XGB+LGBM+Cat) | 0.7684 | 0.7024 | 0.7140 | 0.7024 | 0.7073 | 0.8930 | held-out only | held-out only | 0.775 / 0.489 / 0.858
XGBoost (Optuna-tuned) | 0.7672 | 0.6869 | 0.7079 | 0.6869 | 0.6942 | 0.8877 | 0.7133 ± 0.0127 | 0.8966 ± 0.0103 | 0.772 / 0.449 / 0.861
LightGBM (Optuna-tuned) | 0.7412 | 0.7014 | 0.6980 | 0.7014 | 0.6955 | 0.8897 | 0.7172 ± 0.0184 | 0.8934 ± 0.0102 | 0.736 / 0.510 / 0.841

Optuna best parameters:
```
{
 "XGBoost": {
  "n_estimators": 700,
  "max_depth": 3,
  "learning_rate": 0.051090350033062455,
  "subsample": 0.9272094131362506,
  "colsample_bytree": 0.9695386982894074,
  "min_child_weight": 2,
  "reg_lambda": 0.014146105881536926
 },
 "LightGBM": {
  "n_estimators": 200,
  "num_leaves": 117,
  "learning_rate": 0.02171103454376615,
  "subsample": 0.8650089137415928,
  "colsample_bytree": 0.6558555380447055,
  "min_child_samples": 34,
  "reg_lambda": 0.1537592023548176
 }
}
```

### Student - SMOTE  (train=3539, test=885)

Model | Acc | Bal.Acc | Prec | Rec | F1 | ROC-AUC | CV F1 (mean±std) | CV AUC (mean±std) | F1 Dropout / Enrolled / Graduate
--- | --- | --- | --- | --- | --- | --- | --- | --- | ---
Logistic Regression | 0.7232 | 0.6942 | 0.6881 | 0.6942 | 0.6834 | 0.8742 | 0.7041 ± 0.0086 | 0.8826 ± 0.0084 | 0.739 / 0.490 / 0.821
Random Forest | 0.7672 | 0.7024 | 0.7155 | 0.7024 | 0.7075 | 0.8898 | 0.7160 ± 0.0281 | 0.8900 ± 0.0115 | 0.761 / 0.500 / 0.861
XGBoost | 0.7593 | 0.6925 | 0.7021 | 0.6925 | 0.6965 | 0.8851 | 0.7193 ± 0.0197 | 0.8966 ± 0.0096 | 0.753 / 0.480 / 0.856
LightGBM | 0.7469 | 0.6749 | 0.6877 | 0.6749 | 0.6800 | 0.8781 | 0.7131 ± 0.0091 | 0.8931 ± 0.0085 | 0.738 / 0.455 / 0.847
CatBoost | 0.7627 | 0.7009 | 0.7063 | 0.7009 | 0.7032 | 0.8875 | 0.7156 ± 0.0172 | 0.8937 ± 0.0112 | 0.769 / 0.483 / 0.858
Stacking (RF+XGB+LGBM+Cat) | 0.7650 | 0.7015 | 0.7104 | 0.7015 | 0.7054 | 0.8871 | held-out only | held-out only | 0.763 / 0.497 / 0.857

### Student - early warning (1st sem only, class weights)  (train=3539, test=885)

Model | Acc | Bal.Acc | Prec | Rec | F1 | ROC-AUC | CV F1 (mean±std) | CV AUC (mean±std) | F1 Dropout / Enrolled / Graduate
--- | --- | --- | --- | --- | --- | --- | --- | --- | ---
Logistic Regression | 0.6915 | 0.6620 | 0.6592 | 0.6620 | 0.6528 | 0.8543 | 0.6794 ± 0.0215 | 0.8614 ± 0.0119 | 0.724 / 0.449 / 0.785
Random Forest | 0.7119 | 0.6496 | 0.6585 | 0.6496 | 0.6524 | 0.8596 | 0.6884 ± 0.0228 | 0.8655 ± 0.0139 | 0.725 / 0.423 / 0.810
XGBoost | 0.7209 | 0.6367 | 0.6528 | 0.6367 | 0.6420 | 0.8663 | 0.6872 ± 0.0147 | 0.8756 ± 0.0121 | 0.728 / 0.375 / 0.823
LightGBM | 0.7220 | 0.6611 | 0.6640 | 0.6611 | 0.6622 | 0.8554 | 0.6865 ± 0.0160 | 0.8657 ± 0.0148 | 0.727 / 0.437 / 0.822
CatBoost | 0.7153 | 0.6792 | 0.6780 | 0.6792 | 0.6721 | 0.8652 | 0.6889 ± 0.0245 | 0.8700 ± 0.0139 | 0.725 / 0.476 / 0.815
Stacking (RF+XGB+LGBM+Cat) | 0.7333 | 0.6552 | 0.6706 | 0.6552 | 0.6608 | 0.8701 | held-out only | held-out only | 0.744 / 0.410 / 0.829


Total runtime: 28.2 min
