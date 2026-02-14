from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.core.config import settings
from apps.api.routers.adoptions import router as adoptions_router
from apps.api.routers.analytics import router as analytics_router
from apps.api.routers.auth import router as auth_router
from apps.api.routers.community import router as community_router
from apps.api.routers.events import router as events_router
from apps.api.routers.experiments import router as experiments_router
from apps.api.routers.health import router as health_router
from apps.api.routers.journeys import router as journeys_router
from apps.api.routers.portfolio import router as portfolio_router
from apps.api.routers.projects import router as projects_router
from apps.api.routers.scenarios import router as scenarios_router
from apps.api.routers.sql_lab import router as sql_lab_router
from apps.api.routers.workspaces import router as workspaces_router


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix, tags=["health"])
app.include_router(auth_router, prefix=settings.api_prefix, tags=["auth"])
app.include_router(workspaces_router, prefix=settings.api_prefix, tags=["workspaces"])
app.include_router(projects_router, prefix=settings.api_prefix, tags=["projects"])
app.include_router(events_router, prefix=settings.api_prefix, tags=["events"])
app.include_router(experiments_router, prefix=settings.api_prefix, tags=["experiments"])
app.include_router(adoptions_router, prefix=settings.api_prefix, tags=["adoptions"])
app.include_router(analytics_router, prefix=settings.api_prefix, tags=["analytics"])
app.include_router(journeys_router, prefix=settings.api_prefix, tags=["journeys"])
app.include_router(portfolio_router, prefix=settings.api_prefix, tags=["portfolio"])
app.include_router(sql_lab_router, prefix=settings.api_prefix, tags=["sql"])
app.include_router(community_router, prefix=settings.api_prefix, tags=["community"])
app.include_router(scenarios_router, prefix=settings.api_prefix, tags=["scenarios"])
