import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class MaterialIn(BaseModel):
    name: str
    quantity: str = "1"


class MaterialOut(MaterialIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


class HCPOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    specialty: Optional[str] = None
    hospital: Optional[str] = None


class InteractionCreate(BaseModel):
    hcp_name: str
    interaction_type: str = "Meeting"
    date: Optional[dt.datetime] = None
    attendees: List[str] = []
    topics_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    materials: List[MaterialIn] = []
    follow_up_notes: Optional[str] = None
    follow_up_date: Optional[dt.datetime] = None
    raw_transcript: Optional[str] = None  # if logging came from a voice note / chat message


class InteractionUpdate(BaseModel):
    """All fields optional - only supplied fields are changed (used by the Edit Interaction tool)."""
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    date: Optional[dt.datetime] = None
    attendees: Optional[List[str]] = None
    topics_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    materials: Optional[List[MaterialIn]] = None
    follow_up_notes: Optional[str] = None
    follow_up_date: Optional[dt.datetime] = None


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    hcp_name_raw: Optional[str]
    interaction_type: str
    date: dt.datetime
    topics_discussed: Optional[str]
    sentiment: Optional[str]
    summary: Optional[str]
    follow_up_notes: Optional[str]
    follow_up_date: Optional[dt.datetime]
    materials: List[MaterialOut] = []


class ChatMessageIn(BaseModel):
    message: str
    session_id: str = "default"
    # Optional partially-filled form state from the frontend, so the agent has
    # context on what's already on screen (Redux state) when the rep is using
    # the structured form + chat together.
    current_form_state: Optional[dict] = None


class ChatMessageOut(BaseModel):
    reply: str
    tool_calls: List[str] = []
    updated_form_state: Optional[dict] = None
    interaction_id: Optional[str] = None
