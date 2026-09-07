# Verification materials for "Automatic Determination of the Number of Clusters in K-Means Clustering: A Critical Review, 2016--2026"

This repository holds the machine-readable corpus and the verification code that accompany the review.

## Contents

| File | What it is |
|---|---|
| `methods_table.csv` | The full 110-method comparison table in machine-readable form, viz. one row per method with year, family, decision mechanism, verdict (AUTO / AUTO-dagger / RANGE / SUBST / NOT-AUTO), range requirement, user parameters, cost, scaling behaviour, failure modes and the DOI or identifier of the source paper. |
| `ref_records.json` | One record per reference entry of the paper: entry number, DOI or arXiv identifier as printed, caution flag, and the plain text of the entry. |
| `caution_refs.json` | The entry numbers of the 31 references that carry a caution mark in the paper. |
| `verify_refs.py` | Script that re-resolves every identifier against Crossref, DataCite and arXiv and checks the record title against the printed entry. Writes `verification_report.csv`. |
| `CDK_review_reference_verification.ipynb` | The same check as a self-contained Colab notebook. Open in Google Colab and run all cells. |

## How to verify the reference list

```
pip install requests
python3 verify_refs.py
```

The run takes a few minutes for 240 identifiers and prints a summary. Entries flagged `title-mismatch` or `unresolved` should be checked by hand; the 31 caution-marked entries are expected to appear there, and the paper says so.

## How to check the paper's headline counts

The verdict distribution reported in Table 1 of the paper can be recomputed from `methods_table.csv`:

```python
import csv, collections
rows = list(csv.DictReader(open("methods_table.csv")))
print(collections.Counter(r["verdict"] for r in rows))
```

## Citation

If you use the table or the scripts, please cite the review.
