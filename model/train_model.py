"""
Trains the credit-risk model used by the API.

This is the same Logistic Regression approach used in
`Quant-Research-main/Task 3 - Credit risk analysis/task-3.ipynb`, cleaned up
into a reusable script:

- drops customer_id from the features (it's an ID, not a risk signal —
  the notebook accidentally left it in)
- adds a debt-to-income and loan-to-income ratio, which the EDA in the
  notebook showed were informative
- wraps scaling + the classifier in one sklearn Pipeline, so the exact
  same object can be reused for training and for live predictions
- saves the fitted pipeline + evaluation metrics to disk

Run it with:
    python model/train_model.py
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

THIS_DIR = Path(__file__).parent
DATA_CSV = (
    THIS_DIR.parent
    / "Quant-Research-main"
    / "Task 3 - Credit risk analysis"
    / "Task 3 and 4_Loan_Data.csv"
)
MODEL_PATH = THIS_DIR / "credit_model.joblib"
METRICS_PATH = THIS_DIR / "metrics.json"

# Order matters: the API builds a row in exactly this order before predicting.
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


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["debt_to_income"] = df["total_debt_outstanding"] / df["income"]
    df["loan_to_income"] = df["loan_amt_outstanding"] / df["income"]
    return df


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(DATA_CSV)
    df = add_engineered_features(df)
    X = df[FEATURE_COLUMNS]
    y = df["default"]
    return X, y


def train() -> None:
    X, y = load_training_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "f1_score": round(f1_score(y_test, y_pred), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "features": FEATURE_COLUMNS,
        "model": "LogisticRegression",
    }

    joblib.dump(pipeline, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    print("Model trained and saved to", MODEL_PATH)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    train()
