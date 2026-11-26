
-- BANK CUSTOMER CREDIT RISK ANALYSIS
-- Business Analysis using PostgreSQL

-- 1. Total customers and credit classification
SELECT
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE risk_status = 'Good') AS good_customers,
    COUNT(*) FILTER (WHERE risk_status = 'Bad') AS bad_customers
FROM credit_risk_analysis;


-- 2. Credit risk distribution by age group
SELECT
    age_group,
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE risk_status = 'Bad') AS bad_customers,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE risk_status = 'Bad')
        / NULLIF(COUNT(*), 0), 2
    ) AS bad_credit_percentage
FROM credit_risk_analysis
GROUP BY age_group
ORDER BY bad_credit_percentage DESC;


-- 3. Credit risk by loan purpose
SELECT
    loan_purpose,
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE risk_status = 'Bad') AS bad_customers,
    ROUND(AVG(credit_amount), 2) AS average_loan_amount
FROM credit_risk_analysis
GROUP BY loan_purpose
ORDER BY bad_customers DESC;


-- 4. Credit risk by employment duration
SELECT
    employment_since,
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE risk_status = 'Bad') AS bad_customers
FROM credit_risk_analysis
GROUP BY employment_since
ORDER BY bad_customers DESC;


-- 5. Average loan amount and duration by credit status
SELECT
    risk_status,
    COUNT(*) AS total_customers,
    ROUND(AVG(credit_amount), 2) AS average_credit_amount,
    ROUND(AVG(loan_duration_months), 2) AS average_loan_duration
FROM credit_risk_analysis
GROUP BY risk_status;


-- 6. Credit risk by checking account balance category
SELECT
    checking_account,
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE risk_status = 'Bad') AS bad_customers
FROM credit_risk_analysis
GROUP BY checking_account
ORDER BY bad_customers DESC;


-- 7. Credit risk by loan amount band
SELECT
    loan_amount_band,
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE risk_status = 'Bad') AS bad_customers,
    ROUND(AVG(credit_amount), 2) AS average_credit_amount
FROM credit_risk_analysis
GROUP BY loan_amount_band
ORDER BY average_credit_amount;


-- 8. Credit risk by housing category
SELECT
    housing,
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE risk_status = 'Bad') AS bad_customers,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE risk_status = 'Bad')
        / NULLIF(COUNT(*), 0), 2
    ) AS bad_credit_percentage
FROM credit_risk_analysis
GROUP BY housing
ORDER BY bad_credit_percentage DESC;


-- 9. Rank loan purposes by bad-credit percentage (Window Function)
WITH purpose_summary AS (
    SELECT
        loan_purpose,
        COUNT(*) AS total_customers,
        COUNT(*) FILTER (WHERE risk_status = 'Bad') AS bad_customers,
        100.0 * COUNT(*) FILTER (WHERE risk_status = 'Bad')
        / NULLIF(COUNT(*), 0) AS bad_credit_percentage
    FROM credit_risk_analysis
    GROUP BY loan_purpose
)
SELECT
    loan_purpose,
    total_customers,
    bad_customers,
    ROUND(bad_credit_percentage, 2) AS bad_credit_percentage,
    RANK() OVER (ORDER BY bad_credit_percentage DESC) AS risk_rank
FROM purpose_summary
ORDER BY risk_rank;


-- 10. Compare each customer's loan with their credit-status average
SELECT
    risk_status,
    credit_amount,
    ROUND(
        AVG(credit_amount) OVER (PARTITION BY risk_status), 2
    ) AS status_average_loan,
    ROUND(
        credit_amount -
        AVG(credit_amount) OVER (PARTITION BY risk_status), 2
    ) AS difference_from_status_average
FROM credit_risk_analysis
ORDER BY risk_status, credit_amount DESC;
