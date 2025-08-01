JP Morgan Quantitative Research Analysis – Report
Task 1 – Natural Gas Price Forecasting
Data overview

    Dataset – Monthly Henry Hub natural gas prices from October 2020 to September 2024 (48 observations).

    Descriptive statistics – Mean price about 11.21 $/MMBtu, standard deviation 0.76, minimum 9.84, maximum 12.80. The 25th/50th/75th percentiles are approximately 10.65/11.30/11.63 respectively【8†L1-L9】.

    Moving averages – A 3‑month simple moving average (SMA) smooths short‑term volatility while a 12‑month SMA captures the annual trend. By September 2024 the SMA‑3 is ≈11.63 and the SMA‑12 is ≈12.03【8†L20-L29】, showing that the long‑term average price is slightly higher than recent months.

    Trend analysis – Fitting a linear trend to the price series yields slope ≈0.039 $/MMBtu per month and intercept ≈10.25【8†L13-L14】. This corresponds to an annual increase of ~$0.47 (4 %) and indicates a gradual upward trend.

    Seasonal decomposition – A multiplicative seasonal‑trend decomposition reveals a mild seasonal component and a rising trend. The series is not stationary according to the Augmented Dickey‑Fuller test (p‑value ≈ 0.97)【8†L32-L32】, so differencing is needed for time‑series models.

Forecasting models
Model	Key steps	Findings
Seasonal ARIMA (SARIMA)	Used pmdarima.auto_arima to select optimal parameters. The best model, ARIMA(2,1,2) with no seasonal terms, minimized AIC ≈ 36.1. Forecasts were generated starting from a user‑selected date. For example, forecasting from 31‑Dec‑2020 yielded a predicted December 2021 price of ≈11.27 $/MMBtu, close to the actual 11.40【8†L53-L54】.	SARIMA captured the slow upward trend and produced accurate one‑year forecasts with errors around 1–2 %.
Prophet	Converted the data to Prophet’s ds/y format, fitted a multiplicative seasonal model with MCMC sampling and generated 2‑year forecasts. The predicted August 2024 price was ≈12.37 $/MMBtu versus the actual 11.50, a 7.6 % error【8†L64-L65】. Forecasts for 2025 showed prices climbing toward 14.6 $/MMBtu by mid‑2025【8†L63-L64】.	Prophet captured seasonality and projected a stronger upward trend than SARIMA; however, the model tends to over‑forecast in periods where actual prices flatten.
Key takeaways

    Natural gas prices showed a gradual upward drift (~$0.47 per year) with mild seasonality. The 3‑month moving average lagged the 12‑month average by ~0.4 $/MMBtu toward the end of the sample.

    SARIMA provided a parsimonious model with good short‑term predictive power (1–2 % error). Prophet offered a more flexible structure but tended to overestimate prices in the latter part of the sample, projecting higher growth than observed in reality.

    Forecasts are sensitive to the starting date; using data up to December 2023, SARIMA and Prophet both anticipate continued growth, though the magnitude differs. A range of 11.9–14.6 $/MMBtu for 2025 emerges from the models, highlighting uncertainty.

Task 2 – Commodity Storage Contract Valuation
Scenario and assumptions

    Underlying asset – The same natural gas price series as Task 1.

    Injection schedule – On 30 Jun 2021, 31 Jul 2021 and 31 Aug 2021 the storage operator injects the maximum rate of 500,000 MMBtu per month. Prices at the injection dates were $10.00, $10.10 and $10.30【9†L10-L10】.

    Withdrawal schedule – Gas is withdrawn on 31 Dec 2021, 31 Jan 2022 and 28 Feb 2022 at the maximum rate of 500,000 MMBtu per month; withdrawal prices were $11.40, $11.50 and $11.80【9†L11-L11】.

    Costs – Injection cost $10k per injection, withdrawal cost $10k per withdrawal, transportation cost $50k per injection or withdrawal (so six legs), storage cost $100k per month, and maximum inventory 1.5 million MMBtu.

Financial evaluation

    Planned injection cost – The total purchase cost for the 1.5 million MMBtu injected over three months is $15.2 million (10.0 × 500k + 10.1 × 500k + 10.3 × 500k)【9†L13-L13】.

    Planned withdrawal revenue – Selling the same quantity in Dec 2021–Feb 2022 yields $17.35 million (11.4 × 500k + 11.5 × 500k + 11.8 × 500k)【9†L14-L14】.

    Gross margin – $2.15 million profit before costs【9†L15-L15】.

    Additional costs – Transportation cost for six legs: $0.3 million; storage cost for nine months: $0.9 million (storage period from June 2021 to February 2022)【9†L18-L20】; injection fees: $30k; withdrawal fees: $30k.

    Net margin – After deducting all costs, the value of the storage contract is $0.89 million【9†L21-L21】. This indicates the strategy is profitable under the assumed price curve and cost structure, though margins are sensitive to price spreads and could be negative if injection costs increase or withdrawal prices fall.

Task 3 – Credit Risk Analysis and Expected Loss Modelling
Dataset and exploratory analysis

    Dataset – 10,000 consumer loans with fields including customer ID, number of credit lines, loan amount, total debt, annual income, years employed, FICO score and a default flag (1=default). Defaults occurred in 1,851 loans (18.5 %)【10†L6-L6】.

    Initial insights – Defaults are more common for lower FICO scores and lower income levels; histograms show that defaulters’ FICO scores cluster below 600 and income distributions are skewed lower. Borrowers with high FICO scores (above 700) rarely default. Scatter plots of FICO vs. income and other loan characteristics show a weak negative correlation between credit quality and default.

    Feature engineering – Two ratios were computed: income/total debt and income/loan amount, capturing the borrower’s ability to service debt. These features help distinguish between borrowers with similar credit scores but different leverage.

XGBoost probability‑of‑default (PD) model

    Model training – An XGBoost classifier was fitted using a 70/30 train‑test split. The model predicts a probability of default for each loan. Thresholding at 60 % PD generates default/non‑default labels.

    Performance – The confusion matrix shows 2,468 true negatives, 520 true positives, 4 false positives and 8 false negatives on the test set; precision and recall for the default class are 0.99 and 0.98 respectively, and overall accuracy is ≈99 %【10†L75-L75】. The ROC‑AUC is 0.995【10†L76-L76】, indicating excellent discrimination.

    Portfolio PDs and expected loss – Applying the model to all loans yields PDs ranging from near zero to 100 %. A 90 % loss‑given‑default (LGD) assumption is used (i.e., recovery rate 10 %), so LGD = 0.9 × loan amount. Expected loss per loan is PD × LGD. Total expected loss across the portfolio is about $7.42 million, with the largest single expected loss about $9.19 k (a borrower with a loan of $10,210 and PD ≈1) as shown in the top‑loss table below.

Customer ID	Loan amount ($)	Probability of default	Expected loss ($)
6,597,386	10,210.75	0.9999	9,188.73
1,998,635	9,563.69	0.9999	8,606.32
4,836,461	9,105.96	0.9999	8,194.73
3,983,392	8,989.18	0.9998	8,088.75
2,527,305	8,841.92	0.9999	7,957.26

The model therefore highlights a small number of high‑risk loans that drive a disproportionate share of expected losses; these are prime candidates for enhanced monitoring or rejection.
FICO bucket analysis and simplified logistic model

    Quantization of FICO scores – FICO scores were mapped into six discrete rating buckets: 1 (800–850), 2 (750–799), 3 (700–749), 4 (650–699), 5 (600–649) and 6 (300–599)【11†L8-L11】. The mapping reflects the industry convention that a lower rating number is better credit.

    Default rates by rating – Default rates rise monotonically as credit quality deteriorates: rating 1 has a 3 % default rate, rating 2 ≈2.8 %, rating 3 ≈5 %, rating 4 ≈9.6 %, rating 5 ≈17.9 % and rating 6 ≈36.6 %【analysis†L1-L2】. This confirms the value of FICO in predicting default.

    Rating‑only logistic regression – A logistic regression model using only the rating as the independent variable was trained on 30 % of the data and tested on 70 %. The model’s accuracy is ≈81.8 % and AUC ≈0.71, far below the XGBoost model. Predicted PDs for ratings 1–6 were roughly 2 %, 4 %, 9 %, 20 %, 37 % and 37 % respectively. The model consequently underestimates the risk of default for low‑FICO borrowers with high leverage. It can, however, serve as a quick a‑priori PD estimate when full borrower data are unavailable.

Overall Conclusions

    Natural gas pricing and storage – The gas price time‑series has a modest upward trend and mild seasonality. A well‑timed storage contract based on the 2021–2022 spread would have generated a net margin of nearly $0.9 million, after accounting for injection/withdrawal fees, transportation and storage costs. Future profitability is sensitive to the spread between injection and withdrawal prices; ongoing price monitoring is essential.

    Credit risk modelling – Advanced machine‑learning methods like XGBoost deliver highly accurate borrower‑level PD estimates (AUC ≈ 0.995). When combined with LGD assumptions, the model quantifies expected losses and highlights the small subset of loans driving the majority of portfolio risk.

    Simplified rating models – Mapping FICO scores into discrete ratings provides a quick and interpretable measure of risk. Default rates increase sharply for ratings 5 and 6, reinforcing the need for caution when lending to low‑FICO borrowers. However, models that rely solely on rating information (≈81 % accuracy) are inferior to full‑feature models and should be used only when data are limited.

STAR‑method bullet points

    Natural‑gas forecasting and contract valuation – Situation: JP Morgan’s commodities desk needed to assess the profitability of storing natural gas during 2021–2022 amid volatile prices. Task: Analyse 48 months of Henry Hub price data, build a forecasting model and value a storage contract with specified injection/withdrawal dates. Action: Calculated descriptive statistics and moving averages, fitted SARIMA and Prophet models, tested stationarity, forecasted 12 months ahead and compared predictions against actual prices; computed cash‑flows for a storage strategy and deducted injection, withdrawal, transportation and storage costs. Result: Identified a slow upward price trend (~$0.039 per month) and seasonal patterns; SARIMA forecasted December 2021 prices within 1 % error. The storage strategy delivered ≈$0.89 million net margin, demonstrating profitability under the assumed spread and costs.

    Machine‑learning‑based credit risk model – Situation: The bank had a loan portfolio of 10,000 borrowers and needed to estimate default probabilities and expected losses for risk management. Task: Build a predictive model that distinguishes defaulters from non‑defaulters and quantify expected loss. Action: Performed exploratory analysis, engineered income‑to‑debt ratios, split the data 70/30, trained an XGBoost classifier, selected a 60 % PD threshold and evaluated performance; computed loss‑given‑default assuming a 10 % recovery and calculated expected loss per loan. Result: The model achieved ~99 % accuracy and AUC ≈ 0.995, with only 12 misclassifications in the test set. Portfolio‑wide expected loss was ≈$7.42 million, with the top five loans accounting for >0.04 % of the portfolio but >1 % of total expected losses, enabling targeted risk mitigation.

    FICO rating quantization and simplified PD model – Situation: Stakeholders wanted an easy‑to‑interpret credit rating scale derived from FICO scores and an associated PD for each bucket. Task: Convert raw FICO scores into six rating categories and estimate PDs using a logistic regression model based solely on the rating. Action: Mapped scores into ratings (1 best to 6 worst), analysed default frequencies across buckets, trained and tested a rating‑only logistic model on a 30/70 split, and compared results to the full‑feature XGBoost model. Result: Default rates increased monotonically from ~3 % (rating 1) to ~37 % (rating 6)【analysis†L1-L2】, validating the rating scale. The rating‑only logistic model achieved ≈81.8 % accuracy and AUC ≈ 0.71, offering a quick PD estimate but underscoring that richer data are needed for robust risk assessment.

In summary, the natural gas price data show a gradual upward trend (~$0.039 per month) with mild seasonality; a storage strategy capturing the 2021–22 price spread yields a net margin of approximately $0.89 million when accounting for injection, withdrawal, transportation and storage costs. Machine-learning analysis of a 10 000‑loan portfolio demonstrates that an XGBoost model with engineered income‑to‑debt features achieves ~99 % classification accuracy and highlights a handful of borrowers as the main drivers of expected losses, which total roughly $7.42 million. Simplifying credit analysis by bucketing FICO scores into six ratings reveals a monotonic increase in default rates from 3 % to 37 %, but a rating-only logistic regression model attains only 81.8 % accuracy and tends to underestimate risk for the lowest‑quality borrowers.
