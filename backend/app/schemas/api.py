from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from typing import Any

class PropertyCreate(BaseModel):
    title:str=Field(min_length=8,max_length=220); description:str=Field(min_length=30)
    transaction_type:str; property_type:str; city:str; state:str; locality:str
    address:str|None=None; pincode:str|None=Field(default=None,pattern=r"^\d{6}$")
    price:float=Field(gt=0); maintenance:float|None=Field(default=None,ge=0); deposit:float|None=Field(default=None,ge=0)
    negotiable:bool=False; bedrooms:int=Field(default=0,ge=0,le=20); bathrooms:int=Field(default=0,ge=0,le=20)
    balconies:int=Field(default=0,ge=0,le=20); carpet_area:float|None=Field(default=None,gt=0); builtup_area:float|None=Field(default=None,gt=0)
    furnishing:str="Unfurnished"; floor_number:int|None=None; total_floors:int|None=None; facing:str|None=None
    parking:int=Field(default=0,ge=0,le=20); age_years:int|None=None; possession_status:str="Ready to move"
    rera_number:str|None=None; latitude:float|None=None; longitude:float|None=None
    amenities:list[str]=[]; images:list[str]=[]; status:str="draft"
    @field_validator("images")
    @classmethod
    def secure_image_urls(cls, values):
        if len(values)>20: raise ValueError("Maximum 20 images per listing")
        if any(not value.startswith("https://") for value in values): raise ValueError("Property image URLs must use HTTPS")
        return values
    @field_validator("latitude")
    @classmethod
    def valid_latitude(cls, value):
        if value is not None and not -90<=value<=90: raise ValueError("Invalid latitude")
        return value
    @field_validator("longitude")
    @classmethod
    def valid_longitude(cls, value):
        if value is not None and not -180<=value<=180: raise ValueError("Invalid longitude")
        return value

class InquiryCreate(BaseModel):
    name:str=Field(min_length=2,max_length=160); email:EmailStr; phone:str=Field(min_length=8,max_length=20,pattern=r"^[0-9+() -]{8,20}$")
    message:str=Field(min_length=5,max_length=3000)
    consent:bool

class VisitCreate(BaseModel):
    name:str=Field(min_length=2,max_length=160); phone:str=Field(min_length=8,max_length=20,pattern=r"^[0-9+() -]{8,20}$"); scheduled_at:datetime; consent:bool

class StatusUpdate(BaseModel): status:str
class ModerationDecision(BaseModel): decision:str; reason:str|None=None
class SavedSearchCreate(BaseModel): name:str; filters:dict[str,Any]
class ReportCreate(BaseModel): reason:str; details:str|None=None

class UserOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:str; email:str|None; phone:str|None; full_name:str; roles:list[str]

class PropertyOut(BaseModel):
    id:str; property_id:str; slug:str; title:str; description:str; transaction_type:str; property_type:str
    status:str; city:str; state:str; locality:str; address:str|None; pincode:str|None; price:float
    maintenance:float|None; deposit:float|None; bedrooms:int; bathrooms:int; balconies:int; carpet_area:float|None
    builtup_area:float|None; furnishing:str; parking:int; possession_status:str; rera_number:str|None
    rera_verified:bool; featured:bool; demo:bool; latitude:float|None; longitude:float|None; images:list[str]; amenities:list[str]; created_at:datetime

class ProfileUpdate(BaseModel):
    full_name:str=Field(min_length=2,max_length=160)
    contact_phone:str|None=Field(default=None,max_length=20,pattern=r"^[0-9+() -]{8,20}$")
    avatar_url:str|None=Field(default=None,max_length=1000)
    bio:str|None=Field(default=None,max_length=3000)
    company:str|None=Field(default=None,max_length=180)
    experience_years:int|None=Field(default=None,ge=0,le=80)
    address:str|None=Field(default=None,max_length=300)

class ProjectCreate(BaseModel):
    name:str=Field(min_length=3,max_length=180); slug:str=Field(min_length=3,max_length=200)
    city:str; locality:str; price_min:float|None=None; price_max:float|None=None
    status:str; possession_date:date|None=None; rera_number:str|None=None; developer_id:str|None=None

class DeveloperCreate(BaseModel):
    name:str=Field(min_length=2,max_length=180); description:str=""; website:str|None=None

class BlogPostCreate(BaseModel):
    title:str=Field(min_length=5,max_length=220); slug:str=Field(min_length=3,max_length=220)
    excerpt:str; content:str; published:bool=False

class NewsletterCreate(BaseModel):
    email:EmailStr
    consent:bool

class PropertyDraftCreate(BaseModel):
    title:str="Untitled property draft"; description:str="Draft listing. Add a complete description before submitting."
    transaction_type:str="buy"; property_type:str="Apartment"; city:str="Pune"; state:str="Maharashtra"; locality:str="Not specified"
    address:str|None=None; pincode:str|None=None; price:float=1; maintenance:float|None=None; deposit:float|None=None
    negotiable:bool=False; bedrooms:int=0; bathrooms:int=0; balconies:int=0; carpet_area:float|None=None; builtup_area:float|None=None
    furnishing:str="Unfurnished"; floor_number:int|None=None; total_floors:int|None=None; facing:str|None=None; parking:int=0; age_years:int|None=None
    possession_status:str="Ready to move"; rera_number:str|None=None; latitude:float|None=None; longitude:float|None=None
    amenities:list[str]=[]

class SettingUpdate(BaseModel):
    value:dict[str,Any]

class CategoryCreate(BaseModel):
    name:str=Field(min_length=2,max_length=80)
    is_active:bool=True

class FeatureUpdate(BaseModel): featured:bool
class LocationCreate(BaseModel):
    state:str=Field(min_length=2,max_length=80); city:str=Field(min_length=2,max_length=80); locality:str=Field(min_length=2,max_length=120); pincode:str|None=Field(default=None,pattern=r"^\d{6}$")
class AgentCreate(BaseModel):
    user_id:str|None=None; company:str|None=None; experience_years:int=Field(default=0,ge=0,le=80); locations_served:list[str]=[]; bio:str=""

class ContactMessageCreate(BaseModel):
    name:str=Field(min_length=2,max_length=160); email:EmailStr; topic:str=Field(min_length=2,max_length=100); message:str=Field(min_length=5,max_length=5000); consent:bool
