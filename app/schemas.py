"""
Request and response models. Keeping these separate from the route
functions makes both easier to read, and gives FastAPI everything it
needs to generate the /docs page and validate input automatically.
"""

from pydantic import BaseModel, Field


class BorrowerInput(BaseModel):
    customer_id: int = Field(..., examples=[8153374])
    credit_lines_outstanding: int = Field(..., ge=0, examples=[0])
    loan_amt_outstanding: float = Field(..., gt=0, examples=[5221.5])
    total_debt_outstanding: float = Field(..., ge=0, examples=[3915.5])
    income: float = Field(..., gt=0, examples=[78039.4])
    years_employed: int = Field(..., ge=0, examples=[5])
    fico_score: int = Field(..., ge=300, le=850, examples=[605])


class PredictionResult(BaseModel):
    customer_id: int
    prob_default: float
    credit_rating: int
    risk_label: str
    expected_loss: float
    saved_to_db: bool


class RatingBreakdownItem(BaseModel):
    rating: int
    risk_label: str
    borrowers: int
    avg_pd: float
    total_expected_loss: float


class FicoBucketItem(BaseModel):
    bucket: str
    total_borrowers: int
    default_rate_pct: float
    avg_income: float


class TopRiskBorrower(BaseModel):
    customer_id: int
    fico_score: int
    income: float
    prob_default: float
    expected_loss: float
    risk_label: str


class PortfolioOverview(BaseModel):
    total_loans: int
    total_scored: int
    avg_prob_default: float | None
    total_expected_loss: float | None
    high_risk_pct: float | None
