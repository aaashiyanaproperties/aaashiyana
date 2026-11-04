import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Text, Boolean, DateTime, Date, Integer, Float, ForeignKey, Numeric, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

def uid(): return str(uuid.uuid4())
def utcnow(): return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__="users"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False), primary_key=True, default=uid)
    firebase_uid: Mapped[str|None]=mapped_column(String(128), unique=True, index=True)
    email: Mapped[str|None]=mapped_column(String(320), unique=True, index=True)
    phone: Mapped[str|None]=mapped_column(String(20), index=True)
    full_name: Mapped[str]=mapped_column(String(160), default="Aashiyana user")
    avatar_url: Mapped[str|None]=mapped_column(String(1000))
    is_active: Mapped[bool]=mapped_column(Boolean, default=True)
    is_verified: Mapped[bool]=mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=utcnow)
    roles: Mapped[list["UserRole"]]=relationship(back_populates="user", cascade="all, delete-orphan")

class UserRole(Base):
    __tablename__="user_roles"
    __table_args__=(UniqueConstraint("user_id","role"),)
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str]=mapped_column(String(24), index=True)
    user: Mapped[User]=relationship(back_populates="roles")

class Location(Base):
    __tablename__="locations"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    state: Mapped[str]=mapped_column(String(80), index=True)
    city: Mapped[str]=mapped_column(String(80), index=True)
    locality: Mapped[str]=mapped_column(String(120), index=True)
    pincode: Mapped[str|None]=mapped_column(String(6), index=True)

class Property(Base):
    __tablename__="properties"
    __table_args__=(Index("ix_property_search","city","transaction_type","status"), Index("ix_property_price","price"))
    id: Mapped[str]=mapped_column(UUID(as_uuid=False), primary_key=True, default=uid)
    owner_id: Mapped[str|None]=mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    property_id: Mapped[str]=mapped_column(String(24), unique=True, index=True)
    slug: Mapped[str]=mapped_column(String(220), unique=True, index=True)
    title: Mapped[str]=mapped_column(String(220), index=True)
    description: Mapped[str]=mapped_column(Text, default="")
    transaction_type: Mapped[str]=mapped_column(String(16), index=True)
    property_type: Mapped[str]=mapped_column(String(40), index=True)
    status: Mapped[str]=mapped_column(String(24), default="pending", index=True)
    moderation_note: Mapped[str|None]=mapped_column(Text)
    city: Mapped[str]=mapped_column(String(80), index=True)
    state: Mapped[str]=mapped_column(String(80), default="Maharashtra")
    locality: Mapped[str]=mapped_column(String(120), index=True)
    address: Mapped[str|None]=mapped_column(String(300))
    pincode: Mapped[str|None]=mapped_column(String(6), index=True)
    latitude: Mapped[float|None]=mapped_column(Float)
    longitude: Mapped[float|None]=mapped_column(Float)
    price: Mapped[float]=mapped_column(Numeric(14,2), index=True)
    maintenance: Mapped[float|None]=mapped_column(Numeric(12,2))
    deposit: Mapped[float|None]=mapped_column(Numeric(12,2))
    negotiable: Mapped[bool]=mapped_column(Boolean, default=False)
    bedrooms: Mapped[int]=mapped_column(Integer, default=0)
    bathrooms: Mapped[int]=mapped_column(Integer, default=0)
    balconies: Mapped[int]=mapped_column(Integer, default=0)
    carpet_area: Mapped[float|None]=mapped_column(Float)
    builtup_area: Mapped[float|None]=mapped_column(Float)
    super_builtup_area: Mapped[float|None]=mapped_column(Float)
    furnishing: Mapped[str]=mapped_column(String(32), default="Unfurnished")
    floor_number: Mapped[int|None]=mapped_column(Integer)
    total_floors: Mapped[int|None]=mapped_column(Integer)
    facing: Mapped[str|None]=mapped_column(String(24))
    parking: Mapped[int]=mapped_column(Integer, default=0)
    age_years: Mapped[int|None]=mapped_column(Integer)
    possession_status: Mapped[str]=mapped_column(String(40), default="Ready to move")
    available_from: Mapped[date|None]=mapped_column(Date)
    lease_months: Mapped[int|None]=mapped_column(Integer)
    rera_number: Mapped[str|None]=mapped_column(String(80))
    rera_verified: Mapped[bool]=mapped_column(Boolean, default=False)
    featured: Mapped[bool]=mapped_column(Boolean, default=False)
    demo: Mapped[bool]=mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    images: Mapped[list["PropertyImage"]]=relationship(back_populates="property", cascade="all, delete-orphan", order_by="PropertyImage.position")
    amenities: Mapped[list["PropertyAmenity"]]=relationship(back_populates="property", cascade="all, delete-orphan")

class PropertyImage(Base):
    __tablename__="property_images"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False), primary_key=True, default=uid)
    property_id: Mapped[str]=mapped_column(ForeignKey("properties.id",ondelete="CASCADE"), index=True)
    url: Mapped[str]=mapped_column(String(1200))
    alt_text: Mapped[str]=mapped_column(String(240), default="Property image")
    position: Mapped[int]=mapped_column(Integer, default=0)
    is_cover: Mapped[bool]=mapped_column(Boolean, default=False)
    property: Mapped[Property]=relationship(back_populates="images")

class Amenity(Base):
    __tablename__="amenities"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    name: Mapped[str]=mapped_column(String(80),unique=True)

class PropertyAmenity(Base):
    __tablename__="property_amenities"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    property_id: Mapped[str]=mapped_column(ForeignKey("properties.id",ondelete="CASCADE"),index=True)
    amenity_id: Mapped[int]=mapped_column(ForeignKey("amenities.id",ondelete="CASCADE"))
    property: Mapped[Property]=relationship(back_populates="amenities")
    amenity: Mapped[Amenity]=relationship()

class Favourite(Base):
    __tablename__="favourites"
    __table_args__=(UniqueConstraint("user_id","property_id"),)
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    property_id: Mapped[str]=mapped_column(ForeignKey("properties.id",ondelete="CASCADE"),index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class SavedSearch(Base):
    __tablename__="saved_searches"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    name: Mapped[str]=mapped_column(String(120))
    filters: Mapped[dict]=mapped_column(JSON,default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class Inquiry(Base):
    __tablename__="inquiries"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    property_id: Mapped[str]=mapped_column(ForeignKey("properties.id",ondelete="CASCADE"),index=True)
    sender_id: Mapped[str|None]=mapped_column(ForeignKey("users.id",ondelete="SET NULL"),index=True)
    recipient_id: Mapped[str|None]=mapped_column(ForeignKey("users.id",ondelete="SET NULL"),index=True)
    name: Mapped[str]=mapped_column(String(160))
    email: Mapped[str]=mapped_column(String(320))
    phone: Mapped[str]=mapped_column(String(20))
    message: Mapped[str]=mapped_column(Text)
    consent_at: Mapped[datetime|None]=mapped_column(DateTime)
    status: Mapped[str]=mapped_column(String(24),default="new",index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class PropertyVisit(Base):
    __tablename__="property_visits"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    property_id: Mapped[str]=mapped_column(ForeignKey("properties.id",ondelete="CASCADE"),index=True)
    user_id: Mapped[str|None]=mapped_column(ForeignKey("users.id",ondelete="SET NULL"))
    name: Mapped[str]=mapped_column(String(160))
    phone: Mapped[str]=mapped_column(String(20))
    scheduled_at: Mapped[datetime]=mapped_column(DateTime,index=True)
    consent_at: Mapped[datetime|None]=mapped_column(DateTime)
    status: Mapped[str]=mapped_column(String(24),default="requested")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class Notification(Base):
    __tablename__="notifications"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    title: Mapped[str]=mapped_column(String(180))
    body: Mapped[str]=mapped_column(Text)
    read_at: Mapped[datetime|None]=mapped_column(DateTime)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class Report(Base):
    __tablename__="reports"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    property_id: Mapped[str]=mapped_column(ForeignKey("properties.id",ondelete="CASCADE"),index=True)
    reporter_id: Mapped[str|None]=mapped_column(ForeignKey("users.id",ondelete="SET NULL"))
    reason: Mapped[str]=mapped_column(String(80))
    details: Mapped[str|None]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(24),default="open")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class ListingApproval(Base):
    __tablename__="listing_approvals"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    property_id: Mapped[str]=mapped_column(ForeignKey("properties.id",ondelete="CASCADE"),index=True)
    admin_id: Mapped[str]=mapped_column(ForeignKey("users.id"))
    decision: Mapped[str]=mapped_column(String(24))
    reason: Mapped[str|None]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class Developer(Base):
    __tablename__="developers"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    name: Mapped[str]=mapped_column(String(180),index=True)
    description: Mapped[str]=mapped_column(Text,default="")
    website: Mapped[str|None]=mapped_column(String(300))
    verified: Mapped[bool]=mapped_column(Boolean,default=False)

class Project(Base):
    __tablename__="projects"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    developer_id: Mapped[str|None]=mapped_column(ForeignKey("developers.id"))
    name: Mapped[str]=mapped_column(String(180),index=True)
    slug: Mapped[str]=mapped_column(String(200),unique=True)
    city: Mapped[str]=mapped_column(String(80),index=True)
    locality: Mapped[str]=mapped_column(String(120))
    price_min: Mapped[float|None]=mapped_column(Numeric(14,2))
    price_max: Mapped[float|None]=mapped_column(Numeric(14,2))
    status: Mapped[str]=mapped_column(String(40))
    possession_date: Mapped[date|None]=mapped_column(Date)
    rera_number: Mapped[str|None]=mapped_column(String(80))
    rera_verified: Mapped[bool]=mapped_column(Boolean,default=False)

class Agent(Base):
    __tablename__="agents"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    user_id: Mapped[str|None]=mapped_column(ForeignKey("users.id",ondelete="SET NULL"))
    company: Mapped[str|None]=mapped_column(String(180))
    experience_years: Mapped[int]=mapped_column(Integer,default=0)
    locations_served: Mapped[list]=mapped_column(JSON,default=list)
    bio: Mapped[str]=mapped_column(Text,default="")
    verified: Mapped[bool]=mapped_column(Boolean,default=False)
    user: Mapped[User|None]=relationship()

class BlogPost(Base):
    __tablename__="blog_posts"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    title: Mapped[str]=mapped_column(String(220))
    slug: Mapped[str]=mapped_column(String(220),unique=True)
    excerpt: Mapped[str]=mapped_column(Text)
    content: Mapped[str]=mapped_column(Text)
    published: Mapped[bool]=mapped_column(Boolean,default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    actor_id: Mapped[str|None]=mapped_column(ForeignKey("users.id",ondelete="SET NULL"))
    action: Mapped[str]=mapped_column(String(100),index=True)
    entity_type: Mapped[str]=mapped_column(String(60))
    entity_id: Mapped[str]=mapped_column(String(80))
    metadata_json: Mapped[dict]=mapped_column(JSON,default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)

class UserProfile(Base):
    __tablename__="user_profiles"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),unique=True,index=True)
    bio: Mapped[str]=mapped_column(Text,default="")
    company: Mapped[str|None]=mapped_column(String(180))
    contact_phone: Mapped[str|None]=mapped_column(String(20))
    experience_years: Mapped[int|None]=mapped_column(Integer)
    address: Mapped[str|None]=mapped_column(String(300))
    preferences: Mapped[dict]=mapped_column(JSON,default=dict)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow,onupdate=utcnow)

class State(Base):
    __tablename__="states"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    name: Mapped[str]=mapped_column(String(80),unique=True,index=True)
    code: Mapped[str|None]=mapped_column(String(8),unique=True)

class City(Base):
    __tablename__="cities"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    state_id: Mapped[int]=mapped_column(ForeignKey("states.id",ondelete="CASCADE"),index=True)
    name: Mapped[str]=mapped_column(String(80),index=True)
    __table_args__=(UniqueConstraint("state_id","name"),)

class PlatformSetting(Base):
    __tablename__="platform_settings"
    key: Mapped[str]=mapped_column(String(100),primary_key=True)
    value: Mapped[dict]=mapped_column(JSON,default=dict)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow,onupdate=utcnow)

class ProjectImage(Base):
    __tablename__="project_images"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    project_id: Mapped[str]=mapped_column(ForeignKey("projects.id",ondelete="CASCADE"),index=True)
    url: Mapped[str]=mapped_column(String(1200))
    position: Mapped[int]=mapped_column(Integer,default=0)

class ProjectAmenity(Base):
    __tablename__="project_amenities"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    project_id: Mapped[str]=mapped_column(ForeignKey("projects.id",ondelete="CASCADE"),index=True)
    amenity_id: Mapped[int]=mapped_column(ForeignKey("amenities.id",ondelete="CASCADE"))

class NewsletterSubscription(Base):
    __tablename__="newsletter_subscriptions"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    email: Mapped[str]=mapped_column(String(320),unique=True,index=True)
    consent_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)

class PropertyCategory(Base):
    __tablename__="property_categories"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    name: Mapped[str]=mapped_column(String(80),unique=True)
    slug: Mapped[str]=mapped_column(String(100),unique=True)
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)

class ContactMessage(Base):
    __tablename__="contact_messages"
    id: Mapped[str]=mapped_column(UUID(as_uuid=False),primary_key=True,default=uid)
    name: Mapped[str]=mapped_column(String(160))
    email: Mapped[str]=mapped_column(String(320))
    topic: Mapped[str]=mapped_column(String(100))
    message: Mapped[str]=mapped_column(Text)
    consent_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
    status: Mapped[str]=mapped_column(String(24),default="new",index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=utcnow)
