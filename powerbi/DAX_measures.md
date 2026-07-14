# Power BI DAX Measures

Connect Power BI to PostgreSQL:
**Home → Get Data → PostgreSQL database → localhost:5432 → quant_research**

Import tables: `fact_loan_risk`, `dim_borrower`, `dim_rating`, `dim_date`

Then build the relationships (Model view) if Power BI doesn't auto-detect them:
`fact_loan_risk[borrower_key] → dim_borrower[borrower_key]`,
`fact_loan_risk[date_key] → dim_date[date_key]`,
`fact_loan_risk[rating_key] → dim_rating[rating_key]`.

---

## Portfolio measures

```dax
Total Borrowers =
COUNTROWS(fact_loan_risk)

Avg PD % =
AVERAGE(fact_loan_risk[prob_default]) * 100

Total Expected Loss =
SUM(fact_loan_risk[expected_loss])

High Risk Count =
CALCULATE(
    COUNTROWS(fact_loan_risk),
    fact_loan_risk[prob_default] >= 0.60
)

High Risk % =
DIVIDE([High Risk Count], [Total Borrowers], 0) * 100

Avg FICO =
AVERAGE(dim_borrower[fico_score])

Total Loan Exposure =
SUM(fact_loan_risk[loan_amt])

Loss Rate % =
DIVIDE([Total Expected Loss], [Total Loan Exposure], 0) * 100

Avg Expected Loss per Borrower =
DIVIDE([Total Expected Loss], [Total Borrowers], 0)
```

---

## Model performance measures (new)

These compare the model's prediction (`fact_loan_risk[predicted_default]`, 1 if
PD ≥ 60%) against what actually happened (`dim_borrower[actual_default]`), so
you can build a confusion matrix and standard classification metrics.

```dax
True Positives =
CALCULATE(
    COUNTROWS(fact_loan_risk),
    fact_loan_risk[predicted_default] = 1,
    dim_borrower[actual_default] = 1
)

False Positives =
CALCULATE(
    COUNTROWS(fact_loan_risk),
    fact_loan_risk[predicted_default] = 1,
    dim_borrower[actual_default] = 0
)

False Negatives =
CALCULATE(
    COUNTROWS(fact_loan_risk),
    fact_loan_risk[predicted_default] = 0,
    dim_borrower[actual_default] = 1
)

True Negatives =
CALCULATE(
    COUNTROWS(fact_loan_risk),
    fact_loan_risk[predicted_default] = 0,
    dim_borrower[actual_default] = 0
)

Model Accuracy % =
DIVIDE(
    [True Positives] + [True Negatives],
    [Total Borrowers],
    0
) * 100

Model Precision % =
DIVIDE([True Positives], [True Positives] + [False Positives], 0) * 100

Model Recall % =
DIVIDE([True Positives], [True Positives] + [False Negatives], 0) * 100

Model F1 Score =
DIVIDE(
    2 * [Model Precision %] * [Model Recall %],
    [Model Precision %] + [Model Recall %],
    0
)

Actual Default Rate % =
AVERAGE(dim_borrower[actual_default]) * 100
```

---

## Recommended pages & visuals

| Page | Visual | Fields |
|---|---|---|
| **KPI Overview** | Cards | Total Borrowers, Avg PD %, Total Expected Loss, High Risk % |
| **Rating Analysis** | Bar chart | `dim_rating[rating_label]` (axis) × Total Borrowers (value) |
| | Donut chart | `dim_rating[rating_label]` (legend) × Total Loan Exposure (value) |
| | Slicer | `dim_rating[rating_label]` |
| **Borrower Risk Profile** | Scatter plot | Avg FICO (X) vs Avg PD % (Y), bubble size = Total Loan Exposure, split by `dim_borrower[income_band]` |
| | Column chart | `dim_borrower[income_band]` (axis) × Total Expected Loss (value) |
| | Slicers | `dim_borrower[income_band]`, `dim_borrower[employment_band]`, `dim_borrower[dti_band]` |
| **Model Performance** *(new)* | 2×2 matrix or 4 cards | True Positives, False Positives, False Negatives, True Negatives |
| | Cards | Model Accuracy %, Model Precision %, Model Recall %, Model F1 Score |
| | Clustered column | Avg PD % vs Actual Default Rate %, split by `dim_rating[rating_label]` — shows whether the model is well-calibrated per rating band |
| | Line chart | `dim_date[full_date]` (axis) × Avg PD % (value) — trend of scoring runs over time |

---

## Slicers available across all pages

- `dim_borrower[income_band]`
- `dim_borrower[employment_band]`
- `dim_borrower[dti_band]`
- `dim_rating[rating_label]`
- `dim_date[year]`, `dim_date[quarter]`
