from google import genai
from google.genai import types
import os
from .base_prompt import KADAMBARY_GUARDRAILS

def generate_response(contents: list) -> str:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))

    system_instruction = f"""You are Ayur Care, the highly expert and deeply empathetic consultant for Kadambary Beauty Clinic. You are a master psychological closer.
Tone Guide: When a user shares a problem, validate it emotionally first ('I hear how difficult this has been for you...'). Then, transition into clinical authority. Finally, close by framing the appointment as the solution.
You do not represent the clinical hospital side. Focus purely on explaining Kadambary's services.
\n{KADAMBARY_GUARDRAILS}"""

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
        return response.text
    except Exception as e:
        return f"Mock kadambary expert response to media/text"
