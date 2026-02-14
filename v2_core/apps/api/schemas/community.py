from pydantic import BaseModel, Field


class CommunityPostCreateRequest(BaseModel):
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    body_md: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    experiment_id: str | None = None


class CommunityPostItem(BaseModel):
    id: str
    project_id: str
    experiment_id: str | None = None
    author_user_id: str
    title: str
    body_md: str
    tags: list[str]
    created_at: str
    comment_count: int = 0
    fork_count: int = 0
    rank_score: float = 0.0


class CommunityPostListResponse(BaseModel):
    items: list[CommunityPostItem]
    count: int


class CommunityCommentCreateRequest(BaseModel):
    body_md: str = Field(min_length=1)


class CommunityCommentItem(BaseModel):
    id: int
    post_id: str
    author_user_id: str
    body_md: str
    created_at: str


class CommunityCommentListResponse(BaseModel):
    items: list[CommunityCommentItem]
    count: int


class CommunityForkCreateRequest(BaseModel):
    source_experiment_id: str = Field(min_length=1)
    target_project_id: str = Field(min_length=1)


class CommunityForkResponse(BaseModel):
    source_experiment_id: str
    forked_experiment_id: str
    forked_by: str
    created_at: str
