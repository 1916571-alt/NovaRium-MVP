from pydantic import BaseModel, Field, model_validator


class SqlExecuteRequest(BaseModel):
    query: str = Field(min_length=1)
    max_rows: int = Field(default=100, ge=1, le=500)


class SqlExecuteResponse(BaseModel):
    columns: list[str]
    rows: list[list]
    row_count: int
    truncated: bool


class SqlChallengeCreateRequest(BaseModel):
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    prompt_md: str = Field(min_length=1)
    difficulty: str = Field(pattern="^(easy|medium|hard)$")
    expected_schema: dict = Field(default_factory=dict)
    expected_metrics: dict = Field(default_factory=dict)


class SqlChallengeItem(BaseModel):
    id: str
    project_id: str
    title: str
    prompt_md: str
    difficulty: str
    created_at: str


class SqlChallengeListResponse(BaseModel):
    items: list[SqlChallengeItem]
    count: int


class SqlSubmissionCreateRequest(BaseModel):
    sql_text: str = Field(min_length=1)


class SqlSubmissionResponse(BaseModel):
    id: int
    challenge_id: str
    user_id: str
    is_correct: bool
    feedback_json: dict
    submitted_at: str


class SqlSnippetCreateRequest(BaseModel):
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=120)
    sql_text: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class SqlSnippetUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    sql_text: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None
    is_pinned: bool | None = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if (
            self.title is None
            and self.sql_text is None
            and self.tags is None
            and self.is_pinned is None
        ):
            raise ValueError("At least one of title, sql_text, tags or is_pinned is required")
        return self


class SqlSnippetItem(BaseModel):
    id: str
    project_id: str
    author_user_id: str
    title: str
    sql_text: str
    tags: list[str]
    is_pinned: bool
    pinned_at: str | None = None
    created_at: str
    updated_at: str


class SqlSnippetListResponse(BaseModel):
    items: list[SqlSnippetItem]
    count: int
