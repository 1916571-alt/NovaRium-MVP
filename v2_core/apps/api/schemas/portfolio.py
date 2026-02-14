from pydantic import BaseModel


class PortfolioSummary(BaseModel):
    experiments_total: int
    experiments_adopted: int
    avg_lift: float
    sql_submissions_total: int
    sql_correct_total: int
    sql_accuracy: float
    journey_events_total: int


class PortfolioRecentExperiment(BaseModel):
    experiment_id: str
    hypothesis: str
    decision: str | None = None
    created_at: str


class PortfolioResponse(BaseModel):
    summary: PortfolioSummary
    recent_experiments: list[PortfolioRecentExperiment]

