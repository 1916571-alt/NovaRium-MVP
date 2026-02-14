from pydantic import BaseModel, Field


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class WorkspaceRetentionUpdateRequest(BaseModel):
    simulation_retention_days: int = Field(ge=1, le=365)


class WorkspaceMemberAddRequest(BaseModel):
    user_id: str = Field(min_length=1)
    role: str = Field(pattern="^(owner|editor|viewer)$")


class WorkspaceItem(BaseModel):
    id: str
    owner_user_id: str
    name: str
    simulation_retention_days: int
    my_role: str
    created_at: str


class WorkspaceListResponse(BaseModel):
    items: list[WorkspaceItem]
    count: int


class WorkspaceRetentionAuditItem(BaseModel):
    id: int
    workspace_id: str
    changed_by_user_id: str
    old_retention_days: int
    new_retention_days: int
    changed_at: str


class WorkspaceRetentionAuditListResponse(BaseModel):
    items: list[WorkspaceRetentionAuditItem]
    count: int
