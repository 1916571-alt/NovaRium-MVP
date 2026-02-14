from pydantic import BaseModel, Field, model_validator


class ExperimentCreateRequest(BaseModel):
    project_id: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1, max_length=2000)
    primary_metric: str = Field(min_length=1, max_length=120)
    guardrail_metrics: list[str] = Field(default_factory=list)


class ExperimentItem(BaseModel):
    id: str
    project_id: str
    my_role: str
    hypothesis: str
    primary_metric: str
    guardrail_metrics: list[str]
    status: str
    created_by: str
    created_at: str
    started_at: str | None = None
    ended_at: str | None = None


class ExperimentListResponse(BaseModel):
    items: list[ExperimentItem]
    count: int


class ExperimentAnalysisResponse(BaseModel):
    experiment_id: str
    run_id: str
    metric_event: str
    control_variant: str
    test_variant: str
    control_users: int
    control_conversions: int
    test_users: int
    test_conversions: int
    control_rate: float
    test_rate: float
    lift: float
    z_score: float
    p_value: float
    srm_p_value: float
    srm_detected: bool
    ci_lower: float
    ci_upper: float
    recommendation: str


class ExperimentAnalysisPersistResponse(BaseModel):
    id: int
    experiment_id: str
    run_id: str
    decision: str
    created_at: str


class VariantCreateRequest(BaseModel):
    variant_key: str = Field(min_length=1, max_length=40, pattern=r"^[a-zA-Z0-9_-]+$")
    config_json: dict = Field(default_factory=dict)
    traffic_weight: float = Field(default=50.0, ge=0.0, le=100.0)


class VariantUpdateRequest(BaseModel):
    config_json: dict | None = None
    traffic_weight: float | None = Field(default=None, ge=0.0, le=100.0)

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if self.config_json is None and self.traffic_weight is None:
            raise ValueError("At least one of config_json or traffic_weight is required")
        return self


class VariantItem(BaseModel):
    id: str
    experiment_id: str
    variant_key: str
    config_json: dict
    traffic_weight: float


class VariantListResponse(BaseModel):
    items: list[VariantItem]
    count: int
