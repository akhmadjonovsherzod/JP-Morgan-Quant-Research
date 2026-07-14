SELECT
    CASE
        WHEN fico_score < 550 THEN '< 550  (Very Poor)'
        WHEN fico_score < 600 THEN '550-599 (Poor)'
        WHEN fico_score < 650 THEN '600-649 (Fair)'
        WHEN fico_score < 700 THEN '650-699 (Good)'
        ELSE                       '700+    (Excellent)'
    END                                       AS fico_bucket,
    COUNT(*)                                  AS total_borrowers,
    SUM(default_flag)                         AS total_defaults,
    ROUND(AVG(default_flag) * 100, 2)         AS default_rate_pct,
    ROUND(AVG(income), 0)                     AS avg_income,
    ROUND(AVG(loan_amt_outstanding), 0)       AS avg_loan_amt
FROM loan_data
GROUP BY fico_bucket
ORDER BY MIN(fico_score);


SELECT
    customer_id,
    income,
    total_debt_outstanding,
    ROUND(total_debt_outstanding / NULLIF(income, 0), 4)  AS debt_to_income_ratio,
    NTILE(5) OVER (
        ORDER BY total_debt_outstanding / NULLIF(income, 0) DESC
    )                                                      AS dti_risk_quintile,
    default_flag
FROM loan_data
ORDER BY debt_to_income_ratio DESC
LIMIT 20;


SELECT
    fico_score,
    COUNT(*)          AS borrowers_at_this_score,
    SUM(default_flag) AS defaults_at_this_score,
    SUM(SUM(default_flag)) OVER (
        ORDER BY fico_score
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                 AS cumulative_defaults,
    SUM(COUNT(*)) OVER (
        ORDER BY fico_score
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                 AS cumulative_borrowers
FROM loan_data
GROUP BY fico_score
ORDER BY fico_score;


SELECT
    l.customer_id,
    l.fico_score,
    l.income,
    l.loan_amt_outstanding,
    l.default_flag                        AS actual_default,
    p.prob_default,
    p.credit_rating,
    p.expected_loss,
    CASE
        WHEN p.prob_default >= 0.60 AND l.default_flag = 1 THEN 'True Positive'
        WHEN p.prob_default >= 0.60 AND l.default_flag = 0 THEN 'False Positive'
        WHEN p.prob_default <  0.60 AND l.default_flag = 1 THEN 'False Negative'
        ELSE                                                     'True Negative'
    END                                   AS prediction_outcome
FROM loan_data l
INNER JOIN loan_predictions p ON l.customer_id = p.customer_id
ORDER BY p.prob_default DESC
LIMIT 50;


SELECT
    price_date,
    price,
    LAG(price) OVER (ORDER BY price_date)  AS prev_month_price,
    ROUND(
        price - LAG(price) OVER (ORDER BY price_date),
        4
    )                                      AS price_change,
    ROUND(
        (price - LAG(price) OVER (ORDER BY price_date))
        / NULLIF(LAG(price) OVER (ORDER BY price_date), 0) * 100,
        2
    )                                      AS pct_change
FROM nat_gas_prices
ORDER BY price_date;


CREATE OR REPLACE VIEW portfolio_risk_summary AS
SELECT
    p.credit_rating,
    COUNT(*)                            AS num_borrowers,
    ROUND(AVG(p.prob_default) * 100, 2) AS avg_pd_pct,
    ROUND(SUM(p.expected_loss), 0)      AS total_expected_loss,
    ROUND(AVG(l.income), 0)             AS avg_income,
    ROUND(AVG(l.fico_score), 0)         AS avg_fico
FROM loan_predictions p
JOIN loan_data l ON l.customer_id = p.customer_id
GROUP BY p.credit_rating
ORDER BY p.credit_rating;
