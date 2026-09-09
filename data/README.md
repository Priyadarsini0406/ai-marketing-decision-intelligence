# Training data

An additional [UCI Bank Marketing dataset](bank_marketing/README.md) is included
in `data/bank_marketing/`, with a full CSV and a smaller upload-ready sample.
It has its own schema and is not an input to the current digital campaign trainer.

`Digital_Marketing_Campaign_Dataset.csv` was copied from the user-provided
`E:\digital-marketing-campaign-conversion-prediction-main` folder. It contains
8,000 customer records with the binary `Conversion` target. The source folder
attributes the dataset to Kaggle and the accompanying analysis to Elakkiya
Ulaganathan. See `DM_Dataset_Description.txt` for column descriptions.

The CSV remains local and is excluded from Git by the repository's data rule.
Keep a copy when moving this project to another machine.

From the project root, run:

```powershell
.\.venv\Scripts\python.exe backend/train_model.py
```

This evaluates a gradient boosting classifier on a stratified 80/20 split,
generates five-fold out-of-fold predictions for the supplied leads, then saves
a pipeline fitted on all rows in `backend/artifacts/conversion_model.joblib`.
Evaluation metrics are saved in `backend/artifacts/training_report.json`.
Encoding is fitted inside each training split. Customer identifiers, the target,
masked advertising columns, and the observed `ConversionRate` are excluded from
model inputs. Verify that remaining engagement fields are available at your
intended prediction time before using this model prospectively.

The command imports the CSV into the admin dataset inventory and upserts its
leads and probabilities into the existing database. Repeating it updates the
same customer IDs without duplicating them or clearing other accounts/data.
Scores use High >= 0.7, Medium >= 0.4, otherwise Low. SHAP explanations and
clustering are not generated. This does not train a budget optimization agent.
The stored probabilities are out-of-fold estimates, not scores from the final
model on its own training rows. Use `--no-import` to leave the database untouched,
or `--csv <path>` to train on another CSV with the same required columns.

After training, refresh **Marketing datasets**, **Leads & predictions**, or
admin **Analytics & reports** to see the imported data. Training runs through
the command above; the existing web upload flow still only stores datasets.
