from google import genai
from google.genai import types

def process_request(text: str, parts: list = None) -> str:
    client = genai.Client()
    model = 'gemini-3-flash-preview'

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_level='MINIMAL'),
        system_instruction=(
            "You are Ayur Care, an AI sales expert for Ayurdan Ayurveda Hospital, specializing in Post Delivery care. "
            "You act as a 'Psychological Closer' utilizing a 3-step framework: Empathy, Authority, The Close. "
            "Rules: "
            "1. Empathy: Validate pain/concerns first. "
            "2. Authority: Mention our 100-year hospital legacy and 30-year product trust. "
            "3. Language: Strictly use 'Detect and Mirror' for Malayalam/English text and audio. "
            "4. Never provide medical diagnoses, always pivot to bookings."
        )
    )

    contents = []
    if parts:
        contents.extend(parts)
    if text:
        contents.append(text)

    if not contents:
        return "No content provided."

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    return response.text
