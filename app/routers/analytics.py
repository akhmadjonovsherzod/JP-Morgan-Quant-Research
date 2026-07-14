import psycopg2
from fastapi import APIRouter, HTTPException, Query

from app.config import RATING_LABELS
from app.database import get_connection

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview():
    """One summary payload for the top-of-dashboard KPI cards.
    Works even before anything has been scored — it just returns nulls
    for the prediction-based numbers."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM loan_data")
                total_loans = cur.fetchone()[0]

                cur.execute("SELECT COUNT(DISTINCT customer_id) FROM loan_predictions")
                total_scored = cur.fetchone()[0]

                cur.execute(
                    """
                    SELECT ROUND(AVG(prob_default)::numeric, 4),
                           ROUND(SUM(expected_loss)::numeric, 2),
                           ROUND(100.0 * SUM(CASE WHEN prob_default >= 0.6 THEN 1 ELSE 0 END)
                                 / NULLIF(COUNT(*), 0), 2)
                    FROM loan_predictions
                    """
                )
                avg_pd, total_el, high_risk_pct = cur.fetchone()

        return {
            "total_loans": total_loans,
            "total_scored": total_scored,
            "avg_prob_default": float(avg_pd) if avg_pd is not None else None,
            "total_expected_loss": float(total_el) if total_el is not None else None,
            "high_risk_pct": float(high_risk_pct) if high_risk_pct is not None else None,
        }
    except psycopg2.Error as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e}")


@router.get("/rating-breakdown")
def rating_breakdown():
    """Portfolio grouped by predicted credit rating (1=Very Low risk .. 6=Extreme)."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT credit_rating,
                           COUNT(*),
                           ROUND(AVG(prob_default)::numeric, 4),
                           ROUND(SUM(expected_loss)::numeric, 2)
                    FROM loan_predictions
                    GROUP BY credit_rating
                    ORDER BY credit_rating
                    """
                )
                rows = cur.fetchall()
        return [
            {
                "rating": r[0],
                "risk_label": RATING_LABELS.get(r[0], "Unknown"),
                "borrowers": r[1],
                "avg_pd": float(r[2]),
                "total_expected_loss": float(r[3]),
            }
            for r in rows
        ]
    except psycopg2.Error as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e}")


@router.get("/fico-buckets")
def fico_buckets():
    """Default rate by FICO band, straight from the raw loan data.
    Useful because it's available immediately, no scoring required."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        CASE
                            WHEN fico_score < 550 THEN '< 550'
                            WHEN fico_score < 600 THEN '550-599'
                            WHEN fico_score < 650 THEN '600-649'
                            WHEN fico_score < 700 THEN '650-699'
                            ELSE '700+'
                        END AS bucket,
                        COUNT(*),
                        ROUND(AVG(default_flag) * 100, 2),
                        ROUND(AVG(income), 0)
                    FROM loan_data
                    GROUP BY bucket
                    ORDER BY MIN(fico_score)
                    """
                )
                rows = cur.fetchall()
        return [
            {
                "bucket": r[0],
                "total_borrowers": r[1],
                "default_rate_pct": float(r[2]),
                "avg_income": float(r[3]),
            }
            for r in rows
        ]
    except psycopg2.Error as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e}")


@router.get("/top-risk")
def top_risk(limit: int = Query(10, ge=1, le=100)):
    """Highest expected-loss borrowers — the ones a credit team would look at first."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT l.customer_id, l.fico_score, l.income,
                           p.prob_default, p.expected_loss, p.credit_rating
                    FROM loan_predictions p
                    JOIN loan_data l ON l.customer_id = p.customer_id
                    ORDER BY p.expected_loss DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return [
            {
                "customer_id": r[0],
                "fico_score": r[1],
                "income": float(r[2]),
                "prob_default": float(r[3]),
                "expected_loss": float(r[4]),
                "risk_label": RATING_LABELS.get(r[5], "Unknown"),
            }
            for r in rows
        ]
    except psycopg2.Error as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e}")
