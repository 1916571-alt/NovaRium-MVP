from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)


class ProjectItem(BaseModel):
    id: str
    workspace_id: str
    name: str
    my_role: str
    created_at: str


class ProjectListResponse(BaseModel):
    items: list[ProjectItem]
    count: int
