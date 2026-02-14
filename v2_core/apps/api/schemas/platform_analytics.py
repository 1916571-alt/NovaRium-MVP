import datetime as dt
from pydantic import BaseModel, Field, model_validator


class PlatformEventInput(BaseModel):
    event_id: str = Field(min_length=1, max_length=64)
    event_name: str = Field(min_length=1, max_length=80)
    event_time: dt.datetime | None = None
    client_ts: dt.datetime | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    session_id: str | None = Field(default=None, max_length=120)
    page_path: str | None = Field(default=None, max_length=300)
    props_json: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_context_ids(self):
        if self.workspace_id is not None and len(self.workspace_id.strip()) == 0:
            raise ValueError("workspace_id cannot be empty")
        if self.project_id is not None and len(self.project_id.strip()) == 0:
            raise ValueError("project_id cannot be empty")
        return self


class PlatformEventBatchRequest(BaseModel):
    items: list[PlatformEventInput] = Field(min_length=1, max_length=200)


class PlatformEventBatchResponse(BaseModel):
    accepted_count: int
    dropped_count: int
    dropped_reasons: list[str] = []


class PlatformDailyMetricItem(BaseModel):
    event_date: str
    workspace_id: str | None = None
    project_id: str | None = None
    event_name: str
    events_count: int
    users_count: int
    sessions_count: int
    computed_at: str


class PlatformDailyMetricListResponse(BaseModel):
    items: list[PlatformDailyMetricItem]
    count: int
