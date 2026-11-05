from fastapi import APIRouter, Depends
from sqlalchemy import Connection

from app.core.security import require_roles
from app.db.datasource import data_source
from app.schemas.api import (
    AgentCreate,
    BlogPostCreate,
    CategoryCreate,
    DeveloperCreate,
    FeatureUpdate,
    LocationCreate,
    ModerationDecision,
    ProjectCreate,
    SettingUpdate,
    StatusUpdate,
)
from app.services.admin import AdminService
from app.services.catalog import CatalogService

router = APIRouter()


@router.get("/admin/overview")
def admin_overview(
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).overview()


@router.get("/admin/properties")
def admin_properties(
    status: str | None = None,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).properties(status)


@router.post("/admin/properties/{pid}/moderate")
def moderate(
    pid: str,
    data: ModerationDecision,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).moderate(pid, data.decision, data.reason, user.id)


@router.patch("/admin/users/{uid}/roles")
def set_roles(
    uid: str,
    roles: list[str],
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).set_roles(uid, roles, user.id)


@router.get("/admin/reports")
def admin_reports(
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).reports()


@router.get("/admin/users")
def admin_users(
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).users_list()


@router.patch("/admin/reports/{rid}")
def update_report(
    rid: str,
    data: StatusUpdate,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).update_report(rid, data.status, user.id)


@router.get("/admin/projects")
def admin_projects(
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).projects()


@router.delete("/admin/properties/{pid}")
def admin_delete_property(
    pid: str,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).delete_property(pid, user.id)


@router.post("/admin/projects")
def create_project(
    data: ProjectCreate,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).create_project(data.model_dump(), user.id)


@router.post("/admin/developers")
def create_developer(
    data: DeveloperCreate,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).create_developer(data.model_dump(), user.id)


@router.post("/admin/blog")
def create_blog_post(
    data: BlogPostCreate,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).create_blog_post(data.model_dump(), user.id)


@router.get("/admin/audit-logs")
def audit_logs(
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).audit_logs()


@router.get("/admin/settings")
def admin_settings(
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).settings()


@router.put("/admin/settings/{key}")
def update_setting(
    key: str,
    data: SettingUpdate,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).update_setting(key, data.value, user.id)


@router.post("/admin/categories")
def create_category(
    data: CategoryCreate,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return CatalogService(db).create_category(data.model_dump(), user.id)


@router.patch("/admin/properties/{pid}/feature")
def feature_property(
    pid: str,
    data: FeatureUpdate,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).feature_property(pid, data.featured, user.id)


@router.post("/admin/locations")
def create_location(
    data: LocationCreate,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return CatalogService(db).create_location(data.model_dump(), user.id)


@router.post("/admin/agents")
def create_agent(
    data: AgentCreate,
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return CatalogService(db).create_agent(data.model_dump(), user.id)


@router.get("/admin/contact-messages")
def admin_contact_messages(
    user=Depends(require_roles("admin")),
    db: Connection = Depends(data_source.get_connection),
):
    return AdminService(db).contact_messages()
