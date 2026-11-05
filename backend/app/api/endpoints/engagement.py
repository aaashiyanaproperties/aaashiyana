from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import Connection

from app.core.security import current_user, optional_user
from app.db.datasource import data_source
from app.schemas.api import (
    InquiryCreate,
    NewsletterCreate,
    ReportCreate,
    SavedSearchCreate,
    StatusUpdate,
    VisitCreate,
)
from app.services.engagement import EngagementService
from app.services.uploads import UploadService
from app.services.email import send_email

router = APIRouter()


@router.post("/properties/{pid}/inquiries")
def create_inquiry(
    pid: str,
    data: InquiryCreate,
    user=Depends(optional_user),
    db: Connection = Depends(data_source.get_connection),
):
    result = EngagementService(db).create_inquiry(pid, data.model_dump(), user)
    if result["owner_email"]:
        send_email(
            result["owner_email"],
            "New Aashiyana property enquiry",
            f"{result['name']} ({result['phone']}) enquired about {result['property_title']}. Reply to the interested person using your Aashiyana dashboard.",
        )
    return {
        "id": result["id"],
        "status": result["status"],
        "message": result["message"],
    }


@router.post("/properties/{pid}/visits")
def create_visit(
    pid: str,
    data: VisitCreate,
    user=Depends(optional_user),
    db: Connection = Depends(data_source.get_connection),
):
    result = EngagementService(db).create_visit(pid, data.model_dump(), user)
    if result["owner_email"]:
        send_email(
            result["owner_email"],
            "Aashiyana property visit request",
            f"{result['name']} requested a visit for {result['property_title']} at {result['scheduled_at'].isoformat()}.",
        )
    return {"id": result["id"], "status": result["status"]}


@router.get("/me/inquiries")
def my_inquiries(user=Depends(current_user), db: Connection = Depends(data_source.get_connection)):
    return EngagementService(db).my_inquiries(user.id)


@router.patch("/inquiries/{iid}")
def update_inquiry(
    iid: str,
    data: StatusUpdate,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return EngagementService(db).update_inquiry(iid, data.status, user)


@router.get("/me/visits")
def my_visits(user=Depends(current_user), db: Connection = Depends(data_source.get_connection)):
    return EngagementService(db).my_visits(user.id)


@router.post("/me/saved-searches")
def save_search(
    data: SavedSearchCreate,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return EngagementService(db).save_search(user.id, data.name, data.filters)


@router.get("/me/saved-searches")
def list_searches(user=Depends(current_user), db: Connection = Depends(data_source.get_connection)):
    return EngagementService(db).list_searches(user.id)


@router.get("/me/notifications")
def notifications(user=Depends(current_user), db: Connection = Depends(data_source.get_connection)):
    return EngagementService(db).notifications(user.id)


@router.post("/properties/{pid}/reports")
def report_property(
    pid: str,
    data: ReportCreate,
    user=Depends(optional_user),
    db: Connection = Depends(data_source.get_connection),
):
    return EngagementService(db).report(pid, data.model_dump(), user)


@router.post("/uploads")
def upload_image(
    file: UploadFile = File(...),
    user=Depends(current_user),
):
    return UploadService().upload(file)


@router.patch("/me/notifications/{nid}")
def mark_notification_read(
    nid: str,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return EngagementService(db).mark_notification_read(nid, user.id)


@router.post("/newsletter")
def subscribe_newsletter(data: NewsletterCreate, db: Connection = Depends(data_source.get_connection)):
    return EngagementService(db).subscribe(str(data.email), data.consent)


@router.patch("/visits/{vid}")
def update_visit(
    vid: str,
    data: StatusUpdate,
    user=Depends(current_user),
    db: Connection = Depends(data_source.get_connection),
):
    return EngagementService(db).update_visit(vid, data.status, user)
