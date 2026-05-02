from google import genai
from google.genai import types
import os

INTENTS = [
    "BACK_PAIN",
    "PSORIASIS",
    "ANORECTAL",
    "POST_DELIVERY",
    "REJUVENATION",
    "WEIGHT_MGT",
    "HAIR_CARE",
    "KADAMBARY_COSMETIC",
    "DIABETES",
    "GENERAL_INQUIRY"
]

def classify_intent(contents: list) -> str:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))

    system_instruction = f"""Classify the user's intent into EXACTLY ONE of the following categories:
{', '.join(INTENTS)}
Respond with only the category name."""

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_level='MINIMAL')
    )

    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=contents,
            config=config
        )
        intent = response.text.strip().upper()
        if intent in INTENTS:
            return intent
        return "GENERAL_INQUIRY"
    except Exception as e:
        # Fallback for testing/errors
        message = ""
        for item in contents:
            if isinstance(item, str):
                message += item.lower()

        if "back" in message: return "BACK_PAIN"
        if "psoriasis" in message: return "PSORIASIS"
        if "piles" in message or "fistula" in message or "fissure" in message: return "ANORECTAL"
        if "delivery" in message: return "POST_DELIVERY"
        if "rejuvenation" in message: return "REJUVENATION"
        if "weight" in message: return "WEIGHT_MGT"
        if "hair" in message or "dandruff" in message or "alopecia" in message: return "HAIR_CARE"
        if "kadambary" in message or "cosmetic" in message: return "KADAMBARY_COSMETIC"
        if "diabetes" in message: return "DIABETES"
        return "GENERAL_INQUIRY"
