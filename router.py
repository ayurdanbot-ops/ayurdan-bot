from google import genai
from google.genai import types
from pydantic import BaseModel
import os

from agents import backpain, psoriasis, anorectal, post_delivery, rejuvenation, weight, diabetes, kadambary_cosmetic

class RouteResponse(BaseModel):
    category: str

def get_expert_response(text: str, parts: list = None) -> str:
    # 1. Route Intent
    client = genai.Client()

    routing_prompt = """Classify the user's intent based on the input provided into one of the following exact categories:
- backpain
- psoriasis
- anorectal
- post_delivery
- rejuvenation
- weight
- diabetes
- kadambary_cosmetic

If it is about hair care, cosmetic, or beauty, use 'kadambary_cosmetic'.
If it's a general greeting or unclear, pick 'rejuvenation' as a fallback.
Respond ONLY with the exact category name.
"""

    contents = []
    if parts:
        contents.extend(parts)
    contents.append(routing_prompt)
    if text:
        contents.append(f"User Input: {text}")

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RouteResponse,
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_level='MINIMAL'),
    )

    try:
        route_res = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=contents,
            config=config,
        )
        category = route_res.parsed.category if route_res.parsed else "rejuvenation"
    except Exception as e:
        print(f"Routing failed: {e}")
        category = "rejuvenation"

    print(f"Routed to category: {category}")

    # 2. Dispatch to Expert
    experts = {
        "backpain": backpain,
        "psoriasis": psoriasis,
        "anorectal": anorectal,
        "post_delivery": post_delivery,
        "rejuvenation": rejuvenation,
        "weight": weight,
        "diabetes": diabetes,
        "kadambary_cosmetic": kadambary_cosmetic,
    }

    expert_module = experts.get(category, rejuvenation)
    return expert_module.process_request(text, parts)
