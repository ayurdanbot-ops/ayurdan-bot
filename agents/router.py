from google import genai
from google.genai import types
from pydantic import BaseModel

from agents import (
    expert_backpain,
    expert_psoriasis,
    expert_anorectal,
    expert_post_delivery,
    expert_rejuvenation,
    expert_weight_loss,
    expert_weight_gain,
    expert_diabetes,
    expert_kadambary_cosmetic
)

WELCOME_BLUEPRINT = """നമസ്കാരം! ആയുർദാൻ ആയുർവേദ ഹോസ്പിറ്റലിലേക്ക് അങ്ങേയ്ക്ക് സ്വാഗതം❤️

താങ്കളുടെ ആരോഗ്യത്തെക്കുറിച്ചുള്ള ആശങ്കകൾ എന്തുതന്നെയായാലും, ഇനി ആശ്വസിക്കാം. ഒരു കുടുംബാംഗത്തിന്റെ കരുതലോടും സ്നേഹത്തോടും കൂടി നിങ്ങളെ പരിചരിക്കാൻ ഞങ്ങൾ ഇവിടെയുണ്ട്.

കൃത്യമായ സഹായം നൽകാൻ താഴെ പറയുന്നവയിൽ ഏതാണ് നിങ്ങൾ തിരയുന്നത് എന്ന് ഒന്ന് വ്യക്തമാക്കാമോ?

🩺 *ഡോക്ടറെ കാണാൻ (Appointment)*

💊 *മരുന്നുകളെക്കുറിച്ച് അറിയാൻ*

📝 *ചികിത്സാ രീതികളെക്കുറിച്ചുള്ള സംശയങ്ങൾ*

📍 *ഹോസ്പിറ്റൽ ലൊക്കേഷൻ & സമയം*

💇‍♀️ *Hair & Beauty Clinic വിവരങ്ങൾ*

💅 *Rejuvenation & SPA*

💆‍♀️ *Body Massage അന്വേഷണങ്ങൾ*"""

class RouteResponse(BaseModel):
    category: str

def handle_greeting(text: str, parts: list = None) -> str:
    client = genai.Client()
    model = 'gemini-3-flash-preview'

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_level='MINIMAL'),
        system_instruction=(
            "You are Ayur Care. The user has just sent a greeting or a first message."
            "Your ONLY job is to detect the language/script of the user's input and translate the provided Welcome Blueprint into that exact native language/script.\n"
            "Strict Language Rule: The bot must translate the blueprint entirely into the user's detected native language/script (e.g., pure Malayalam script, or pure English). "
            "STRICTLY FORBIDDEN: Do not use or output 'Manglish' (Malayalam written in the English alphabet) unless the user explicitly asks for it or uses it first."
        )
    )

    contents = [f"Welcome Blueprint to translate:\n{WELCOME_BLUEPRINT}"]
    if parts:
        contents.extend(parts)
    if text:
        contents.append(f"User Input to detect language from: {text}")

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    return response.text

def get_expert_response(text: str, parts: list = None) -> str:
    # 1. Route Intent
    client = genai.Client()

    routing_prompt = """Classify the user's intent based on the input provided into one of the following exact categories:
- greeting
- backpain
- psoriasis
- anorectal
- post_delivery
- rejuvenation
- weight_loss
- weight_gain
- diabetes
- kadambary_cosmetic

If it is a general greeting, an introductory message, or unclear, pick 'greeting'.
If it is about hair care, cosmetic, or beauty, use 'kadambary_cosmetic'.
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
        category = route_res.parsed.category if route_res.parsed else "greeting"
    except Exception as e:
        print(f"Routing failed: {e}")
        category = "greeting"

    print(f"Routed to category: {category}")

    # 2. Dispatch to Expert
    if category == "greeting":
        return handle_greeting(text, parts)

    experts = {
        "backpain": expert_backpain,
        "psoriasis": expert_psoriasis,
        "anorectal": expert_anorectal,
        "post_delivery": expert_post_delivery,
        "rejuvenation": expert_rejuvenation,
        "weight_loss": expert_weight_loss,
        "weight_gain": expert_weight_gain,
        "diabetes": expert_diabetes,
        "kadambary_cosmetic": expert_kadambary_cosmetic,
    }

    expert_module = experts.get(category, expert_rejuvenation)
    return expert_module.process_request(text, parts)
