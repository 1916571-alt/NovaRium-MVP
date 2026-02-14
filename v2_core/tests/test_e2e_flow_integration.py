import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.core.config import settings
from apps.api.db.session import get_db_conn
from apps.api.schemas.adoptions import AdoptionCreateRequest
from apps.api.schemas.community import CommunityCommentCreateRequest, CommunityForkCreateRequest, CommunityPostCreateRequest
from apps.api.schemas.experiments import ExperimentCreateRequest
from apps.api.schemas.projects import ProjectCreateRequest
from apps.api.schemas.sql_lab import SqlChallengeCreateRequest, SqlSubmissionCreateRequest
from apps.api.schemas.workspaces import WorkspaceCreateRequest
from apps.api.services.adoptions import create_adoption_for_user
from apps.api.services.community import create_comment_for_user, create_post_for_user, fork_experiment_for_user
from apps.api.services.experiment_analysis import analyze_experiment_run_for_user, persist_experiment_analysis_for_user
from apps.api.services.experiments import create_experiment_for_user
from apps.api.services.journeys import get_my_journey_for_project
from apps.api.services.portfolio import get_portfolio_for_user
from apps.api.services.projects import create_project_for_user
from apps.api.services.sql_lab import create_challenge_for_user, execute_readonly_sql, submit_challenge_for_user
from apps.api.services.users import ensure_app_user
from apps.api.services.workspaces import create_workspace_for_user


def _should_run_integration() -> bool:
    return os.getenv("RUN_DB_INTEGRATION") == "1" and bool(settings.database_url)


@pytest.mark.skipif(not _should_run_integration(), reason="DB integration disabled")
def test_e2e_learning_flow():
    user_id = str(uuid.uuid4())
    run_id = f"run_{uuid.uuid4().hex[:10]}"

    workspace_id = None
    project_id = None
    experiment_id = None

    # Guard: migrations applied
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("select 1 from experiments limit 1")
    except Exception:
        pytest.skip("Required tables not present; apply migrations first")

    try:
        ensure_app_user(user_id, f"{user_id}@local.invalid")

        ws = create_workspace_for_user(user_id, WorkspaceCreateRequest(name="e2e-ws"))
        workspace_id = ws["id"]

        pj = create_project_for_user(
            user_id,
            ProjectCreateRequest(workspace_id=workspace_id, name="e2e-project"),
        )
        project_id = pj["id"]

        # SQL stage: execute and challenge submission
        sql_res = execute_readonly_sql(user_id, "select 1 as x", 10)
        assert sql_res["row_count"] == 1

        ch = create_challenge_for_user(
            user_id,
            SqlChallengeCreateRequest(
                project_id=project_id,
                title="count one",
                prompt_md="return a single row x=1",
                difficulty="easy",
                expected_schema={"columns": ["x"]},
                expected_metrics={
                    "row_count": 1,
                    "expected_rows": [{"x": 1}],
                    "numeric_tolerance": 0.0,
                    "unordered_rows": True,
                },
            ),
        )
        sub = submit_challenge_for_user(
            user_id,
            ch["id"],
            SqlSubmissionCreateRequest(sql_text="select 1 as x"),
        )
        assert sub["is_correct"] is True

        # Experiment stage
        exp = create_experiment_for_user(
            user_id,
            ExperimentCreateRequest(
                project_id=project_id,
                hypothesis="B variant improves click rate",
                primary_metric="CTR",
                guardrail_metrics=["cvr"],
            ),
        )
        experiment_id = exp["id"]

        # Seed assignments/events for a strong positive outcome
        with get_db_conn(user_id=user_id) as conn:
            with conn.cursor() as cur:
                assignments = []
                events = []
                n = 800
                c_conv = 80    # 10%
                t_conv = 152   # 19%
                for i in range(n):
                    c_uid = f"c_{i}"
                    t_uid = f"t_{i}"
                    assignments.append((project_id, experiment_id, c_uid, "A", run_id))
                    assignments.append((project_id, experiment_id, t_uid, "B", run_id))
                    if i < c_conv:
                        events.append((project_id, experiment_id, c_uid, run_id, "click_cta", 0))
                    if i < t_conv:
                        events.append((project_id, experiment_id, t_uid, run_id, "click_cta", 0))

                cur.executemany(
                    """
                    insert into assignments (project_id, experiment_id, user_key, variant_key, run_id)
                    values (%s::uuid, %s::uuid, %s, %s, %s)
                    """,
                    assignments,
                )
                cur.executemany(
                    """
                    insert into events (project_id, experiment_id, user_key, run_id, event_name, value)
                    values (%s::uuid, %s::uuid, %s, %s, %s, %s)
                    """,
                    events,
                )

        analysis = analyze_experiment_run_for_user(user_id, experiment_id, run_id)
        assert analysis["recommendation"] == "adopt"
        persisted = persist_experiment_analysis_for_user(user_id, analysis)
        assert persisted["decision"] == "adopt"

        adoption = create_adoption_for_user(
            user_id,
            AdoptionCreateRequest(
                experiment_id=experiment_id,
                winning_variant_key=analysis["test_variant"],
                traffic_percentage=100.0,
                reason="e2e adopt",
            ),
        )
        assert adoption["id"] > 0

        # Journey stage
        journey = get_my_journey_for_project(user_id, project_id)
        assert journey is not None
        feature_key = f"experiment:{experiment_id}"
        assert feature_key in (journey["current_state_json"].get("features") or {})

        # Community stage
        post = create_post_for_user(
            user_id,
            CommunityPostCreateRequest(
                project_id=project_id,
                experiment_id=experiment_id,
                title="E2E result",
                body_md="We adopted variant B based on analysis.",
                tags=["e2e", "abtest", "sql"],
            ),
        )
        comment = create_comment_for_user(
            user_id,
            post["id"],
            CommunityCommentCreateRequest(body_md="Looks reproducible."),
        )
        assert comment["id"] > 0

        fork = fork_experiment_for_user(
            user_id,
            CommunityForkCreateRequest(
                source_experiment_id=experiment_id,
                target_project_id=project_id,
            ),
        )
        assert fork["forked_experiment_id"] != experiment_id

        # Portfolio stage
        pf = get_portfolio_for_user(user_id)
        assert pf["summary"]["experiments_total"] >= 1
        assert pf["summary"]["experiments_adopted"] >= 1
        assert pf["summary"]["sql_submissions_total"] >= 1

    finally:
        if workspace_id:
            try:
                with get_db_conn(user_id=user_id) as conn:
                    with conn.cursor() as cur:
                        cur.execute("delete from workspaces where id = %s::uuid", (workspace_id,))
            except Exception:
                pass
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from users where id = %s::uuid", (user_id,))

