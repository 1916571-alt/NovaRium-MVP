import datetime as dt

from pydantic import BaseModel, Field, model_validator


ALLOWED_EVENT_NAMES = {
    "session_start",
    "view_home",
    "view_detail",
    "click_cta",
    "add_to_cart",
    "start_checkout",
    "purchase",
    "bounce",
}


class EventIngestItem(BaseModel):
    project_id: str = Field(min_length=1)
    user_key: str = Field(min_length=1, max_length=180)
    event_name: str = Field(min_length=1, max_length=80)
    event_time: dt.datetime | None = None
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=120)
    experiment_id: str | None = None
    run_id: str | None = Field(default=None, max_length=120)
    value: float = 0.0
    schema_version: str = Field(default="event-v1", min_length=1, max_length=40)
    source: str = Field(default="sdk", min_length=1, max_length=40)
    props_json: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_item(self):
        if not self.project_id.strip():
            raise ValueError("project_id cannot be empty")
        if not self.user_key.strip():
            raise ValueError("user_key cannot be empty")
        if self.event_name not in ALLOWED_EVENT_NAMES:
            allowed = ", ".join(sorted(ALLOWED_EVENT_NAMES))
            raise ValueError(f"event_name must be one of: {allowed}")
        if self.idempotency_key is not None and not self.idempotency_key.strip():
            raise ValueError("idempotency_key cannot be blank")
        return self


class EventIngestBatchRequest(BaseModel):
    items: list[EventIngestItem] = Field(min_length=1, max_length=500)


class EventIngestBatchResponse(BaseModel):
    accepted_count: int
    duplicated_count: int
    dropped_count: int
    dropped_reasons: list[str] = Field(default_factory=list)
