from app.db.session import SessionLocal, Base, engine
from app.models import Property, PropertyImage, Amenity, PropertyAmenity, Location, Developer, Project, Agent, BlogPost, State, City, PropertyCategory
from datetime import date
from uuid import uuid4

CITIES=[("Pune","Maharashtra",["Hinjewadi","Kharadi","Baner","Wagholi","Wakad"]),("Mumbai","Maharashtra",["Andheri East","Powai","Thane","Chembur"]),("Bengaluru","Karnataka",["Whitefield","Indiranagar","Sarjapur Road"]),("Hyderabad","Telangana",["Gachibowli","Kondapur"]),("Delhi NCR","Delhi",["Dwarka","Noida Sector 150"]),("Chennai","Tamil Nadu",["OMR","Velachery"]),("Kolkata","West Bengal",["New Town"]),("Ahmedabad","Gujarat",["Prahlad Nagar"]),("Jaipur","Rajasthan",["Vaishali Nagar"]),("Lucknow","Uttar Pradesh",["Gomti Nagar"]) ]
PHOTOS=["https://images.unsplash.com/photo-1600607687939-ce8a6c25118c","https://images.unsplash.com/photo-1600607687920-4e2a09cf159d","https://images.unsplash.com/photo-1600585154340-be6161a56a0c","https://images.unsplash.com/photo-1600210492486-724fe5c67fb0","https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea"]
AMENITIES=["Clubhouse","Swimming pool","Gymnasium","24×7 security","Power backup","Parking","Lift","Children’s play area"]
def main():
    Base.metadata.create_all(engine); db=SessionLocal()
    try:
        if db.query(Property).count(): print("Seed skipped: properties already exist"); return
        amap={a.name:a for a in db.query(Amenity).all()}
        for name in AMENITIES:
            if name not in amap: a=Amenity(name=name); db.add(a); db.flush(); amap[name]=a
        states={}
        for city,state,localities in CITIES:
            if state not in states:
                state_row=State(name=state);db.add(state_row);db.flush();states[state]=state_row
            city_row=City(state_id=states[state].id,name=city);db.add(city_row)
            for i,locality in enumerate(localities): db.add(Location(city=city,state=state,locality=locality,pincode=f"{411001+i:06d}" if city=="Pune" else None))
        for name in ["Apartment","Independent house","Villa","Plot","Penthouse","Studio apartment","Builder floor","Commercial"]:
            db.add(PropertyCategory(name=name,slug=slugify(name)))
        developers=[]
        for name in ["Demo VTP Realty","Demo Prestige Group","Demo Lodha Developers","Demo Godrej Properties"]:
            d=Developer(name=name,description="Seeded demo developer profile. Verification has not been performed.",verified=False); db.add(d); developers.append(d)
        db.flush()
        for i in range(36):
            city,state,locs=CITIES[i%len(CITIES)]; locality=locs[i%len(locs)]; rent=i%3==0; typ=["Apartment","Villa","Independent house","Plot","Builder floor"][i%5]
            price=(18000+(i*2300) if rent else 4200000+(i*1250000))
            title=f"Demo {['Olive','Serene','Lakeview','Palm','Garden','Urban'][i%6]} {typ} in {locality}"
            slug=f"demo-{slugify(title)}-{i+1}"
            p=Property(property_id=f"DEMO-{i+1:04d}",slug=slug,title=title,description="DEMO LISTING — Sample development data for testing marketplace discovery. Confirm all property details, ownership, title and statutory approvals independently before any transaction.",transaction_type="rent" if rent else "buy",property_type=typ,status="published",city=city,state=state,locality=locality,price=price,bedrooms=0 if typ=="Plot" else 1+i%4,bathrooms=0 if typ=="Plot" else 1+i%3,balconies=i%3,carpet_area=550+(i*75),builtup_area=650+(i*90),furnishing=["Unfurnished","Semi-furnished","Fully furnished"][i%3],parking=i%3,possession_status="Under construction" if i%4==0 else "Ready to move",deposit=price*2 if rent else None,rera_number=None,rera_verified=False,featured=i%7==0,demo=True)
            db.add(p); db.flush(); db.add(PropertyImage(property_id=p.id,url=PHOTOS[i%len(PHOTOS)],position=0,is_cover=True))
            for a in AMENITIES[:3+i%4]: db.add(PropertyAmenity(property_id=p.id,amenity_id=amap[a].id))
        for i,d in enumerate(developers):
            db.add(Project(developer_id=d.id,name=f"Demo {d.name.replace('Demo ','')} Residences",slug=f"demo-project-{i+1}",city=CITIES[i][0],locality=CITIES[i][2][0],price_min=7500000+i*1500000,price_max=15000000+i*2500000,status="Under construction",possession_date=date(2028,6,30),rera_number=None,rera_verified=False))
        db.add(Agent(company="Demo Aarav Realty",experience_years=6,locations_served=["Pune","Mumbai"],bio="Seeded demo agent profile; not a verified professional."))
        db.add(BlogPost(title="A first-time buyer’s checklist",slug="first-time-buyer-checklist",excerpt="A practical checklist for researching a home purchase.",content="DEMO EDITORIAL CONTENT. Seek independent legal and financial advice.",published=True))
        db.commit(); print("Seeded 36 demo properties, locations, amenities, projects, agents and editorial content.")
    finally: db.close()
def slugify(s):
    import re
    return re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",s.lower())).strip("-")
if __name__=="__main__": main()
