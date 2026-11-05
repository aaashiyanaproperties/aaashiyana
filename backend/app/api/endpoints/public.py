from fastapi import APIRouter, Depends
from sqlalchemy import Connection

from app.core.config import settings
from app.db.datasource import data_source
from app.schemas.api import ContactMessageCreate
from app.services.catalog import CatalogService
from app.services.engagement import EngagementService
from app.services.email import send_email

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "aashiyana-api", "environment": settings.environment}


@router.get("/locations")
def locations(q: str | None = None, db: Connection = Depends(data_source.get_connection)):
    return CatalogService(db).locations(q)


@router.get("/projects")
def projects(city: str | None = None, db: Connection = Depends(data_source.get_connection)):
    return CatalogService(db).projects(city)


@router.get("/agents")
def agents(db: Connection = Depends(data_source.get_connection)):
    return CatalogService(db).agents()


@router.get("/developers")
def developers(db: Connection = Depends(data_source.get_connection)):
    return CatalogService(db).developers()


@router.get("/blog")
def public_blog(db: Connection = Depends(data_source.get_connection)):
    return CatalogService(db).blog()


@router.get("/categories")
def categories(db: Connection = Depends(data_source.get_connection)):
    return CatalogService(db).categories()


@router.post("/contact-messages")
def create_contact_message(
    data: ContactMessageCreate,
    db: Connection = Depends(data_source.get_connection),
):
    result = EngagementService(db).contact_message(data.model_dump())
    if settings.contact_email:
        send_email(
            settings.contact_email,
            f"Aashiyana contact: {result['topic']}",
            f"From: {result['name']} <{result['email']}>\n\n{result['body']}",
        )
    return {
        "id": result["id"],
        "status": result["status"],
        "message": result["message"],
    }
