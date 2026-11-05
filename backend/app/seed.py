import re
from datetime import date, datetime, timezone
from uuid import uuid4

from app.dao.repositories import CatalogDao, PropertyDao
from app.dao.template import NamedParameterJdbcTemplate
from app.db.datasource import data_source
from app.services.properties import PropertyService

CITIES = [
    ("Pune", "Maharashtra", ["Hinjewadi", "Kharadi", "Baner", "Wagholi", "Wakad"]),
    ("Mumbai", "Maharashtra", ["Andheri East", "Powai", "Thane", "Chembur"]),
    ("Bengaluru", "Karnataka", ["Whitefield", "Indiranagar", "Sarjapur Road"]),
    ("Hyderabad", "Telangana", ["Gachibowli", "Kondapur"]),
    ("Delhi NCR", "Delhi", ["Dwarka", "Noida Sector 150"]),
    ("Chennai", "Tamil Nadu", ["OMR", "Velachery"]),
    ("Kolkata", "West Bengal", ["New Town"]),
    ("Ahmedabad", "Gujarat", ["Prahlad Nagar"]),
    ("Jaipur", "Rajasthan", ["Vaishali Nagar"]),
    ("Lucknow", "Uttar Pradesh", ["Gomti Nagar"]),
]
PHOTOS = [
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c",
    "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
    "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0",
    "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea",
]
AMENITIES = [
    "Clubhouse",
    "Swimming pool",
    "Gymnasium",
    "24×7 security",
    "Power backup",
    "Parking",
    "Lift",
    "Children’s play area",
]
CATEGORIES = [
    "Apartment",
    "Independent house",
    "Villa",
    "Plot",
    "Penthouse",
    "Studio apartment",
    "Builder floor",
    "Commercial",
]


def slugify(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")


def main() -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with data_source.engine.begin() as connection:
        jdbc = NamedParameterJdbcTemplate(connection)
        if jdbc.query_one("seed.has_properties") is not None:
            print("Seed skipped: properties already exist")
            return

        property_dao = PropertyDao(connection)
        catalog_dao = CatalogDao(connection)
        amenity_ids: dict[str, int] = {}
        for name in AMENITIES:
            existing = property_dao.one("amenities.by_name", {"name": name})
            if existing is None:
                property_dao.insert("amenities.insert", {"name": name})
                existing = property_dao.one("amenities.by_name", {"name": name})
            amenity_ids[name] = existing["id"]

        state_ids: dict[str, int] = {}
        for city, state, localities in CITIES:
            if state not in state_ids:
                state_row = catalog_dao.one("states.by_name", {"name": state})
                if state_row is None:
                    state_row = catalog_dao.insert(
                        "states.insert", {"name": state, "code": None}
                    )
                state_ids[state] = state_row["id"]
            catalog_dao.insert(
                "cities.insert", {"state_id": state_ids[state], "name": city}
            )
            for index, locality in enumerate(localities):
                catalog_dao.insert(
                    "locations.insert",
                    {
                        "city": city,
                        "state": state,
                        "locality": locality,
                        "pincode": f"{411001 + index:06d}" if city == "Pune" else None,
                    },
                )

        for name in CATEGORIES:
            catalog_dao.insert(
                "seed.category_insert",
                {"name": name, "slug": slugify(name)},
            )

        developers = []
        for name in [
            "Demo VTP Realty",
            "Demo Prestige Group",
            "Demo Lodha Developers",
            "Demo Godrej Properties",
        ]:
            developer_id = str(uuid4())
            catalog_dao.insert(
                "seed.developer_insert",
                {
                    "id": developer_id,
                    "name": name,
                    "description": "Seeded demo developer profile. Verification has not been performed.",
                },
            )
            developers.append((developer_id, name))

        for index in range(36):
            city, state, localities = CITIES[index % len(CITIES)]
            locality = localities[index % len(localities)]
            is_rent = index % 3 == 0
            property_type = [
                "Apartment",
                "Villa",
                "Independent house",
                "Plot",
                "Builder floor",
            ][index % 5]
            price = 18000 + index * 2300 if is_rent else 4200000 + index * 1250000
            title = (
                f"Demo {['Olive', 'Serene', 'Lakeview', 'Palm', 'Garden', 'Urban'][index % 6]} "
                f"{property_type} in {locality}"
            )
            property_id = str(uuid4())
            values = PropertyService._values(
                {
                    "id": property_id,
                    "owner_id": None,
                    "property_id": f"DEMO-{index + 1:04d}",
                    "slug": f"demo-{slugify(title)}-{index + 1}",
                    "title": title,
                    "description": "DEMO LISTING — Sample development data for testing marketplace discovery. Confirm all property details, ownership, title and statutory approvals independently before any transaction.",
                    "transaction_type": "rent" if is_rent else "buy",
                    "property_type": property_type,
                    "status": "published",
                    "city": city,
                    "state": state,
                    "locality": locality,
                    "address": None,
                    "pincode": None,
                    "latitude": None,
                    "longitude": None,
                    "price": price,
                    "maintenance": None,
                    "deposit": price * 2 if is_rent else None,
                    "negotiable": False,
                    "bedrooms": 0 if property_type == "Plot" else 1 + index % 4,
                    "bathrooms": 0 if property_type == "Plot" else 1 + index % 3,
                    "balconies": index % 3,
                    "carpet_area": 550 + index * 75,
                    "builtup_area": 650 + index * 90,
                    "furnishing": ["Unfurnished", "Semi-furnished", "Fully furnished"][
                        index % 3
                    ],
                    "floor_number": None,
                    "total_floors": None,
                    "facing": None,
                    "parking": index % 3,
                    "age_years": None,
                    "possession_status": (
                        "Under construction" if index % 4 == 0 else "Ready to move"
                    ),
                    "rera_number": None,
                    "rera_verified": False,
                    "featured": index % 7 == 0,
                    "demo": True,
                }
            )
            property_dao.insert("properties.insert", values)
            property_dao.create_images(property_id, [PHOTOS[index % len(PHOTOS)]])
            for amenity in AMENITIES[: 3 + index % 4]:
                property_dao.insert(
                    "property_amenities.insert",
                    {"property_id": property_id, "amenity_id": amenity_ids[amenity]},
                )

        for index, (developer_id, name) in enumerate(developers):
            catalog_dao.insert(
                "seed.project_insert",
                {
                    "id": str(uuid4()),
                    "developer_id": developer_id,
                    "name": f"Demo {name.replace('Demo ', '')} Residences",
                    "slug": f"demo-project-{index + 1}",
                    "city": CITIES[index][0],
                    "locality": CITIES[index][2][0],
                    "price_min": 7500000 + index * 1500000,
                    "price_max": 15000000 + index * 2500000,
                    "status": "Under construction",
                    "possession_date": date(2028, 6, 30),
                },
            )

        catalog_dao.insert(
            "seed.agent_insert",
            {
                "id": str(uuid4()),
                "company": "Demo Aarav Realty",
                "experience_years": 6,
                "locations_served": ["Pune", "Mumbai"],
                "bio": "Seeded demo agent profile; not a verified professional.",
            },
        )
        catalog_dao.insert(
            "seed.blog_insert",
            {
                "id": str(uuid4()),
                "title": "A first-time buyer’s checklist",
                "slug": "first-time-buyer-checklist",
                "excerpt": "A practical checklist for researching a home purchase.",
                "content": "DEMO EDITORIAL CONTENT. Seek independent legal and financial advice.",
                "created_at": now,
            },
        )

    print("Seeded 36 demo properties, locations, amenities, projects, agents and editorial content.")


if __name__ == "__main__":
    main()
