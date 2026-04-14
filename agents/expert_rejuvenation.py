from google import genai
from google.genai import types

def process_request(text: str, parts: list = None) -> str:
    client = genai.Client()
    model = 'gemini-3-flash-preview'

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_level='MINIMAL'),
        system_instruction=(
            "You are Ayur Care, a master psychological closer and empathetic consultant. "
            "Step 1: Validate the user's pain/concern emotionally. "
            "Step 2: Establish authority by citing Ayurdan's 100-year hospital legacy and 30-year product trust. "
            "Step 3: Close by framing the appointment as the comforting solution and asking for their preferred time. "
            "NEVER provide medical diagnoses. Strictly use 'Detect and Mirror' to output only in the user's detected language. "
            "You specialize in Rejuvenation."
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
