import psycopg2
from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.model import score_borrower
from app.schemas import BorrowerInput, PredictionResult

router = APIRouter(tags=["prediction"])

MODEL_NAME = "logistic_regression_v1"


def _save_prediction(result: dict) -> bool:
    """Best-effort save. A borrower can still get a prediction even if
    the database is temporarily down — it just won't be persisted."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO loan_predictions
                        (customer_id, prob_default, credit_rating, expected_loss, model_name)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        result["customer_id"],
                        result["prob_default"],
                        result["credit_rating"],
                        result["expected_loss"],
                        MODEL_NAME,
                    ),
                )
            conn.commit()
        return True
    except psycopg2.Error:
        return False


@router.post("/predict", response_model=PredictionResult)
def predict(borrower: BorrowerInput):
    result = score_borrower(borrower)
    result["saved_to_db"] = _save_prediction(result)
    return result


@router.post("/score-all", tags=["prediction"])
def score_all_loans():
    """
    Scores every loan currently in `loan_data` and stores the results in
    `loan_predictions`. This replaces the old approach of looping over
    every loan and calling /predict over HTTP one at a time.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT customer_id, credit_lines_outstanding, loan_amt_outstanding,
                           total_debt_outstanding, income, years_employed, fico_score
                    FROM loan_data
                    """
                )
                loans = cur.fetchall()

            scored = 0
            with conn.cursor() as cur:
                for loan in loans:
                    borrower = BorrowerInput(
                        customer_id=loan[0],
                        credit_lines_outstanding=loan[1],
                        loan_amt_outstanding=float(loan[2]),
                        total_debt_outstanding=float(loan[3]),
                        income=float(loan[4]),
                        years_employed=loan[5],
                        fico_score=loan[6],
                    )
                    result = score_borrower(borrower)
                    cur.execute(
                        """
                        INSERT INTO loan_predictions
                            (customer_id, prob_default, credit_rating, expected_loss, model_name)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            result["customer_id"],
                            result["prob_default"],
                            result["credit_rating"],
                            result["expected_loss"],
                            MODEL_NAME,
                        ),
                    )
                    scored += 1
            conn.commit()
        return {"scored": scored}
    except psycopg2.Error as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e}")
