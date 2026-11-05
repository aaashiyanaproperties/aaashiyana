from fastapi import APIRouter, Depends, Query
from sqlalchemy import Connection

from app.core.security import current_user
from app.db.datasource import data_source
from app.schemas.api import PropertyCreate, PropertyDraftCreate
from app.services.properties import PropertyService

router = APIRouter()


@router.get("/properties")
def search_properties(
    q: str | None = None,
    city: str | None = None,
    locality: str | None = None,
    transaction_type: str | None = None,
    property_type: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    bedrooms: int | None = None,
    bathrooms: int | None = None,
    furnishing: str | None = None,
    possession_status: str | None = None,
    pincode: str | None = None,
    verified: bool | None = None,
    featured: bool | None = None,
    parking: bool | None = None,
    amenity: str | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    posted_within_days: int | None = Query(default=None, ge=1, le=3650),
    sort: str = "newest",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=60),
    db: Connection = Depends(data_source.get_connection),
):
    return PropertyService(db).search(
        q=q,
        city=city,
        locality=locality,
        transaction_type=transaction_type,
        property_type=property_type,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        furnishing=furnishing,
        possession_status=possession_status,
        pincode=pincode,
        verified=verified,
        featured=featured,
        parking=parking,
        amenity=amenity,
        min_area=min_area,
        max_area=max_area,
        posted_within_days=posted_within_days,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/properties/{slug}")
def property_detail(slug: str, db: Connection = Depends(data_source.get_connection)):
    return PropertyService(db).get_published(slug)


@router.post("/properties")
def create_property(
    data: PropertyCreate,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return PropertyService(db).create(data.model_dump(), user.id)


@router.patch("/properties/{pid}")
def update_property(
    pid: str,
    data: PropertyCreate,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return PropertyService(db).update(pid, data.model_dump(), user)


@router.delete("/properties/{pid}")
def delete_property(
    pid: str,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return PropertyService(db).delete(pid, user)


@router.get("/me/properties")
def my_properties(user=Depends(current_user), db: Connection = Depends(data_source.get_connection)):
    return PropertyService(db).my_properties(user.id)


@router.post("/properties/{pid}/favourite")
def add_favourite(
    pid: str,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return PropertyService(db).add_favourite(pid, user.id)


@router.delete("/properties/{pid}/favourite")
def remove_favourite(
    pid: str,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return PropertyService(db).remove_favourite(pid, user.id)


@router.get("/me/favourites")
def favourites(user=Depends(current_user), db: Connection = Depends(data_source.get_connection)):
    return PropertyService(db).favourites(user.id)


@router.post("/properties/drafts")
def save_property_draft(
    data: PropertyDraftCreate,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return PropertyService(db).create_draft(data.model_dump(), user.id)
