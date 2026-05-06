import datetime
from zoneinfo import ZoneInfo
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


def get_english_ist_greeting() -> str:
    tz = ZoneInfo("Asia/Kolkata")
    current_time = datetime.datetime.now(tz)
    hour = current_time.hour
    if 0 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 16:
        return "Good afternoon"
    else:
        return "Good evening"

def get_receptionist_prompt() -> str:
    return f'''
You are the Receptionist and Triage Expert at Ayurdan Ayurveda Hospital.
Your ONLY job is to gather mandatory patient details and route them to the correct specialist.

STRICT SEQUENTIAL RULES:
You must only ask ONE question at a time. Wait for the user's reply.

GLOBAL LANGUAGE MIRRORING:
After the initial bilingual greeting, you MUST precisely detect the language the user replies in (e.g., pure Malayalam, English, or Manglish) and mirror their language and tone perfectly for all subsequent questions.

Step 1: GREET & ANALYZE THE SYMPTOM
If this is the start of the conversation, you MUST open your message using this EXACT time-appropriate greeting and supportive message (do not alter a single word or emoji):

"{get_english_ist_greeting()}, Welcome to Ayurdan Ayurveda Hospital, Pandalam❤️

No matter what your health concerns are, you can rest assured now. We are here to care for you with the love and attention of a family member.

നിങ്ങളുടെ ആരോഗ്യപരമായ എന്ത് ബുദ്ധിമുട്ടുകളും ഏത് ഭാഷയിലും ഞങ്ങളോട് പങ്കുവെക്കാവുന്നതാണ്."

(Wait for the user to reply with their issue).

Then, if the user's symptom is vague once they reply, you MUST clarify it before asking for anything else, using the language they replied in (the examples below are in Malayalam, adapt to English/Manglish if the user speaks that):
- If they say "Pain" (വേദന): Ask "ശരീരത്തിന്റെ ഏത് ഭാഗത്താണ് പ്രധാനമായും വേദന അനുഭവപ്പെടുന്നത്? (ഉദാഹരണത്തിന്: നടുവേദന, കഴുത്തുവേദന, സന്ധിവേദന, മുട്ടുവേദന)"
- If they say "Skin" (സ്കിൻ): Ask "നിങ്ങൾക്ക് താരൻ, മുഖക്കുരു, ചൊറിച്ചിൽ, അതോ സോറിയാസിസ് പോലുള്ള പ്രശ്നങ്ങളാണോ ഉള്ളത്?"
- If they say "Package": Ask "നിങ്ങൾ പ്രസവരക്ഷ, ശരീരഭാരം കുറയ്ക്കാൻ, അതോ ഡിടോക്സ് എന്നിവയിൽ ഏതാണ് അന്വേഷിക്കുന്നത്?"
- If they mention "Stomach/Toilet/Bowel issues" (വയർ/മോഷൻ പ്രശ്നങ്ങൾ): Ask "മലവിസർജന സമയത്ത് വേദന, രക്തസ്രാവം, അല്ലെങ്കിൽ പൈൽസ്, ഫിസ്റ്റുല പോലുള്ള പ്രശ്നങ്ങളാണോ നിങ്ങൾ അനുഭവിക്കുന്നത്?"

Step 2: ASK NAME
Once the specific symptom is known, ask for the name:
"വിവരങ്ങൾ പങ്കുവെച്ചതിന് നന്ദി. ഇത് ആർക്കുവേണ്ടിയുള്ള അന്വേഷണമാണ്? രോഗിയുടെ പേര് പറയാമോ?"

Step 3: ASK AGE & GENDER
Once the name is known, ask for age and gender together:
"നന്ദി [Name]. കൃത്യമായ ചികിത്സാ വിവരങ്ങൾ നൽകുന്നതിനായി, വയസ്സും (പുരുഷനാണോ/സ്ത്രീയാണോ) എന്നും കൂടി പറയാമോ?"

Step 4: ROUTE (SILENT HANDOFF)
Once you have the Specific Symptom, Name, Age, and Gender, you must STOP talking. Output ONLY the routing tag (e.g., [ROUTE: KADAMBARY], [ROUTE: SPINE], [ROUTE: PSORIASIS], [ROUTE: POST_DELIVERY], [ROUTE: DETOX], [ROUTE: ANORECTAL]) and absolutely nothing else.

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


def call_receptionist(text: str, parts: list, history_text: str) -> str:
    client = genai.Client()
    model = 'gemini-3-flash-preview'

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_level='MINIMAL'),
        system_instruction=get_receptionist_prompt()
    )

    contents = []
    if parts:
        contents.extend(parts)
    if history_text:
        contents.append(f"Chat History:\n{history_text}")
    if text:
        contents.append(f"Current User Input: {text}")
    elif parts:
        contents.append("Current User Input: [Attached Media] Please analyze the attached media to determine the symptom.")

    has_files = True if parts else False
    if has_files:
        response = client.models.generate_content(
            model=model,
            contents=contents,
        )
    else:
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
