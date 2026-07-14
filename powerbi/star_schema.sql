-- Star schema for the Power BI dashboard.
-- Run this after loans have been scored (POST /api/score-all, or the
-- "Score all loans" button in the app).
--
-- Changes from the original version:
--   1. dim_date is now actually populated (it was created but left empty,
--      so any date-based visual in Power BI would have shown blanks).
--   2. dim_borrower now carries the *actual* default flag, which is what
--      makes a Model Performance page possible (predicted vs. actual).
--   3. fact_loan_risk is built from each borrower's most recent score
--      instead of hard-filtering on a model name, so re-running
--      "Score all loans" doesn't silently produce an empty fact table.

CREATE TABLE IF NOT EXISTS dim_borrower (
    borrower_key    SERIAL PRIMARY KEY,
    customer_id     BIGINT      NOT NULL UNIQUE,
    fico_score      INT,
    income_band     VARCHAR(20),
    employment_band VARCHAR(20),
    dti_band        VARCHAR(20),
    actual_default  SMALLINT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key    INT PRIMARY KEY,
    full_date   DATE,
    year        INT,
    quarter     INT,
    month       INT,
    month_name  VARCHAR(9),
    day_of_week VARCHAR(9)
);

CREATE TABLE IF NOT EXISTS dim_rating (
    rating_key   INT PRIMARY KEY,
    rating_label VARCHAR(20),
    pd_range     VARCHAR(20),
    color_hex    CHAR(7)
);

INSERT INTO dim_rating VALUES
    (1, 'Very Low Risk',  '< 5%',   '#1E8E5A'),
    (2, 'Low Risk',       '5-15%',  '#7CB518'),
    (3, 'Medium Risk',    '15-30%', '#E3A008'),
    (4, 'High Risk',      '30-50%', '#E8730A'),
    (5, 'Very High Risk', '50-70%', '#D8412F'),
    (6, 'Extreme Risk',   '> 70%',  '#6D3F91')
ON CONFLICT (rating_key) DO NOTHING;

CREATE TABLE IF NOT EXISTS fact_loan_risk (
    fact_key           SERIAL PRIMARY KEY,
    borrower_key       INT REFERENCES dim_borrower(borrower_key),
    date_key           INT REFERENCES dim_date(date_key),
    rating_key         INT REFERENCES dim_rating(rating_key),
    prob_default       NUMERIC(6, 4),
    expected_loss       NUMERIC(14, 2),
    loan_amt            NUMERIC(14, 2),
    total_debt          NUMERIC(14, 2),
    income               NUMERIC(14, 2),
    credit_lines         INT,
    predicted_default    SMALLINT   -- 1 if prob_default >= 0.60, else 0
);

-- Reset before rebuilding so this script can be re-run safely.
TRUNCATE TABLE fact_loan_risk RESTART IDENTITY;
TRUNCATE TABLE dim_borrower RESTART IDENTITY CASCADE;
DELETE FROM dim_date;

INSERT INTO dim_borrower
    (customer_id, fico_score, income_band, employment_band, dti_band, actual_default)
SELECT
    customer_id,
    fico_score,
    CASE
        WHEN income <  30000  THEN 'Low'
        WHEN income <  70000  THEN 'Mid'
        WHEN income < 150000  THEN 'High'
        ELSE                       'Very High'
    END,
    CASE
        WHEN years_employed <= 2 THEN '0-2 yrs'
        WHEN years_employed <= 5 THEN '3-5 yrs'
        ELSE                          '6+ yrs'
    END,
    CASE
        WHEN total_debt_outstanding / NULLIF(income, 0) < 0.3 THEN 'Low'
        WHEN total_debt_outstanding / NULLIF(income, 0) < 0.7 THEN 'Medium'
        ELSE                                                        'High'
    END,
    default_flag
FROM loan_data;

-- One row per calendar date that appears in loan_predictions.
INSERT INTO dim_date (date_key, full_date, year, quarter, month, month_name, day_of_week)
SELECT DISTINCT
    TO_CHAR(scored_at::date, 'YYYYMMDD')::INT,
    scored_at::date,
    EXTRACT(YEAR    FROM scored_at)::INT,
    EXTRACT(QUARTER FROM scored_at)::INT,
    EXTRACT(MONTH   FROM scored_at)::INT,
    TO_CHAR(scored_at, 'Month'),
    TO_CHAR(scored_at, 'Day')
FROM loan_predictions;

-- One row per borrower: their most recent prediction, whichever model produced it.
INSERT INTO fact_loan_risk
    (borrower_key, date_key, rating_key, prob_default, expected_loss,
     loan_amt, total_debt, income, credit_lines, predicted_default)
SELECT
    db.borrower_key,
    TO_CHAR(latest.scored_at::date, 'YYYYMMDD')::INT,
    latest.credit_rating,
    latest.prob_default,
    latest.expected_loss,
    l.loan_amt_outstanding,
    l.total_debt_outstanding,
    l.income,
    l.credit_lines_outstanding,
    CASE WHEN latest.prob_default >= 0.60 THEN 1 ELSE 0 END
FROM (
    SELECT DISTINCT ON (customer_id) *
    FROM loan_predictions
    ORDER BY customer_id, scored_at DESC
) latest
JOIN loan_data l     ON l.customer_id  = latest.customer_id
JOIN dim_borrower db ON db.customer_id = latest.customer_id;
