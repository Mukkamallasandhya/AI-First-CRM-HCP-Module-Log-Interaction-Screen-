from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/hcps", tags=["hcps"])


@router.get("", response_model=List[schemas.HCPOut])
def search_hcps(q: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    """Used by the 'Search or select HCP...' autocomplete field on the form."""
    query = db.query(models.HCP)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.HCP.name.ilike(like), models.HCP.specialty.ilike(like)))
    return query.limit(20).all()
