from google import genai
from google.genai import types
import re

from agents import (
    expert_backpain,
    expert_psoriasis,
    expert_anorectal,
    expert_post_delivery,
    expert_rejuvenation,
    expert_weight_loss,
    expert_weight_gain,
    expert_diabetes,
    expert_kadambary_cosmetic,
    expert_allergy,
    expert_arthritis
)
from memory_manager import get_active_expert, set_active_expert

WELCOME_BLUEPRINT = '''നമസ്കാരം! ആയുർദാൻ ആയുർവേദ ഹോസ്പിറ്റലിലേക്ക് അങ്ങേയ്ക്ക് സ്വാഗതം❤️

താങ്കളുടെ ആരോഗ്യത്തെക്കുറിച്ചുള്ള ആശങ്കകൾ എന്തുതന്നെയായാലും, ഇനി ആശ്വസിക്കാം. ഒരു കുടുംബാംഗത്തിന്റെ കരുതലോടും സ്നേഹത്തോടും കൂടി നിങ്ങളെ പരിചരിക്കാൻ ഞങ്ങൾ ഇവിടെയുണ്ട്.

കൃത്യമായ സഹായം നൽകാൻ താഴെ പറയുന്നവയിൽ ഏതാണ് നിങ്ങൾ തിരയുന്നത് എന്ന് ഒന്ന് വ്യക്തമാക്കാമോ?

🩺 *ഡോക്ടറെ കാണാൻ (Appointment)*

💊 *മരുന്നുകളെക്കുറിച്ച് അറിയാൻ*

📝 *ചികിത്സാ രീതികളെക്കുറിച്ചുള്ള സംശയങ്ങൾ*

📍 *ഹോസ്പിറ്റൽ ലൊക്കേഷൻ & സമയം*

💇‍♀️ *Hair & Beauty Clinic വിവരങ്ങൾ*

💅 *Rejuvenation & SPA*

💆‍♀️ *Body Massage അന്വേഷണങ്ങൾ*'''


RECEPTIONIST_PROMPT = '''
You are the Receptionist and Triage Expert at Ayurdan Ayurveda Hospital.
Your ONLY job is to gather mandatory patient details and route them to the correct specialist.

STRICT RULES:
1. ONE QUESTION LIMIT: Never ask more than one question at a time.
2. MANDATORY DATA: You MUST know the patient's Age, whether they are Male/Female, and their primary symptom.
3. GATHERING PHASE: If you do not have all 3 pieces of information, politely ask the patient for the missing piece. Use professional empathy.
4. THE HANDOFF (SILENT ROUTING): Once you have Age, Male/Female, and the Symptom, you must STOP talking to the patient. You must analyze the symptom and output EXACTLY ONE of the following routing tags, and absolutely nothing else:
   - [ROUTE: PSORIASIS] (For psoriasis, itching, scaling, skin issues)
   - [ROUTE: HAIR] (For hair fall, dandruff, baldness, Kadambary clinic)
   - [ROUTE: BACKPAIN] (For back pain, disc bulge, spine issues)
   - [ROUTE: ANORECTAL] (For piles, fistula, fissure, or painful bowel movements)
   - [ROUTE: ALLERGY] (For allergic reactions, sneezing, breathing issues)
   - [ROUTE: ARTHRITIS] (For joint pain, knee pain, arthritis)
   - [ROUTE: GENERAL] (For anything else, appointments, or general wellness)
'''


def handle_greeting(text: str, parts: list, history_text: str) -> str:
    client = genai.Client()
    model = 'gemini-3-flash-preview'

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_level='MINIMAL'),
        system_instruction=(
            """You are Ayur Care. The user has just sent a greeting or a first message.
Your ONLY job is to detect the language/script of the user's input and translate the provided Welcome Blueprint into that exact native language/script.
Strict Language Rule: The bot must translate the blueprint entirely into the user's detected native language/script (e.g., pure Malayalam script, or pure English).
STRICTLY FORBIDDEN: Do not use or output 'Manglish' (Malayalam written in the English alphabet) unless the user explicitly asks for it or uses it first."""
        )
    )

    contents = [f"Welcome Blueprint to translate:\n{WELCOME_BLUEPRINT}"]
    if parts:
        contents.extend(parts)
    if history_text:
        contents.append(f"Chat History:\n{history_text}")
    if text:
        contents.append(f"User Input to detect language from: {text}")

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    return response.text.strip()

def call_receptionist(text: str, parts: list, history_text: str) -> str:
    client = genai.Client()
    model = 'gemini-3-flash-preview'

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_level='MINIMAL'),
        system_instruction=RECEPTIONIST_PROMPT
    )

    contents = []
    if parts:
        contents.extend(parts)
    if history_text:
        contents.append(f"Chat History:\n{history_text}")
    if text:
        contents.append(f"Current User Input: {text}")

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    return response.text.strip()

def dispatch_to_expert(expert_tag: str, text: str, parts: list, history_text: str, state_notes: str) -> str:
    experts = {
        "BACKPAIN": expert_backpain,
        "PSORIASIS": expert_psoriasis,
        "HAIR": expert_kadambary_cosmetic,
        "ANORECTAL": expert_anorectal,
        "ALLERGY": expert_allergy,
        "ARTHRITIS": expert_arthritis,
        "GENERAL": expert_rejuvenation
    }
    expert_module = experts.get(expert_tag, expert_rejuvenation)
    return expert_module.process_request(text, parts, history_text, state_notes)

def get_expert_response(phone_number: str, text: str, parts: list = None, history_text: str = "", state_notes: str = "") -> str:
    active_expert = get_active_expert(phone_number)

    if not history_text.strip():
        # First message of the session, trigger dynamic Welcome message
        return handle_greeting(text, parts, history_text)

    if active_expert:
        # Bypass Receptionist
        return dispatch_to_expert(active_expert, text, parts, history_text, state_notes)

    # No active expert, send to Receptionist
    receptionist_reply = call_receptionist(text, parts, history_text)

    # Check for Routing Tag
    match = re.search(r'\[ROUTE:\s*(.*?)\]', receptionist_reply, re.IGNORECASE)

    if match:
        # We found a routing tag
        route_tag = match.group(1).upper()

        # Valid tags safety
        if route_tag not in ["PSORIASIS", "HAIR", "BACKPAIN", "ANORECTAL", "ALLERGY", "ARTHRITIS", "GENERAL"]:
            route_tag = "GENERAL"

        # Set Active Expert
        set_active_expert(phone_number, route_tag)

        # Forward everything to expert silently
        return dispatch_to_expert(route_tag, text, parts, history_text, state_notes)

    # Otherwise, it's a conversational gathering message. Return it to the user.
    return receptionist_reply
