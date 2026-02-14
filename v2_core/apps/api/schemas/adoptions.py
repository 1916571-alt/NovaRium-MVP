from pydantic import BaseModel, Field


class AdoptionCreateRequest(BaseModel):
    experiment_id: str = Field(min_length=1)
    winning_variant_key: str = Field(min_length=1, max_length=120)
    traffic_percentage: float = Field(default=100.0, ge=0.0, le=100.0)
    reason: str | None = None


class AdoptionRolloutRequest(BaseModel):
    traffic_percentage: float = Field(ge=0.0, le=100.0)


class AdoptionItem(BaseModel):
    id: int
    experiment_id: str
    winning_variant_key: str
    traffic_percentage: float
    reason: str | None = None
    adopted_by: str
    adopted_at: str
    rolled_back_at: str | None = None

