DROP TABLE IF EXISTS loan_predictions CASCADE;
DROP TABLE IF EXISTS loan_data CASCADE;
DROP TABLE IF EXISTS nat_gas_prices CASCADE;

CREATE TABLE loan_data (
    id                       SERIAL PRIMARY KEY,
    customer_id              BIGINT         NOT NULL UNIQUE,
    credit_lines_outstanding INT            NOT NULL,
    loan_amt_outstanding     NUMERIC(12, 2) NOT NULL,
    total_debt_outstanding   NUMERIC(12, 2) NOT NULL,
    income                   NUMERIC(14, 2) NOT NULL,
    years_employed           INT            NOT NULL,
    fico_score               INT            NOT NULL,
    default_flag             SMALLINT       NOT NULL CHECK (default_flag IN (0, 1)),
    loaded_at                TIMESTAMP      DEFAULT NOW()
);

CREATE INDEX idx_loan_fico    ON loan_data(fico_score);
CREATE INDEX idx_loan_default ON loan_data(default_flag);
CREATE INDEX idx_loan_income  ON loan_data(income);

CREATE TABLE nat_gas_prices (
    id         SERIAL PRIMARY KEY,
    price_date DATE           NOT NULL UNIQUE,
    price      NUMERIC(10, 4) NOT NULL,
    loaded_at  TIMESTAMP      DEFAULT NOW()
);

CREATE INDEX idx_gas_date ON nat_gas_prices(price_date);

CREATE TABLE loan_predictions (
    id            SERIAL PRIMARY KEY,
    customer_id   BIGINT         NOT NULL REFERENCES loan_data(customer_id),
    prob_default  NUMERIC(6, 4)  NOT NULL,
    credit_rating SMALLINT       NOT NULL,
    expected_loss NUMERIC(14, 2),
    model_name    VARCHAR(50)    NOT NULL,
    scored_at     TIMESTAMP      DEFAULT NOW()
);

CREATE INDEX idx_pred_customer ON loan_predictions(customer_id);
CREATE INDEX idx_pred_rating   ON loan_predictions(credit_rating);
