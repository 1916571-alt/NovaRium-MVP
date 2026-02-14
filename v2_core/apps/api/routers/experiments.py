from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.deps import get_current_user
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.experiments import (
    ExperimentAnalysisResponse,
    ExperimentAnalysisPersistResponse,
    ExperimentCreateRequest,
    ExperimentItem,
    ExperimentListResponse,
    VariantCreateRequest,
    VariantItem,
    VariantListResponse,
    VariantUpdateRequest,
)
from apps.api.schemas.adoptions import AdoptionCreateRequest, AdoptionItem
from apps.api.services.adoptions import create_adoption_for_user
from apps.api.services.experiment_analysis import (
    analyze_experiment_run_for_user,
    persist_experiment_analysis_for_user,
)
from apps.api.services.experiments import (
    create_variant_for_user,
    delete_variant_for_user,
    create_experiment_for_user,
    list_variants_for_user,
    list_experiments_for_user,
    set_experiment_status_for_user,
    update_variant_for_user,
)
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/experiments")


@router.get("", response_model=ExperimentListResponse)
def list_experiments(
    project_id: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    items = [
        ExperimentItem(**x)
        for x in list_experiments_for_user(current_user.user_id, project_id)
    ]
    return ExperimentListResponse(items=items, count=len(items))


@router.post("", response_model=ExperimentItem, status_code=status.HTTP_201_CREATED)
def create_experiment(
    body: ExperimentCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = create_experiment_for_user(current_user.user_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return ExperimentItem(**row)


@router.post("/{experiment_id}/activate", response_model=ExperimentItem)
def activate_experiment(
    experiment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = set_experiment_status_for_user(current_user.user_id, experiment_id, True)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return ExperimentItem(**row)


@router.post("/{experiment_id}/deactivate", response_model=ExperimentItem)
def deactivate_experiment(
    experiment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = set_experiment_status_for_user(current_user.user_id, experiment_id, False)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return ExperimentItem(**row)


@router.get("/{experiment_id}/analysis", response_model=ExperimentAnalysisResponse)
def analyze_experiment(
    experiment_id: str,
    run_id: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = analyze_experiment_run_for_user(current_user.user_id, experiment_id, run_id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return ExperimentAnalysisResponse(**row)


@router.post(
    "/{experiment_id}/analysis/persist",
    response_model=ExperimentAnalysisPersistResponse,
    status_code=status.HTTP_201_CREATED,
)
def persist_analysis(
    experiment_id: str,
    run_id: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        analysis = analyze_experiment_run_for_user(current_user.user_id, experiment_id, run_id)
        row = persist_experiment_analysis_for_user(current_user.user_id, analysis)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return ExperimentAnalysisPersistResponse(**row)


@router.post(
    "/{experiment_id}/adopt-from-analysis",
    response_model=AdoptionItem,
    status_code=status.HTTP_201_CREATED,
)
def adopt_from_analysis(
    experiment_id: str,
    run_id: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        analysis = analyze_experiment_run_for_user(current_user.user_id, experiment_id, run_id)
        if analysis["recommendation"] != "adopt":
            raise ValueError(
                f"Recommendation is '{analysis['recommendation']}', only 'adopt' can be auto-adopted"
            )
        row = create_adoption_for_user(
            current_user.user_id,
            AdoptionCreateRequest(
                experiment_id=experiment_id,
                winning_variant_key=analysis["test_variant"],
                traffic_percentage=100.0,
                reason=(
                    f"auto-adopt run={run_id}, lift={analysis['lift']:.4f}, "
                    f"p={analysis['p_value']:.6f}, srm_p={analysis['srm_p_value']:.6f}"
                ),
            ),
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return AdoptionItem(**row)


@router.get("/{experiment_id}/variants", response_model=VariantListResponse)
def list_variants(
    experiment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    items = [
        VariantItem(**x)
        for x in list_variants_for_user(current_user.user_id, experiment_id)
    ]
    return VariantListResponse(items=items, count=len(items))


@router.post(
    "/{experiment_id}/variants",
    response_model=VariantItem,
    status_code=status.HTTP_201_CREATED,
)
def create_variant(
    experiment_id: str,
    body: VariantCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = create_variant_for_user(current_user.user_id, experiment_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return VariantItem(**row)


@router.put("/{experiment_id}/variants/{variant_key}", response_model=VariantItem)
def update_variant(
    experiment_id: str,
    variant_key: str,
    body: VariantUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = update_variant_for_user(current_user.user_id, experiment_id, variant_key, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return VariantItem(**row)


@router.delete("/{experiment_id}/variants/{variant_key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(
    experiment_id: str,
    variant_key: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        delete_variant_for_user(current_user.user_id, experiment_id, variant_key)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return None
