import re, uuid, os, mimetypes
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc
from app.db.session import get_db
from app.models import *
from app.schemas.api import *
from app.core.security import current_user, optional_user, require_roles
from app.core.config import settings
from app.services.email import send_email

router=APIRouter()

def slugify(value): return re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",value.lower())).strip("-")
def property_out(p):
    return {"id":p.id,"property_id":p.property_id,"slug":p.slug,"title":p.title,"description":p.description,"transaction_type":p.transaction_type,"property_type":p.property_type,"status":p.status,"city":p.city,"state":p.state,"locality":p.locality,"address":p.address,"pincode":p.pincode,"price":float(p.price),"maintenance":float(p.maintenance) if p.maintenance is not None else None,"deposit":float(p.deposit) if p.deposit is not None else None,"bedrooms":p.bedrooms,"bathrooms":p.bathrooms,"balconies":p.balconies,"carpet_area":p.carpet_area,"builtup_area":p.builtup_area,"furnishing":p.furnishing,"parking":p.parking,"floor_number":p.floor_number,"total_floors":p.total_floors,"facing":p.facing,"age_years":p.age_years,"latitude":p.latitude,"longitude":p.longitude,"possession_status":p.possession_status,"rera_number":p.rera_number,"rera_verified":p.rera_verified,"featured":p.featured,"demo":p.demo,"images":[i.url for i in p.images],"amenities":[a.amenity.name for a in p.amenities if a.amenity],"created_at":p.created_at}

def get_property(db,pid):
    query=db.query(Property).options(joinedload(Property.images),joinedload(Property.amenities).joinedload(PropertyAmenity.amenity))
    p=query.filter(or_(Property.slug==pid,Property.property_id==pid)).first()
    if p is None and re.fullmatch(r"[0-9a-fA-F-]{36}",pid): p=query.filter(Property.id==pid).first()
    if not p: raise HTTPException(404,"Property not found")
    return p

def notify(db,user_id,title,body):
    if user_id: db.add(Notification(user_id=user_id,title=title,body=body))

@router.get("/health")
def health(): return {"status":"ok","service":"aashiyana-api","environment":settings.environment}

@router.get("/properties")
def search_properties(db:Session=Depends(get_db), q:str|None=None, city:str|None=None, locality:str|None=None, transaction_type:str|None=None, property_type:str|None=None, min_price:float|None=None, max_price:float|None=None, bedrooms:int|None=None, bathrooms:int|None=None, furnishing:str|None=None, possession_status:str|None=None, pincode:str|None=None, verified:bool|None=None, featured:bool|None=None, parking:bool|None=None, amenity:str|None=None, min_area:float|None=None, max_area:float|None=None, posted_within_days:int|None=Query(None,ge=1,le=3650), sort:str="newest", page:int=Query(1,ge=1), page_size:int=Query(12,ge=1,le=60)):
    query=db.query(Property).options(joinedload(Property.images),joinedload(Property.amenities).joinedload(PropertyAmenity.amenity)).filter(Property.status=="published")
    if q:
        for term in [part.strip() for part in q.split(",") if part.strip()]:
            query=query.filter(or_(Property.title.ilike(f"%{term}%"),Property.locality.ilike(f"%{term}%"),Property.city.ilike(f"%{term}%"),Property.pincode.ilike(f"%{term}%")))
    for col,val in [(Property.city,city),(Property.locality,locality),(Property.transaction_type,transaction_type),(Property.property_type,property_type),(Property.furnishing,furnishing),(Property.possession_status,possession_status),(Property.pincode,pincode)]:
        if val: query=query.filter(col.ilike(val) if col in (Property.city,Property.locality) else col==val)
    if min_price is not None: query=query.filter(Property.price>=min_price)
    if max_price is not None: query=query.filter(Property.price<=max_price)
    if bedrooms is not None: query=query.filter(Property.bedrooms>=bedrooms)
    if bathrooms is not None: query=query.filter(Property.bathrooms>=bathrooms)
    if verified is not None: query=query.filter(Property.rera_verified==verified)
    if featured is not None: query=query.filter(Property.featured==featured)
    if parking: query=query.filter(Property.parking>0)
    if min_area is not None: query=query.filter(or_(Property.carpet_area>=min_area,Property.builtup_area>=min_area))
    if max_area is not None: query=query.filter(or_(Property.carpet_area<=max_area,Property.builtup_area<=max_area))
    if posted_within_days: query=query.filter(Property.created_at>=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(days=posted_within_days))
    if amenity: query=query.join(PropertyAmenity).join(Amenity).filter(Amenity.name.ilike(f"%{amenity}%"))
    total=query.count()
    if sort=="price_asc": query=query.order_by(Property.price.asc())
    elif sort=="price_desc": query=query.order_by(Property.price.desc())
    elif sort=="oldest": query=query.order_by(Property.created_at.asc())
    elif sort=="relevance": query=query.order_by(Property.featured.desc(),Property.created_at.desc())
    else: query=query.order_by(Property.created_at.desc())
    rows=query.offset((page-1)*page_size).limit(page_size).all()
    return {"items":[property_out(p) for p in rows],"total":total,"page":page,"page_size":page_size,"pages":(total+page_size-1)//page_size}

@router.get("/properties/{slug}")
def property_detail(slug:str,db:Session=Depends(get_db)):
    p=get_property(db,slug)
    if p.status!="published": raise HTTPException(404,"Property not found")
    return property_out(p)

@router.post("/properties")
def create_property(data:PropertyCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if data.transaction_type not in ["buy","rent","lease"]: raise HTTPException(422,"Invalid transaction type")
    if data.status not in ["draft","pending"]: raise HTTPException(422,"New listings must be draft or pending")
    slug=slugify(data.title+"-"+data.city+"-"+uuid.uuid4().hex[:6])
    values=data.model_dump(exclude={"amenities","images","status"})
    p=Property(**values,owner_id=user.id,slug=slug,property_id="AA-"+uuid.uuid4().hex[:8].upper(),status=data.status)
    db.add(p); db.flush()
    for i,url in enumerate(data.images[:20]): db.add(PropertyImage(property_id=p.id,url=url,position=i,is_cover=i==0))
    for name in set(data.amenities):
        amenity=db.query(Amenity).filter(Amenity.name==name).first()
        if not amenity: amenity=Amenity(name=name); db.add(amenity); db.flush()
        db.add(PropertyAmenity(property_id=p.id,amenity_id=amenity.id))
    db.commit(); db.refresh(p); return property_out(get_property(db,p.id))

@router.patch("/properties/{pid}")
def update_property(pid:str,data:PropertyCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    p=get_property(db,pid)
    if p.owner_id!=user.id and "admin" not in {r.role for r in user.roles}: raise HTTPException(403,"You cannot edit this listing")
    for k,v in data.model_dump(exclude={"amenities","images","status"}).items(): setattr(p,k,v)
    p.images.clear(); p.amenities.clear(); db.flush()
    for i,url in enumerate(data.images[:20]): db.add(PropertyImage(property_id=p.id,url=url,position=i,is_cover=i==0))
    for name in set(data.amenities):
        a=db.query(Amenity).filter_by(name=name).first()
        if not a: a=Amenity(name=name); db.add(a); db.flush()
        db.add(PropertyAmenity(property_id=p.id,amenity_id=a.id))
    p.status="pending"; db.commit(); return property_out(get_property(db,p.id))

@router.delete("/properties/{pid}")
def delete_property(pid:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    p=get_property(db,pid)
    if p.owner_id!=user.id and "admin" not in {r.role for r in user.roles}: raise HTTPException(403,"You cannot delete this listing")
    p.status="deleted"; db.commit(); return {"ok":True}

@router.get("/me")
def me(user:User=Depends(current_user),db:Session=Depends(get_db)):
    profile=db.query(UserProfile).filter_by(user_id=user.id).first()
    return {"id":user.id,"email":user.email,"phone":user.phone,"contact_phone":profile.contact_phone if profile else None,"avatar_url":user.avatar_url,"full_name":user.full_name,"roles":[r.role for r in user.roles]}

@router.get("/me/properties")
def my_properties(user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Property).options(joinedload(Property.images),joinedload(Property.amenities).joinedload(PropertyAmenity.amenity)).filter(Property.owner_id==user.id,Property.status!="deleted").order_by(desc(Property.created_at)).all()
    return [property_out(p) for p in rows]

@router.post("/properties/{pid}/favourite")
def add_favourite(pid:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    p=get_property(db,pid)
    exists=db.query(Favourite).filter_by(user_id=user.id,property_id=p.id).first()
    if not exists: db.add(Favourite(user_id=user.id,property_id=p.id)); db.commit()
    return {"saved":True}

@router.delete("/properties/{pid}/favourite")
def remove_favourite(pid:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    p=get_property(db,pid); db.query(Favourite).filter_by(user_id=user.id,property_id=p.id).delete(); db.commit(); return {"saved":False}

@router.get("/me/favourites")
def favourites(user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Property).join(Favourite,Favourite.property_id==Property.id).options(joinedload(Property.images),joinedload(Property.amenities).joinedload(PropertyAmenity.amenity)).filter(Favourite.user_id==user.id).all()
    return [property_out(p) for p in rows]

@router.post("/properties/{pid}/inquiries")
def create_inquiry(pid:str,data:InquiryCreate,user:User|None=Depends(optional_user),db:Session=Depends(get_db)):
    p=get_property(db,pid)
    if p.status!="published": raise HTTPException(404,"Property not found")
    if not data.consent: raise HTTPException(422,"Consent is required to submit this enquiry")
    inquiry=Inquiry(property_id=p.id,sender_id=user.id if user else None,recipient_id=p.owner_id,name=data.name,email=str(data.email),phone=data.phone,message=data.message,consent_at=datetime.now(timezone.utc).replace(tzinfo=None))
    db.add(inquiry); notify(db,p.owner_id,"New property enquiry",f"{data.name} enquired about {p.title}"); db.commit(); db.refresh(inquiry)
    owner=db.query(User).filter_by(id=p.owner_id).first() if p.owner_id else None
    if owner and owner.email: send_email(owner.email,"New Aashiyana property enquiry",f"{data.name} ({data.phone}) enquired about {p.title}. Reply to the interested person using your Aashiyana dashboard.")
    return {"id":inquiry.id,"status":inquiry.status,"message":"Your enquiry has been received"}

@router.post("/properties/{pid}/visits")
def create_visit(pid:str,data:VisitCreate,user:User|None=Depends(optional_user),db:Session=Depends(get_db)):
    p=get_property(db,pid)
    if not data.consent: raise HTTPException(422,"Consent is required to request a visit")
    if data.scheduled_at.replace(tzinfo=None)<datetime.now(timezone.utc).replace(tzinfo=None): raise HTTPException(422,"Visit must be in the future")
    visit=PropertyVisit(property_id=p.id,user_id=user.id if user else None,name=data.name,phone=data.phone,scheduled_at=data.scheduled_at.replace(tzinfo=None),consent_at=datetime.now(timezone.utc).replace(tzinfo=None)); db.add(visit); notify(db,p.owner_id,"Property visit requested",f"Visit requested for {p.title}"); db.commit(); db.refresh(visit)
    owner=db.query(User).filter_by(id=p.owner_id).first() if p.owner_id else None
    if owner and owner.email: send_email(owner.email,"Aashiyana property visit request",f"{data.name} requested a visit for {p.title} at {data.scheduled_at.isoformat()}.")
    return {"id":visit.id,"status":visit.status}

@router.get("/me/inquiries")
def my_inquiries(user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Inquiry).filter(or_(Inquiry.sender_id==user.id,Inquiry.recipient_id==user.id)).order_by(desc(Inquiry.created_at)).all()
    return [{"id":x.id,"property_id":x.property_id,"property_title":db.query(Property.title).filter(Property.id==x.property_id).scalar(),"name":x.name,"email":x.email,"phone":x.phone,"message":x.message,"status":x.status,"created_at":x.created_at,"is_received":x.recipient_id==user.id} for x in rows]

@router.patch("/inquiries/{iid}")
def update_inquiry(iid:str,data:StatusUpdate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    x=db.query(Inquiry).filter_by(id=iid).first()
    if not x: raise HTTPException(404,"Inquiry not found")
    if x.recipient_id!=user.id and "admin" not in {r.role for r in user.roles}: raise HTTPException(403,"Not allowed")
    if data.status not in ["new","contacted","follow_up","visit_scheduled","converted","closed"]: raise HTTPException(422,"Invalid inquiry status")
    x.status=data.status; db.commit(); return {"id":x.id,"status":x.status}

@router.get("/me/visits")
def my_visits(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":v.id,"property_id":v.property_id,"property_title":db.query(Property.title).filter(Property.id==v.property_id).scalar(),"name":v.name,"phone":v.phone,"scheduled_at":v.scheduled_at,"status":v.status,"is_received":db.query(Property.owner_id).filter(Property.id==v.property_id).scalar()==user.id} for v in db.query(PropertyVisit).join(Property,Property.id==PropertyVisit.property_id).filter(or_(PropertyVisit.user_id==user.id,Property.owner_id==user.id)).all()]

@router.post("/me/saved-searches")
def save_search(data:SavedSearchCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    s=SavedSearch(user_id=user.id,name=data.name,filters=data.filters); db.add(s); db.commit(); db.refresh(s); return {"id":s.id,"name":s.name,"filters":s.filters}

@router.get("/me/saved-searches")
def list_searches(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":s.id,"name":s.name,"filters":s.filters} for s in db.query(SavedSearch).filter_by(user_id=user.id).all()]

@router.get("/me/notifications")
def notifications(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":n.id,"title":n.title,"body":n.body,"read":n.read_at is not None,"created_at":n.created_at} for n in db.query(Notification).filter_by(user_id=user.id).order_by(desc(Notification.created_at)).limit(100)]

@router.post("/properties/{pid}/reports")
def report_property(pid:str,data:ReportCreate,user:User|None=Depends(optional_user),db:Session=Depends(get_db)):
    p=get_property(db,pid); r=Report(property_id=p.id,reporter_id=user.id if user else None,reason=data.reason,details=data.details); db.add(r); db.commit(); return {"id":r.id,"status":"open"}

@router.post("/uploads")
def upload_image(file:UploadFile=File(...),user:User=Depends(current_user)):
    allowed={"image/jpeg","image/png","image/webp"}
    if file.content_type not in allowed: raise HTTPException(415,"Only JPG, PNG and WebP images are accepted")
    content=file.file.read(settings.max_upload_mb*1024*1024+1)
    if len(content)>settings.max_upload_mb*1024*1024: raise HTTPException(413,"Image exceeds upload size limit")
    valid_signature=(file.content_type=="image/jpeg" and content.startswith(b"\xff\xd8\xff")) or (file.content_type=="image/png" and content.startswith(b"\x89PNG\r\n\x1a\n")) or (file.content_type=="image/webp" and content.startswith(b"RIFF") and content[8:12]==b"WEBP")
    if not valid_signature: raise HTTPException(415,"Image content does not match its declared file type")
    if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key or not settings.cloudinary_api_secret: raise HTTPException(503,"Image storage is not configured. Configure Cloudinary credentials.")
    import cloudinary, cloudinary.uploader
    cloudinary.config(cloud_name=settings.cloudinary_cloud_name,api_key=settings.cloudinary_api_key,api_secret=settings.cloudinary_api_secret,secure=True)
    result=cloudinary.uploader.upload(content,folder="aashiyana/properties",resource_type="image")
    return {"url":result["secure_url"],"public_id":result["public_id"]}

@router.get("/admin/overview")
def admin_overview(user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    return {"users":db.query(User).count(),"listings":db.query(Property).filter(Property.status!="deleted").count(),"pending":db.query(Property).filter_by(status="pending").count(),"published":db.query(Property).filter_by(status="published").count(),"reports":db.query(Report).filter_by(status="open").count(),"inquiries":db.query(Inquiry).count()}

@router.get("/admin/properties")
def admin_properties(status:str|None=None,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    q=db.query(Property).options(joinedload(Property.images),joinedload(Property.amenities).joinedload(PropertyAmenity.amenity))
    if status: q=q.filter(Property.status==status)
    return [property_out(p) for p in q.order_by(desc(Property.created_at)).limit(300)]

@router.post("/admin/properties/{pid}/moderate")
def moderate(pid:str,data:ModerationDecision,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    p=get_property(db,pid)
    if data.decision not in ["approve","reject"]: raise HTTPException(422,"Decision must be approve or reject")
    p.status="published" if data.decision=="approve" else "rejected"; p.moderation_note=data.reason
    db.add(ListingApproval(property_id=p.id,admin_id=user.id,decision=data.decision,reason=data.reason)); db.add(AuditLog(actor_id=user.id,action="listing."+data.decision,entity_type="property",entity_id=p.id,metadata_json={"reason":data.reason})); notify(db,p.owner_id,"Listing reviewed",f"Your listing {p.title} was {p.status}"); db.commit(); return {"id":p.id,"status":p.status}

@router.patch("/admin/users/{uid}/roles")
def set_roles(uid:str,roles:list[str],user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    allowed={"buyer","tenant","seller","owner","agent","builder","admin"}
    if not roles or not set(roles)<=allowed: raise HTTPException(422,"Invalid roles")
    target=db.query(User).filter_by(id=uid).first()
    if not target: raise HTTPException(404,"User not found")
    target.roles.clear(); db.flush()
    for role in set(roles): db.add(UserRole(user_id=uid,role=role))
    db.add(AuditLog(actor_id=user.id,action="user.roles.updated",entity_type="user",entity_id=uid,metadata_json={"roles":roles})); db.commit(); return {"user_id":uid,"roles":roles}

@router.get("/admin/reports")
def admin_reports(user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    return [{"id":r.id,"property_id":r.property_id,"reason":r.reason,"details":r.details,"status":r.status,"created_at":r.created_at} for r in db.query(Report).order_by(desc(Report.created_at)).limit(300)]

@router.get("/locations")
def locations(q:str|None=None,db:Session=Depends(get_db)):
    query=db.query(Location)
    if q: query=query.filter(or_(Location.city.ilike(f"%{q}%"),Location.locality.ilike(f"%{q}%"),Location.pincode.ilike(f"%{q}%")))
    return [{"city":x.city,"state":x.state,"locality":x.locality,"pincode":x.pincode} for x in query.limit(30)]

@router.get("/projects")
def projects(city:str|None=None,db:Session=Depends(get_db)):
    q=db.query(Project)
    if city: q=q.filter(Project.city.ilike(city))
    return [{"id":p.id,"name":p.name,"slug":p.slug,"city":p.city,"locality":p.locality,"price_min":float(p.price_min) if p.price_min else None,"price_max":float(p.price_max) if p.price_max else None,"status":p.status,"possession_date":p.possession_date,"rera_number":p.rera_number,"rera_verified":p.rera_verified} for p in q.all()]

@router.get("/agents")
def agents(db:Session=Depends(get_db)):
    return [{"id":a.id,"name":a.user.full_name if a.user else "Demo property professional","company":a.company,"experience_years":a.experience_years,"locations_served":a.locations_served,"bio":a.bio,"verified":a.verified} for a in db.query(Agent).all()]

@router.get("/developers")
def developers(db:Session=Depends(get_db)):
    return [{"id":d.id,"name":d.name,"description":d.description,"website":d.website,"verified":d.verified} for d in db.query(Developer).all()]

@router.patch("/me")
def update_profile(data:ProfileUpdate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    user.full_name=data.full_name
    if data.avatar_url is not None: user.avatar_url=data.avatar_url
    profile=db.query(UserProfile).filter_by(user_id=user.id).first()
    if not profile: profile=UserProfile(user_id=user.id); db.add(profile)
    profile.bio=data.bio or ""; profile.company=data.company; profile.contact_phone=data.contact_phone; profile.experience_years=data.experience_years; profile.address=data.address
    db.commit(); return {"id":user.id,"full_name":user.full_name,"email":user.email,"phone":user.phone,"contact_phone":profile.contact_phone,"avatar_url":user.avatar_url,"bio":profile.bio,"company":profile.company,"experience_years":profile.experience_years,"address":profile.address}

@router.get("/blog")
def public_blog(db:Session=Depends(get_db)):
    return [{"id":p.id,"title":p.title,"slug":p.slug,"excerpt":p.excerpt,"content":p.content,"created_at":p.created_at} for p in db.query(BlogPost).filter_by(published=True).order_by(desc(BlogPost.created_at)).all()]

@router.get("/admin/users")
def admin_users(user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    return [{"id":u.id,"email":u.email,"phone":u.phone,"full_name":u.full_name,"is_active":u.is_active,"created_at":u.created_at,"roles":[r.role for r in u.roles]} for u in db.query(User).order_by(desc(User.created_at)).limit(500)]

@router.patch("/admin/reports/{rid}")
def update_report(rid:str,data:StatusUpdate,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    report=db.query(Report).filter_by(id=rid).first()
    if not report: raise HTTPException(404,"Report not found")
    if data.status not in ["open","reviewing","resolved","dismissed"]: raise HTTPException(422,"Invalid report status")
    report.status=data.status; db.add(AuditLog(actor_id=user.id,action="report.status.updated",entity_type="report",entity_id=rid,metadata_json={"status":data.status})); db.commit(); return {"id":rid,"status":report.status}

@router.patch("/me/notifications/{nid}")
def mark_notification_read(nid:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    n=db.query(Notification).filter_by(id=nid,user_id=user.id).first()
    if not n: raise HTTPException(404,"Notification not found")
    n.read_at=datetime.now(timezone.utc).replace(tzinfo=None); db.commit(); return {"id":nid,"read":True}

@router.get("/admin/projects")
def admin_projects(user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    return projects(db=db)

@router.delete("/admin/properties/{pid}")
def admin_delete_property(pid:str,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    p=get_property(db,pid); p.status="deleted"; db.add(AuditLog(actor_id=user.id,action="listing.deleted",entity_type="property",entity_id=p.id)); db.commit(); return {"ok":True}

@router.post("/admin/projects")
def create_project(data:ProjectCreate,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    if db.query(Project).filter_by(slug=data.slug).first(): raise HTTPException(409,"Project slug already exists")
    p=Project(**data.model_dump()); db.add(p); db.flush(); db.add(AuditLog(actor_id=user.id,action="project.created",entity_type="project",entity_id=p.id)); db.commit(); return {"id":p.id,"slug":p.slug}

@router.post("/admin/developers")
def create_developer(data:DeveloperCreate,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    d=Developer(**data.model_dump()); db.add(d); db.flush(); db.add(AuditLog(actor_id=user.id,action="developer.created",entity_type="developer",entity_id=d.id)); db.commit(); return {"id":d.id,"name":d.name}

@router.post("/admin/blog")
def create_blog_post(data:BlogPostCreate,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    if db.query(BlogPost).filter_by(slug=data.slug).first(): raise HTTPException(409,"Blog slug already exists")
    p=BlogPost(**data.model_dump()); db.add(p); db.flush(); db.add(AuditLog(actor_id=user.id,action="blog.created",entity_type="blog_post",entity_id=p.id)); db.commit(); return {"id":p.id,"slug":p.slug}

@router.get("/admin/audit-logs")
def audit_logs(user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    return [{"id":x.id,"actor_id":x.actor_id,"action":x.action,"entity_type":x.entity_type,"entity_id":x.entity_id,"metadata":x.metadata_json,"created_at":x.created_at} for x in db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(500)]

@router.post("/newsletter")
def subscribe_newsletter(data:NewsletterCreate,db:Session=Depends(get_db)):
    if not data.consent: raise HTTPException(422,"Consent is required to subscribe")
    email=str(data.email).lower()
    sub=db.query(NewsletterSubscription).filter_by(email=email).first()
    if sub: sub.is_active=True
    else: db.add(NewsletterSubscription(email=email))
    db.commit(); return {"subscribed":True,"message":"Your subscription preference has been saved."}

@router.post("/properties/drafts")
def save_property_draft(data:PropertyDraftCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    values=data.model_dump(); amenities=values.pop("amenities",[]); slug=slugify((values.get("title") or "draft")+"-"+uuid.uuid4().hex[:8])
    p=Property(**values,owner_id=user.id,slug=slug,property_id="DRAFT-"+uuid.uuid4().hex[:8].upper(),status="draft")
    db.add(p);db.flush()
    for name in set(amenities):
        a=db.query(Amenity).filter_by(name=name).first()
        if not a: a=Amenity(name=name);db.add(a);db.flush()
        db.add(PropertyAmenity(property_id=p.id,amenity_id=a.id))
    db.commit();db.refresh(p);return {"id":p.id,"property_id":p.property_id,"slug":p.slug,"status":p.status}

@router.get("/admin/settings")
def admin_settings(user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    return [{"key":s.key,"value":s.value,"updated_at":s.updated_at} for s in db.query(PlatformSetting).all()]

@router.put("/admin/settings/{key}")
def update_setting(key:str,data:SettingUpdate,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    if not re.fullmatch(r"[a-z0-9_.-]{2,100}",key): raise HTTPException(422,"Invalid setting key")
    setting=db.query(PlatformSetting).filter_by(key=key).first()
    if not setting: setting=PlatformSetting(key=key,value=data.value);db.add(setting)
    else: setting.value=data.value
    db.add(AuditLog(actor_id=user.id,action="platform_setting.updated",entity_type="setting",entity_id=key,metadata_json={"keys":list(data.value.keys())}));db.commit();return {"key":key,"value":setting.value}

@router.get("/categories")
def categories(db:Session=Depends(get_db)):
    return [{"id":c.id,"name":c.name,"slug":c.slug} for c in db.query(PropertyCategory).filter_by(is_active=True).order_by(PropertyCategory.name).all()]

@router.post("/admin/categories")
def create_category(data:CategoryCreate,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    slug=slugify(data.name)
    if db.query(PropertyCategory).filter(or_(PropertyCategory.name==data.name,PropertyCategory.slug==slug)).first(): raise HTTPException(409,"Category already exists")
    c=PropertyCategory(name=data.name,slug=slug,is_active=data.is_active);db.add(c);db.flush();db.add(AuditLog(actor_id=user.id,action="category.created",entity_type="property_category",entity_id=str(c.id)));db.commit();return {"id":c.id,"name":c.name,"slug":c.slug}

@router.patch("/admin/properties/{pid}/feature")
def feature_property(pid:str,data:FeatureUpdate,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    p=get_property(db,pid);p.featured=data.featured;db.add(AuditLog(actor_id=user.id,action="listing.feature.updated",entity_type="property",entity_id=p.id,metadata_json={"featured":data.featured}));db.commit();return {"id":p.id,"featured":p.featured}

@router.post("/admin/locations")
def create_location(data:LocationCreate,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    location=Location(**data.model_dump());db.add(location);db.flush();db.add(AuditLog(actor_id=user.id,action="location.created",entity_type="location",entity_id=str(location.id)));db.commit();return {"id":location.id,"city":location.city,"locality":location.locality}

@router.post("/admin/agents")
def create_agent(data:AgentCreate,user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    if data.user_id and not db.query(User).filter_by(id=data.user_id).first(): raise HTTPException(404,"Agent user not found")
    agent=Agent(**data.model_dump());db.add(agent);db.flush();db.add(AuditLog(actor_id=user.id,action="agent.created",entity_type="agent",entity_id=agent.id));db.commit();return {"id":agent.id}

@router.post("/contact-messages")
def create_contact_message(data:ContactMessageCreate,db:Session=Depends(get_db)):
    if not data.consent: raise HTTPException(422,"Consent is required to send this message")
    msg=ContactMessage(name=data.name,email=str(data.email),topic=data.topic,message=data.message);db.add(msg);db.commit();db.refresh(msg)
    if settings.contact_email: send_email(settings.contact_email,f"Aashiyana contact: {data.topic}",f"From: {data.name} <{data.email}>\n\n{data.message}")
    return {"id":msg.id,"status":msg.status,"message":"Your message has been received."}

@router.get("/admin/contact-messages")
def admin_contact_messages(user:User=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    return [{"id":m.id,"name":m.name,"email":m.email,"topic":m.topic,"message":m.message,"status":m.status,"created_at":m.created_at} for m in db.query(ContactMessage).order_by(desc(ContactMessage.created_at)).limit(500)]

@router.patch("/visits/{vid}")
def update_visit(vid:str,data:StatusUpdate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    visit=db.query(PropertyVisit).filter_by(id=vid).first()
    if not visit: raise HTTPException(404,"Visit request not found")
    prop=db.query(Property).filter_by(id=visit.property_id).first()
    if prop.owner_id!=user.id and visit.user_id!=user.id and "admin" not in {r.role for r in user.roles}: raise HTTPException(403,"Not allowed")
    if data.status not in ["requested","confirmed","rescheduled","completed","cancelled"]: raise HTTPException(422,"Invalid visit status")
    visit.status=data.status;db.commit();return {"id":vid,"status":visit.status}
