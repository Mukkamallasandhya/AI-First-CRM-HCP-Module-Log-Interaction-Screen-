"""Run with `python seed.py` (after setting DATABASE_URL) to populate a small
demo HCP roster so the 'Search or select HCP...' field and the chat agent's
search_hcp tool have real records to match against."""
from app.database import SessionLocal, Base, engine
from app.models import HCP

Base.metadata.create_all(bind=engine)

DEMO_HCPS = [
    {"name": "Dr. Sarah Smith", "specialty": "Cardiology", "hospital": "Mercy General Hospital"},
    {"name": "Dr. Raj Malhotra", "specialty": "Endocrinology", "hospital": "Apollo Hospitals"},
    {"name": "Dr. Emily Chen", "specialty": "Oncology", "hospital": "St. Luke's Medical Center"},
    {"name": "Dr. James Wilson", "specialty": "General Practice", "hospital": "Riverside Clinic"},
    {"name": "Dr. Priya Nair", "specialty": "Pediatrics", "hospital": "Sunrise Children's Hospital"},
]

if __name__ == "__main__":
    db = SessionLocal()
    try:
        for h in DEMO_HCPS:
            exists = db.query(HCP).filter(HCP.name == h["name"]).first()
            if not exists:
                db.add(HCP(**h))
        db.commit()
        print(f"Seeded {len(DEMO_HCPS)} demo HCPs.")
    finally:
        db.close()
