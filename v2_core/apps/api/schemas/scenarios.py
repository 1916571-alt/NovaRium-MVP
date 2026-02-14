from pydantic import BaseModel, Field


class ScenarioExportResponse(BaseModel):
    schema_version: str
    exported_at: str
    source_project_id: str
    source_project_name: str
    payload: dict


class ScenarioImportRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    project_name: str = Field(min_length=1, max_length=120)
    schema_version: str | None = None
    payload: dict


class ScenarioImportResponse(BaseModel):
    project_id: str
    project_name: str
    imported_experiments: int
    imported_variants: int
    imported_sql_challenges: int
    imported_feature_states: int
    imported_community_posts: int


class ScenarioImportValidateResponse(BaseModel):
    accepted_schema_version: str
    normalized_counts: dict
    warnings: list[str] = []


class ScenarioShareCreateRequest(BaseModel):
    project_id: str = Field(min_length=1)
    schema_version: str | None = None
    expires_hours: int = Field(default=24, ge=1, le=24 * 30)


class ScenarioShareCreateResponse(BaseModel):
    share_token: str
    expires_at: str
    schema_version: str


class ScenarioShareRevokeResponse(BaseModel):
    revoked: bool
    revoked_at: str
