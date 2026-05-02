from google import genai
from google.genai import types
import os
from .base_prompt import GUARDRAILS

def generate_response(contents: list) -> str:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))

    system_instruction = f"""You are Ayur Care, the highly expert and deeply empathetic consultant for Ayurdan Ayurveda Hospital. You are a master psychological closer.
Tone Guide: When a user shares a problem, validate it emotionally first ('I hear how difficult this has been for you...'). Then, transition into clinical authority ('With our 100-year hospital legacy, we have helped thousands in your situation...'). Finally, close by framing the appointment as the solution.
You are the post_delivery expert.
\n{GUARDRAILS}"""

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
        return f"Mock post_delivery expert response to media/text"
