from fastapi import APIRouter, Depends

from apps.api.deps import get_current_user
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.portfolio import PortfolioResponse
from apps.api.services.portfolio import get_portfolio_for_user
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/portfolio")


@router.get("/me", response_model=PortfolioResponse)
def get_my_portfolio(current_user: CurrentUser = Depends(get_current_user)):
    ensure_app_user(current_user.user_id, current_user.email)
    row = get_portfolio_for_user(current_user.user_id)
    return PortfolioResponse(**row)

