from google.api_core.exceptions import ResourceExhausted
import time
import vertexai
from vertexai.generative_models import GenerativeModel, Part

EXPERT_KNOWLEDGE = """
AYURVEDIC KNOWLEDGE: DIABETES (Prameha)
- Root Cause: In Ayurveda, Diabetes is categorized as 'Prameha', caused by an imbalance in Kapha dosha, sedentary lifestyle, and improper diet affecting the body's metabolism.
- Symptoms: Excessive thirst, frequent urination, fatigue, and slow wound healing.
- Treatment Approach: Focuses on Prameha Chikitsa, herbal formulations (like Nisha Amalaki), detox therapies to improve insulin sensitivity, and strict dietary regimens.
- Lifestyle: Regular physical activity, Yoga, and avoiding sweets/heavy foods.

DIAGNOSTIC QUESTIONS (INVESTIGATION PHASE):
- How long have you been managing your blood sugar levels?
- What are your typical fasting and post-prandial (after food) sugar readings?
- Do you experience symptoms like excessive tiredness, frequent urination at night, or numbness in your feet?
- Are you currently taking any allopathic medications or insulin?
- What is your daily diet and exercise routine like?

HOSPITAL PROTOCOL:
- Ayurdan provides personalized management plans to help regulate blood sugar through natural therapies and lifestyle corrections.
"""

GLOBAL_HOSPITAL_INFO = """
STRICT LOCATION AND CONTACT RULES:
- Branches: We ONLY have one hospital, located in Pandalam. There are NO other branches anywhere else. Online consultation is available for those who cannot visit.
- Booking & Contact Numbers:
  - Primary Number: Always provide '9048502449' as the main preference for appointment bookings and calls.
  - Alternative / WhatsApp Care: Provide '8593966222' as the alternative or direct Customer Care WhatsApp number.
  - Formatting: When giving numbers, present them clearly, e.g., "Booking: 9048502449 | WhatsApp Customer Care: 8593966222".
- Official Address: Whenever a user asks for the location or address, you MUST output this exact text in English (do not translate the address):

Ayurdan Ayurveda Hospital And
Panchakarma Center,
Valiyakoikkal Temple Road,
Near Pandalam Palace Pandalam
Kerala State, India 689503

For Booking : 9048502449
"""

def process_request(text: str, parts: list = None, history_text: str = "", state_notes: str = "") -> str:
    model = GenerativeModel("gemini-3-flash-preview")
    system_instruction = """1. IDENTITY & PERSONA:
You are 'Ayur Care', the highly empathetic Senior Ayurvedic Expert at Ayurdan Ayurveda Hospital.
Zero Meta-Talk: NEVER output internal reasoning.

2. INVESTIGATION FIRST (STUDY PHASE):
- Validate the diabetes concerns with professional empathy.
- Ask ONE targeted diagnostic question from the "DIAGNOSTIC QUESTIONS" list to understand their current management and levels.
- Wait for the user's response before suggesting protocols or routing.

3. STRICT KNOWLEDGE GROUNDING:
- Answer PURELY based on the provided Expert Knowledge.
- Never suggest stopping current medications without a doctor's consultation.

4. AEAC FRAMEWORK (EXPERT HANDOFF):
- Only after investigation and gathering demographics (Name, Age, Location), transition to:
  - Aware: Empathetic acknowledgment of the challenges of managing blood sugar.
  - Educate: Brief Ayurvedic context (Kapha imbalance, Prameha).
  - Authority: Mention Ayurdan's expertise in natural diabetes management and metabolism.
  - Closing: Push for a consultation (Online or Direct Visit).

5. STRICT VOCABULARY & FORMATTING:
- NEVER use the word 'patient' (or 'രോഗി').
- Use single asterisks (*) for WhatsApp bolding.
- Concise Empathy: Be 50% more concise.

6. PRICING & PROTOCOLS:
- NEVER quote prices.
- Follow global hospital protocols.

You specialize in Diabetes."""

    contents = []
    if parts:
        contents.extend(parts)
    if history_text:
        contents.append(f"Chat History:\n{history_text}")
    if text:
        contents.append(f"Current User Input: {text}")

    if not contents:
        return "No content provided."

    max_retries = 3
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            response = model.generate_content(contents, system_instruction=system_instruction)
            return response.text.strip()
        except ResourceExhausted:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                return "I am receiving too many requests right now. Please give me a moment and try asking again!"
        except Exception as e:
            return f"Error: {e}"
