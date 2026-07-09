import uuid
import datetime as dt

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Table, Float, Enum
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class InteractionType(str, enum.Enum):
    meeting = "Meeting"
    call = "Call"
    email = "Email"
    conference = "Conference"
    sample_drop = "Sample Drop"


class Sentiment(str, enum.Enum):
    positive = "Positive"
    neutral = "Neutral"
    negative = "Negative"


# Many-to-many: interaction <-> attendee (HCPs / colleagues present)
interaction_attendees = Table(
    "interaction_attendees",
    Base.metadata,
    Column("interaction_id", String(36), ForeignKey("interactions.id")),
    Column("attendee_name", String(255)),
)


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False, index=True)
    specialty = Column(String(255), nullable=True)
    hospital = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    interactions = relationship("Interaction", back_populates="hcp")


class MaterialShared(Base):
    __tablename__ = "materials_shared"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    interaction_id = Column(String(36), ForeignKey("interactions.id"))
    name = Column(String(255), nullable=False)
    quantity = Column(String(50), default="1")

    interaction = relationship("Interaction", back_populates="materials")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=True)
    hcp_name_raw = Column(String(255), nullable=True)  # fallback if HCP not matched to a record

    interaction_type = Column(Enum(InteractionType), default=InteractionType.meeting)
    date = Column(DateTime, default=dt.datetime.utcnow)

    topics_discussed = Column(Text, nullable=True)
    sentiment = Column(Enum(Sentiment), nullable=True)
    summary = Column(Text, nullable=True)  # AI-generated summary
    raw_transcript = Column(Text, nullable=True)  # original free-text / voice-note transcript

    follow_up_notes = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
    materials = relationship("MaterialShared", back_populates="interaction", cascade="all, delete-orphan")
