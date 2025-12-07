import os

from agno.models.google import Gemini
from agno.models.openrouter import OpenRouter

gemini_3_model = Gemini(
    id="gemini-3-pro-preview",
)

gemini_2_5_flash_model = Gemini(id="gemini-2.5-flash")

openrouter_grok4_1_fast_model = OpenRouter(
    id="x-ai/grok-4.1-fast:free",
    api_key=os.getenv("OPENROUTER_AGNO_API_KEY"),
)

models = {
    "gemini_3": gemini_3_model,
    "gemini_2_5_flash": gemini_2_5_flash_model,
    "openrouter_grok4_1_fast": openrouter_grok4_1_fast_model,
}
