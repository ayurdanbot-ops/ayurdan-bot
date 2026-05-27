from google.api_core.exceptions import ResourceExhausted
import time
import vertexai
from vertexai.generative_models import GenerativeModel, Part

EXPERT_KNOWLEDGE = """
AYURVEDIC KNOWLEDGE: ARTHRITIS & JOINT PAIN
- Root Cause: In Ayurveda, joint pain is primarily associated with Vata imbalance and the accumulation of Aama (toxins) in the joints (Sandhigata Vata).
- Symptoms: Pain, joint stiffness (especially in the morning), swelling, and reduced mobility.
- Treatment Approach: Focuses on balancing Vata, improving Agni (digestion) to eliminate toxins, and utilizing specific therapies like Janu Basti (for knee), Abhyangam, and herbal formulations.
- Conditions: Arthritis, Frozen Shoulder, Knee Pain, Joint stiffness.

DIAGNOSTIC QUESTIONS (INVESTIGATION PHASE):
- In which joints do you experience the most pain or stiffness?
- Is the pain worse in the morning or does it increase after activity?
- Do you notice any swelling or warmth in the painful area?
- How much does this pain affect your daily movements or sleep?
- Have you had any recent injuries or used any specific painkillers?

HOSPITAL PROTOCOL:
- Ayurdan provides comprehensive 14-21 day programs tailored to the severity of joint conditions.
- Focus is on long-term mobility and root cause management through Ayurveda, Yoga, and tailored diet.
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
- Validate the joint pain concerns with professional empathy.
- Ask ONE targeted diagnostic question from the "DIAGNOSTIC QUESTIONS" list to understand the nature of the stiffness or pain.
- Wait for the user's response. Do not recommend treatments or route the user until context is established.

3. STRICT KNOWLEDGE GROUNDING:
- Answer PURELY based on the provided Expert Knowledge.
- Do not suggest general home remedies unless they are specifically mentioned in our protocols.

4. AEAC FRAMEWORK (EXPERT HANDOFF):
- Only after investigation and gathering demographics (Name, Age, Location), transition to:
  - Aware: Empathetic acknowledgment of their mobility challenges.
  - Educate: Brief Ayurvedic context (Vata imbalance, Sandhigata Vata).
  - Authority: Mention Ayurdan's expertise in specialized joint and arthritis care.
  - Closing: Push for a consultation (Online or Direct Visit).

5. STRICT VOCABULARY & FORMATTING:
- NEVER use the word 'patient' (or 'രോഗി').
- Use single asterisks (*) for WhatsApp bolding.
- Concise Empathy: Be 50% more concise.

6. PRICING & PROTOCOLS:
- NEVER quote prices.
- Follow global hospital protocols.

You specialize in Arthritis."""

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
