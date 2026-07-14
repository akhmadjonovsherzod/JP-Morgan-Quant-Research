"""
Loads the trained model once at startup and exposes plain functions for
scoring a borrower. Nothing here talks to the database or to FastAPI —
that separation is what makes this easy to unit test.
"""

from pathlib import Path

import joblib
import pandas as pd

from app.config import RATING_LABELS, RECOVERY_RATE
from app.schemas import BorrowerInput

MODEL_PATH = Path(__file__).parent.parent / "model" / "credit_model.joblib"

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"No trained model found at {MODEL_PATH}. "
        "Run `python model/train_model.py` first."
    )

_pipeline = joblib.load(MODEL_PATH)

# Must match the column order used in model/train_model.py
FEATURE_COLUMNS = [
    "credit_lines_outstanding",
    "loan_amt_outstanding",
    "total_debt_outstanding",
    "income",
    "years_employed",
    "fico_score",
    "debt_to_income",
    "loan_to_income",
]


def _to_feature_row(borrower: BorrowerInput) -> pd.DataFrame:
    debt_to_income = borrower.total_debt_outstanding / borrower.income
    loan_to_income = borrower.loan_amt_outstanding / borrower.income
    row = {
        "credit_lines_outstanding": borrower.credit_lines_outstanding,
        "loan_amt_outstanding": borrower.loan_amt_outstanding,
        "total_debt_outstanding": borrower.total_debt_outstanding,
        "income": borrower.income,
        "years_employed": borrower.years_employed,
        "fico_score": borrower.fico_score,
        "debt_to_income": debt_to_income,
        "loan_to_income": loan_to_income,
    }
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


def predict_prob_default(borrower: BorrowerInput) -> float:
    features = _to_feature_row(borrower)
    prob = _pipeline.predict_proba(features)[0, 1]
    return round(float(prob), 4)


def assign_rating(prob: float) -> int:
    if prob < 0.05:
        return 1
    if prob < 0.15:
        return 2
    if prob < 0.30:
        return 3
    if prob < 0.50:
        return 4
    if prob < 0.70:
        return 5
    return 6


def risk_label(rating: int) -> str:
    return RATING_LABELS[rating]


def calculate_expected_loss(prob_default: float, loan_amt_outstanding: float) -> float:
    lgd = (1 - RECOVERY_RATE) * loan_amt_outstanding
    return round(prob_default * lgd, 2)


def score_borrower(borrower: BorrowerInput) -> dict:
    """One call that returns everything the API/UI needs for a borrower."""
    prob = predict_prob_default(borrower)
    rating = assign_rating(prob)
    expected_loss = calculate_expected_loss(prob, borrower.loan_amt_outstanding)
    return {
        "customer_id": borrower.customer_id,
        "prob_default": prob,
        "credit_rating": rating,
        "risk_label": risk_label(rating),
        "expected_loss": expected_loss,
    }
