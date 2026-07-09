import datetime as dt
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.post("", response_model=schemas.InteractionOut)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """Create an interaction from the structured form (not via chat/agent)."""
    hcp = db.query(models.HCP).filter(models.HCP.name.ilike(f"%{payload.hcp_name}%")).first()

    try:
        itype = models.InteractionType(payload.interaction_type)
    except ValueError:
        itype = models.InteractionType.meeting
    sentiment = None
    if payload.sentiment:
        try:
            sentiment = models.Sentiment(payload.sentiment)
        except ValueError:
            sentiment = None

    interaction = models.Interaction(
        hcp_id=hcp.id if hcp else None,
        hcp_name_raw=payload.hcp_name,
        interaction_type=itype,
        date=payload.date or dt.datetime.utcnow(),
        topics_discussed=payload.topics_discussed,
        sentiment=sentiment,
        follow_up_notes=payload.follow_up_notes,
        follow_up_date=payload.follow_up_date,
        raw_transcript=payload.raw_transcript,
    )
    db.add(interaction)
    db.flush()

    for m in payload.materials:
        db.add(models.MaterialShared(interaction_id=interaction.id, name=m.name, quantity=m.quantity))

    db.commit()
    db.refresh(interaction)
    return interaction


@router.get("", response_model=List[schemas.InteractionOut])
def list_interactions(db: Session = Depends(get_db)):
    return db.query(models.Interaction).order_by(models.Interaction.date.desc()).all()


@router.get("/{interaction_id}", response_model=schemas.InteractionOut)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.patch("/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(interaction_id: str, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    data = payload.model_dump(exclude_unset=True)

    if "hcp_name" in data:
        interaction.hcp_name_raw = data["hcp_name"]
    if "interaction_type" in data:
        try:
            interaction.interaction_type = models.InteractionType(data["interaction_type"])
        except ValueError:
            pass
    if "date" in data:
        interaction.date = data["date"]
    if "topics_discussed" in data:
        interaction.topics_discussed = data["topics_discussed"]
    if "sentiment" in data:
        try:
            interaction.sentiment = models.Sentiment(data["sentiment"])
        except ValueError:
            pass
    if "follow_up_notes" in data:
        interaction.follow_up_notes = data["follow_up_notes"]
    if "follow_up_date" in data:
        interaction.follow_up_date = data["follow_up_date"]
    if "materials" in data:
        db.query(models.MaterialShared).filter(models.MaterialShared.interaction_id == interaction_id).delete()
        for m in data["materials"]:
            db.add(models.MaterialShared(interaction_id=interaction_id, name=m["name"], quantity=m.get("quantity", "1")))

    interaction.updated_at = dt.datetime.utcnow()
    db.commit()
    db.refresh(interaction)
    return interaction


@router.delete("/{interaction_id}")
def delete_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(interaction)
    db.commit()
    return {"status": "deleted", "interaction_id": interaction_id}
