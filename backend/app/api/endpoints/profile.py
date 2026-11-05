from fastapi import APIRouter, Depends
from sqlalchemy import Connection

from app.core.security import current_user
from app.db.datasource import data_source
from app.schemas.api import ProfileUpdate
from app.services.profile import ProfileService

router = APIRouter()


@router.get("/me")
def me(user=Depends(current_user), db: Connection = Depends(data_source.get_connection)):
    return ProfileService(db).get(user)


@router.patch("/me")
def update_profile(
    data: ProfileUpdate,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return ProfileService(db).update(user, data.model_dump())
