from pydantic import BaseModel, Field


class SimulationBootstrapRequest(BaseModel):
    experiment_id: str | None = None
    run_id: str | None = None
    template: str = Field(default="commerce", pattern=r"^(commerce|content|saas)$")
    seed_preset: str = Field(default="standard", pattern=r"^(beginner|standard|advanced)$")
    user_count: int | None = Field(default=None, ge=200, le=20000)
    test_split: float = Field(default=0.5, gt=0.0, lt=1.0)
    control_purchase_rate: float | None = Field(default=None, ge=0.01, le=0.8)
    test_purchase_rate: float | None = Field(default=None, ge=0.01, le=0.9)
    seed_sql_challenges: bool = True
    seed: int = Field(default=42, ge=1, le=10_000_000)


class SimulationBootstrapResponse(BaseModel):
    project_id: str
    experiment_id: str
    run_id: str
    template: str
    seed_preset: str
    user_count: int
    assignments_inserted: int
    events_inserted: int
    control_users: int
    test_users: int
    control_purchase_rate: float
    test_purchase_rate: float
    sql_challenges_seeded: int


class FunnelStepItem(BaseModel):
    step_index: int
    step_name: str
    users_count: int
    conversion_rate: float
    dropoff_rate: float


class FunnelOverviewResponse(BaseModel):
    project_id: str
    run_id: str | None
    experiment_id: str | None
    template: str
    total_users: int
    bottleneck_step: str | None
    steps: list[FunnelStepItem]


class SimulationTemplateItem(BaseModel):
    key: str
    label: str
    description: str
    default_user_count: int
    default_control_purchase_rate: float
    default_test_purchase_rate: float
    preset_defaults: dict[str, dict]


class SimulationTemplateListResponse(BaseModel):
    items: list[SimulationTemplateItem]
    count: int
