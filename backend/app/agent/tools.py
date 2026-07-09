"""
LangGraph tools for the HCP Interaction agent.

Five tools, as required by the brief:
  1. log_interaction        - creates a new Interaction row (structured or from free text)
  2. edit_interaction       - patches an existing Interaction row
  3. search_hcp              - looks up an HCP by name/specialty so the agent can
                                resolve "Dr. Smith" to a real record and autofill the form
  4. summarize_voice_note    - takes a raw transcript and returns a structured summary
                                (topics, sentiment, entities) using the LLM
  5. schedule_followup       - sets/patches the follow-up date & notes on an interaction,
                                separate from edit_interaction because it has its own
                                validation (date must be in the future) and is a distinct
                                sales workflow (follow-up task creation)
"""
import datetime as dt
import json
from typing import Optional, List

from langchain_core.tools import tool
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import HCP, Interaction, MaterialShared, InteractionType, Sentiment
from app.agent.llm import extraction_llm, reasoning_llm


def _get_session() -> Session:
    return SessionLocal()


def _find_or_create_hcp(db: Session, hcp_name: str) -> Optional[HCP]:
    if not hcp_name:
        return None
    hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name.strip()}%")).first()
    return hcp  # we don't auto-create HCP master records; sales reps pick from an existing roster


# ---------------------------------------------------------------------------
# Tool 1: Log Interaction
# ---------------------------------------------------------------------------
@tool
def log_interaction(
    hcp_name: str,
    interaction_type: str = "Meeting",
    topics_discussed: str = "",
    sentiment: str = "",
    materials_shared: Optional[List[str]] = None,
    raw_text: str = "",
) -> str:
    """Create and save a new HCP interaction record.

    Use this when the rep describes a completed interaction, e.g.
    "Met Dr. Smith, discussed Prodo-X efficacy, positive sentiment, shared brochure".
    If sentiment or topics are not explicitly given but `raw_text` (the rep's free-form
    message) is provided, this tool will use the LLM to extract them automatically.

    Args:
        hcp_name: Name of the healthcare professional (e.g. "Dr. Smith").
        interaction_type: One of Meeting, Call, Email, Conference, Sample Drop.
        topics_discussed: Key discussion points, if already known.
        sentiment: Positive, Neutral, or Negative, if already known.
        materials_shared: List of sample/material names distributed.
        raw_text: The original free-text description of the interaction, used for
            entity extraction when structured fields above are incomplete.

    Returns:
        A JSON string with the created interaction's id and extracted fields.
    """
    db = _get_session()
    try:
        extracted = {}
        if raw_text and (not topics_discussed or not sentiment):
            extracted = _extract_entities_from_text(raw_text)

        final_topics = topics_discussed or extracted.get("topics_discussed", "")
        final_sentiment = sentiment or extracted.get("sentiment", "Neutral")
        final_materials = materials_shared or extracted.get("materials_shared", [])
        final_type = interaction_type or extracted.get("interaction_type", "Meeting")

        hcp = _find_or_create_hcp(db, hcp_name)

        try:
            itype_enum = InteractionType(final_type)
        except ValueError:
            itype_enum = InteractionType.meeting
        try:
            sentiment_enum = Sentiment(final_sentiment)
        except ValueError:
            sentiment_enum = Sentiment.neutral

        interaction = Interaction(
            hcp_id=hcp.id if hcp else None,
            hcp_name_raw=hcp_name,
            interaction_type=itype_enum,
            date=dt.datetime.utcnow(),
            topics_discussed=final_topics,
            sentiment=sentiment_enum,
            raw_transcript=raw_text or None,
            summary=extracted.get("summary"),
        )
        db.add(interaction)
        db.flush()

        for m in final_materials:
            db.add(MaterialShared(interaction_id=interaction.id, name=m))

        db.commit()

        return json.dumps({
            "status": "success",
            "interaction_id": interaction.id,
            "hcp_name": hcp_name,
            "hcp_matched": bool(hcp),
            "interaction_type": itype_enum.value,
            "topics_discussed": final_topics,
            "sentiment": sentiment_enum.value,
            "materials_shared": final_materials,
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 2: Edit Interaction
# ---------------------------------------------------------------------------
@tool
def edit_interaction(
    interaction_id: str,
    topics_discussed: Optional[str] = None,
    sentiment: Optional[str] = None,
    interaction_type: Optional[str] = None,
    materials_shared: Optional[List[str]] = None,
    hcp_name: Optional[str] = None,
) -> str:
    """Modify fields on an already-logged interaction.

    Use this when the rep wants to correct or add to a previous log, e.g.
    "Actually change the sentiment to Positive" or "Add that I also left the
    dosing brochure" for an existing interaction_id.

    Args:
        interaction_id: The id of the interaction to update (required).
        topics_discussed: New/updated topics text, if changing.
        sentiment: New sentiment (Positive, Neutral, Negative), if changing.
        interaction_type: New interaction type, if changing.
        materials_shared: Replacement list of materials, if changing.
        hcp_name: Corrected HCP name, if changing.

    Returns:
        A JSON string confirming which fields were updated, or an error if the
        interaction_id was not found.
    """
    db = _get_session()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"status": "error", "message": f"No interaction found with id {interaction_id}"})

        updated_fields = []

        if topics_discussed is not None:
            interaction.topics_discussed = topics_discussed
            updated_fields.append("topics_discussed")
        if sentiment is not None:
            try:
                interaction.sentiment = Sentiment(sentiment)
                updated_fields.append("sentiment")
            except ValueError:
                pass
        if interaction_type is not None:
            try:
                interaction.interaction_type = InteractionType(interaction_type)
                updated_fields.append("interaction_type")
            except ValueError:
                pass
        if hcp_name is not None:
            hcp = _find_or_create_hcp(db, hcp_name)
            interaction.hcp_name_raw = hcp_name
            interaction.hcp_id = hcp.id if hcp else interaction.hcp_id
            updated_fields.append("hcp_name")
        if materials_shared is not None:
            db.query(MaterialShared).filter(MaterialShared.interaction_id == interaction_id).delete()
            for m in materials_shared:
                db.add(MaterialShared(interaction_id=interaction_id, name=m))
            updated_fields.append("materials_shared")

        interaction.updated_at = dt.datetime.utcnow()
        db.commit()

        return json.dumps({
            "status": "success",
            "interaction_id": interaction_id,
            "updated_fields": updated_fields,
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 3: Search HCP
# ---------------------------------------------------------------------------
@tool
def search_hcp(query: str) -> str:
    """Search the HCP roster by name or specialty.

    Use this to resolve a name the rep typed (e.g. "Dr. Smith" or "cardiologists
    at Mercy General") to real HCP records before logging an interaction, or when
    the rep asks "who have I met with recently in cardiology".

    Args:
        query: Free-text search - a name, specialty, or hospital.

    Returns:
        A JSON string with a list of matching HCPs (id, name, specialty, hospital).
    """
    db = _get_session()
    try:
        like = f"%{query.strip()}%"
        results = db.query(HCP).filter(
            or_(HCP.name.ilike(like), HCP.specialty.ilike(like), HCP.hospital.ilike(like))
        ).limit(10).all()
        return json.dumps({
            "status": "success",
            "results": [
                {"id": h.id, "name": h.name, "specialty": h.specialty, "hospital": h.hospital}
                for h in results
            ],
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 4: Summarize Voice Note
# ---------------------------------------------------------------------------
@tool
def summarize_voice_note(transcript: str) -> str:
    """Summarize a raw voice-note transcript of an HCP interaction into structured fields.

    Use this when the rep has dictated a voice note (already transcribed to text)
    describing a visit, and wants it turned into a clean summary plus extracted
    topics/sentiment/materials before logging. This does NOT save anything to the
    database - it only returns the structured extraction so the calling agent/tool
    (log_interaction) can act on it, or so the frontend can preview it for the rep
    to confirm first (voice-note summarization requires rep consent per the UI).

    Args:
        transcript: The raw transcribed text of the voice note.

    Returns:
        A JSON string with keys: summary, topics_discussed, sentiment, materials_shared,
        suggested_hcp_name.
    """
    extracted = _extract_entities_from_text(transcript, include_hcp_guess=True)
    return json.dumps({"status": "success", **extracted})


def _extract_entities_from_text(text: str, include_hcp_guess: bool = False) -> dict:
    """Shared helper: calls the LLM to pull structured fields out of free text."""
    hcp_field = '  "suggested_hcp_name": "<best guess of HCP name mentioned, or empty string>",\n' if include_hcp_guess else ""
    prompt = f"""You are a pharma CRM assistant. Extract structured information from this
field rep's note about a healthcare professional (HCP) interaction.

Note: \"\"\"{text}\"\"\"

Respond with ONLY a valid JSON object (no markdown, no commentary) with exactly these keys:
{{
  "summary": "<one or two sentence neutral summary>",
  "topics_discussed": "<comma separated key discussion points>",
  "sentiment": "<one of: Positive, Neutral, Negative>",
  "materials_shared": ["<material 1>", "<material 2>"],
{hcp_field}  "interaction_type": "<one of: Meeting, Call, Email, Conference, Sample Drop>"
}}"""
    try:
        response = reasoning_llm.invoke(prompt)
        content = response.content.strip()
        # Strip accidental markdown code fences
        if content.startswith("```"):
            content = content.strip("`")
            content = content.split("\n", 1)[1] if "\n" in content else content
            if content.lower().startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception:
        # Graceful fallback if the model returns non-JSON or the API call fails
        return {
            "summary": text[:200],
            "topics_discussed": text[:200],
            "sentiment": "Neutral",
            "materials_shared": [],
            "interaction_type": "Meeting",
        }


# ---------------------------------------------------------------------------
# Tool 5: Schedule Follow-up
# ---------------------------------------------------------------------------
@tool
def schedule_followup(interaction_id: str, follow_up_notes: str, follow_up_date: str) -> str:
    """Set a follow-up task/date on a previously logged interaction.

    Use this when the rep says something like "remind me to follow up with Dr. Smith
    next Tuesday about the new dosing study" after an interaction has already been logged.

    Args:
        interaction_id: The id of the interaction this follow-up relates to.
        follow_up_notes: What the follow-up is about.
        follow_up_date: ISO date/datetime string (e.g. "2026-07-15") for the follow-up.

    Returns:
        A JSON string confirming the scheduled follow-up, or an error message if the
        date is invalid or in the past, or the interaction doesn't exist.
    """
    db = _get_session()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"status": "error", "message": f"No interaction found with id {interaction_id}"})

        try:
            parsed_date = dt.datetime.fromisoformat(follow_up_date)
        except ValueError:
            return json.dumps({"status": "error", "message": f"Could not parse date '{follow_up_date}'. Use ISO format e.g. 2026-07-15."})

        if parsed_date.date() < dt.datetime.utcnow().date():
            return json.dumps({"status": "error", "message": "Follow-up date cannot be in the past."})

        interaction.follow_up_notes = follow_up_notes
        interaction.follow_up_date = parsed_date
        db.commit()

        return json.dumps({
            "status": "success",
            "interaction_id": interaction_id,
            "follow_up_date": parsed_date.isoformat(),
            "follow_up_notes": follow_up_notes,
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()


ALL_TOOLS = [log_interaction, edit_interaction, search_hcp, summarize_voice_note, schedule_followup]
