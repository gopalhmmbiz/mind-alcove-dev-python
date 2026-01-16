from langchain.chat_models import  init_chat_model
from app.core.config import settings

SMART = "google_genai:gemini-2.5-flash"  # better reasoning
FAST = "google_genai:gemini-2.5-flash-lite"  # cheap, fast

llm = init_chat_model(FAST, api_key=settings.google_api_key)

# print(llm.profile)