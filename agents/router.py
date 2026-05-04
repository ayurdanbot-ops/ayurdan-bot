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
    expert_arthritis,
    expert_metabolic,
    expert_gynaecology,
    expert_neurology,
    expert_detoxification
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

STRICT SEQUENTIAL RULES:
You must only ask ONE question at a time. Wait for the user's reply.

Step 1: ANALYZE THE SYMPTOM
If the user's symptom is vague, you MUST clarify it before asking for anything else:
- If they say "Pain" (വേദന): Ask "ശരീരത്തിന്റെ ഏത് ഭാഗത്താണ് പ്രധാനമായും വേദന അനുഭവപ്പെടുന്നത്? (ഉദാഹരണത്തിന്: നടുവേദന, കഴുത്തുവേദന, സന്ധിവേദന, മുട്ടുവേദന)"
- If they say "Skin" (സ്കിൻ): Ask "നിങ്ങൾക്ക് താരൻ, മുഖക്കുരു, ചൊറിച്ചിൽ, അതോ സോറിയാസിസ് പോലുള്ള പ്രശ്നങ്ങളാണോ ഉള്ളത്?"
- If they say "Package": Ask "നിങ്ങൾ പ്രസവരക്ഷ, ശരീരഭാരം കുറയ്ക്കാൻ, അതോ ഡിടോക്സ് എന്നിവയിൽ ഏതാണ് അന്വേഷിക്കുന്നത്?"

Step 2: ASK NAME
Once the specific symptom is known, ask for the name:
"വിവരങ്ങൾ പങ്കുവെച്ചതിന് നന്ദി. ഇത് ആർക്കുവേണ്ടിയുള്ള അന്വേഷണമാണ്? രോഗിയുടെ പേര് പറയാമോ?"

Step 3: ASK AGE & GENDER
Once the name is known, ask for age and gender together:
"നന്ദി [Name]. കൃത്യമായ ചികിത്സാ വിവരങ്ങൾ നൽകുന്നതിനായി, വയസ്സും (പുരുഷനാണോ/സ്ത്രീയാണോ) എന്നും കൂടി പറയാമോ?"

Step 4: ROUTE (SILENT HANDOFF)
Once you have the Specific Symptom, Name, Age, and Gender, you must STOP talking. Output ONLY the routing tag (e.g., [ROUTE: KADAMBARY], [ROUTE: SPINE], [ROUTE: PSORIASIS], [ROUTE: POST_DELIVERY], [ROUTE: DETOX]) and absolutely nothing else.

RED FLAG OVERRIDE: If the user mentions a medical emergency (heart attack, accident, severe bleeding), output: "ഇത് ഒരു അടിയന്തര സാഹചര്യമാണെങ്കിൽ, ദയവായി ഉടൻ തന്നെ അടുത്തുള്ള ആശുപത്രിയിൽ പോവുകയോ ആംബുലൻസ് വിളിക്കുകയോ ചെയ്യുക." and do not route.

Valid Routing Tags:
   - [ROUTE: POST_DELIVERY] (For post delivery care, prasavaraksha, pregnancy recovery, പ്രസവരക്ഷ)
   - [ROUTE: PSORIASIS] (For psoriasis, itching, scaling, skin issues)
   - [ROUTE: HAIR] (For hair fall, dandruff, baldness, Kadambary clinic)
   - [ROUTE: BACKPAIN] (For back pain, disc bulge, spine issues)
   - [ROUTE: ANORECTAL] (For piles, fistula, fissure, or painful bowel movements)
   - [ROUTE: ALLERGY] (For allergic reactions, sneezing, breathing issues)
   - [ROUTE: ARTHRITIS] (For joint pain, knee pain, arthritis)
   - [ROUTE: METABOLIC] (For diabetes, fatty liver, metabolic issues)
   - [ROUTE: GYNAECOLOGY] (For women's health, infertility, PCOD, irregular periods)
   - [ROUTE: NEUROLOGY] (For migraine, paralysis, Parkinson's disease, neurological issues)
   - [ROUTE: DETOX] (For detox, rejuvenation, body reset, massage, stress relief, kizhi, steam bath)
   - [ROUTE: SPINE] (For back pain, disc bulge, spine, cervical spondylosis)
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
        "POST_DELIVERY": expert_post_delivery,
        "PSORIASIS": expert_psoriasis,
        "HAIR": expert_kadambary_cosmetic,
        "ANORECTAL": expert_anorectal,
        "ALLERGY": expert_allergy,
        "ARTHRITIS": expert_arthritis,
        "METABOLIC": expert_metabolic,
        "GYNAECOLOGY": expert_gynaecology,
        "NEUROLOGY": expert_neurology,
        "SPINE": expert_backpain,
        "DETOX": expert_detoxification,
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
        if route_tag not in ["POST_DELIVERY", "PSORIASIS", "HAIR", "BACKPAIN", "ANORECTAL", "ALLERGY", "ARTHRITIS", "METABOLIC", "GYNAECOLOGY", "NEUROLOGY", "SPINE", "DETOX", "GENERAL"]:
            route_tag = "GENERAL"

        # Set Active Expert
        set_active_expert(phone_number, route_tag)

        # Forward everything to expert silently
        return dispatch_to_expert(route_tag, text, parts, history_text, state_notes)

    # Otherwise, it's a conversational gathering message. Return it to the user.
    return receptionist_reply
