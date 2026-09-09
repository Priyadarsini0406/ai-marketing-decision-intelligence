# Bank Marketing dataset

Additional labeled marketing data for campaign response prediction.

Source: [UCI Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing).
Citation: Moro, S., Rita, P., & Cortez, P. (2014). Bank Marketing [Dataset].
UCI Machine Learning Repository. https://doi.org/10.24432/C5K306.
License: [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
Downloaded on 2026-09-09 from
https://archive.ics.uci.edu/static/public/222/bank+marketing.zip.

## Files

- `bank-additional-full.csv`: 41,188 records, 20 input columns and target `y`.
- `bank-additional.csv`: UCI's supplied 4,119-record sample of the full data.
- `bank-additional-names.txt`: original column descriptions and source notes.
- `manifest.json`: verified row counts, label counts and file checksums.
- `prepare.py`: repeatable conversion and validation script. To regenerate,
  download the source URL above as `source.zip` in this folder, then run
  `.\.venv\Scripts\python.exe data/bank_marketing/prepare.py` from the project root.
  The downloaded ZIP is excluded from Git; the converted CSVs are included.

Both CSVs are converted from UCI's semicolon delimiter to standard comma CSV
for this project's dataset uploader. Column names, values, and row order are
preserved. These CSVs are explicitly allowed by `.gitignore` so they can travel
with the project when committed. The sample overlaps the full dataset: do not
concatenate them or treat the sample as an independent test set.

## Use in this project

In admin **Marketing datasets**, upload `bank-additional.csv` to preview the
sample. It fits the existing 10,000-row and 5 MB upload limits. The full file
is intended for offline analysis; it exceeds the uploader's row limit.

The prediction target is `y`: `yes` means subscribed to a term deposit and
`no` means did not subscribe. This is telephone marketing data, with client,
campaign contact, prior campaign, and economic attributes. It is a related
conversion task with a different schema from the existing digital campaign CSV.
`backend/train_model.py` currently requires that original schema and cannot
train this dataset directly. This addition supplies data only; the existing
model and database predictions are unchanged. A separate pipeline should use
`y` as its target and the bank-specific features without fabricating missing
digital campaign columns such as ad spend or email clicks.

Exclude `duration` when predicting before a call: the completed call duration
is not yet available then. Treat `unknown` categories explicitly and remember
that `pdays=999` means no previous contact. The full file is ordered by date;
prefer evaluation that preserves time order for future-campaign predictions.
