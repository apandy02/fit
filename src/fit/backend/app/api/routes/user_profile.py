from fastapi import APIRouter, Depends, HTTPException

from fit.backend.app.api.models.user_profile import (
    ProfileResponse,
    ProfileUpdateRequest,
    RestrictionChangeRequest,
    RestrictionListResponse,
)
from fit.backend.auth import get_current_user_id
from fit.backend.database.database import Database
from fit.backend.app.deps import get_database_service


router = APIRouter(tags=["profile"], prefix="/profile")


@router.get("", response_model=ProfileResponse)
def get_profile(user_id: int = Depends(get_current_user_id), database_service: Database = Depends(get_database_service)):
    data = database_service.profile.get_profile_data(user_id)
    restrictions = data.get("dietary_restrictions", "") or ""
    restrictions_list = [] if restrictions == "" else restrictions.split(",")
    print(f"data: {data}")
    return ProfileResponse(
        user_id=user_id,
        name=data.get("name"),
        email=data.get("email"),
        gender=data.get("gender"),
        date_of_birth=data.get("date_of_birth"),
        units=data.get("units"),
        dietary_restrictions=restrictions_list,
        activity_level=data.get("activity_level"),
        weight_goal=str(data.get("weight_goal")) if data.get("weight_goal") is not None else None,
        fitness_goal=data.get("fitness_goal"),
        onboarding_stage=data.get("onboarding_stage"),
    )


@router.post("", response_model=ProfileResponse)
def update_profile(body: ProfileUpdateRequest, user_id: int = Depends(get_current_user_id), database_service: Database = Depends(get_database_service)):
    try:
        form_data = body.model_dump(exclude_none=True)
        print(f"form_data: {form_data}")
        form_data["user_id"] = user_id
        # join restrictions as comma-separated string for storage
        if "dietary_restrictions" in form_data:
            form_data["dietary_restrictions"] = ",".join(form_data["dietary_restrictions"]) if form_data["dietary_restrictions"] else ""
        ok = database_service.profile.update_profile(form_data)
        if ok is False:
            raise HTTPException(status_code=500, detail="Failed to update profile")
        data = database_service.profile.get_profile_data(user_id)
        restrictions = data.get("dietary_restrictions", "") or ""
        restrictions_list = [] if restrictions == "" else restrictions.split(",")
        print(f"data: {data}")
        return ProfileResponse(
            user_id=user_id,
            name=data.get("name"),
            email=data.get("email"),
            gender=data.get("gender"),
            date_of_birth=data.get("date_of_birth"),
            units=data.get("units"),
            dietary_restrictions=restrictions_list,
            activity_level=data.get("activity_level"),
            weight_goal=str(data.get("weight_goal")) if data.get("weight_goal") is not None else None,
            fitness_goal=data.get("fitness_goal"),
            onboarding_stage=data.get("onboarding_stage"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restrictions/add", response_model=RestrictionListResponse)
def add_restriction(body: RestrictionChangeRequest, user_id: int = Depends(get_current_user_id), database_service: Database = Depends(get_database_service)):
    # Load current restrictions from DB to avoid client-side drift
    data = database_service.profile.get_profile_data(user_id)
    current = data.get("dietary_restrictions", "") or ""
    restrictions = set([] if current == "" else current.split(","))
    if body.restriction:
        restrictions.add(body.restriction)
    new_csv = ",".join(sorted(list(restrictions)))
    ok = database_service.profile.update_profile({"user_id": user_id, "dietary_restrictions": new_csv})
    if ok is False:
        raise HTTPException(status_code=500, detail="Failed to update restrictions")
    return RestrictionListResponse(restrictions=sorted(list(restrictions)))


@router.post("/restrictions/remove", response_model=RestrictionListResponse)
def remove_restriction(body: RestrictionChangeRequest, user_id: int = Depends(get_current_user_id), database_service: Database = Depends(get_database_service)):
    data = database_service.profile.get_profile_data(user_id)
    current = data.get("dietary_restrictions", "") or ""
    restrictions = [] if current == "" else current.split(",")
    new_list = [r for r in restrictions if r != body.restriction]
    new_csv = ",".join(new_list)
    ok = database_service.profile.update_profile({"user_id": user_id, "dietary_restrictions": new_csv})
    if ok is False:
        raise HTTPException(status_code=500, detail="Failed to update restrictions")
    return RestrictionListResponse(restrictions=new_list)


