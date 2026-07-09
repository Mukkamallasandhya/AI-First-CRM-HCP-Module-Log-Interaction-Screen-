from langchain_groq import ChatGroq

from app.config import settings

# Fast/cheap model - used for structured extraction, entity extraction,
# sentiment classification and short summarization inside tools.
extraction_llm = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_model,  # gemma2-9b-it
    temperature=0,
)

# Larger-context model - used for the conversational agent turns and for
# summarizing longer voice-note transcripts where more reasoning helps.
reasoning_llm = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_model_large,  # llama-3.3-70b-versatile
    temperature=0.3,
)
