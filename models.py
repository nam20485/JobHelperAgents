import os

from agno.models.google import Gemini
from agno.models.openrouter import OpenRouter

gemini_3_model = Gemini(
    id="gemini-3-pro-preview",
)
gemini_2_5_flash_model = Gemini(id="gemini-2.5-flash")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_AGNO_API_KEY", "")


class OpenRouterModel(OpenRouter):
    def __init__(self, id: str):
        super().__init__(id=id, api_key=OPENROUTER_API_KEY)


qwen3_coder_model = OpenRouterModel(id="qwen/qwen3-coder:free")
gemini_flash_exp_model = OpenRouterModel(id="google/gemini-2.0-flash-exp:free")
glm_4_5_air_model = OpenRouterModel(id="z-ai/glm-4.5-air:free")
qwen3_235b_model = OpenRouterModel(id="qwen/qwen3-235b-a22b:free")
gpt_oss_model = OpenRouterModel(id="openai/gpt-oss-120b:free")
kimi_model = OpenRouterModel(id="moonshotai/kimi-k2:free")
