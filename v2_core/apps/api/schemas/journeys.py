from pydantic import BaseModel


class JourneyPatchItem(BaseModel):
    id: int
    source_type: str
    source_id: str | None = None
    patch_json: dict
    created_at: str


class JourneyEventItem(BaseModel):
    id: int
    event_type: str
    payload_json: dict
    created_at: str


class MyJourneyResponse(BaseModel):
    journey_id: str
    user_id: str
    project_id: str
    start_state_json: dict
    current_state_json: dict
    updated_at: str
    patches: list[JourneyPatchItem]
    events: list[JourneyEventItem]

