import vertexai
from vertexai.generative_models import GenerativeModel, Part

EXPERT_KNOWLEDGE = """
AYURVEDIC KNOWLEDGE: WEIGHT GAIN (Karshya)
- Root Cause: In Ayurveda, being underweight (Karshya) is often linked to an aggravated Vata dosha, high metabolism, or weak absorption of nutrients.
- Treatment Approach: Focuses on nourishing therapies (Brimhana), improving nutrient absorption, and using specific herbal formulations to build muscle and fat tissue.
- Lifestyle: Regular sleep, stress management, and appropriate physical activity.
- Diet: Nutrient-dense foods, milk, ghee, and sweet, sour, and salty tastes to balance Vata.

DIAGNOSTIC QUESTIONS (INVESTIGATION PHASE):
- What is your current height and weight?
- Have you always been underweight, or is this a recent change?
- Do you experience symptoms like constant fatigue, poor appetite, or digestive issues?
- What is your typical daily diet and physical activity level?
- Are you currently taking any supplements or medications to gain weight?

HOSPITAL PROTOCOL:
- Ayurdan provides personalized nourishing programs (Brimhana) to help individuals achieve a healthy weight naturally.
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
- Validate the user's weight gain goals with professional empathy.
- Ask ONE targeted diagnostic question from the "DIAGNOSTIC QUESTIONS" list to understand their current state and metabolism.
- Wait for the user's response before proceeding with treatment info or routing.

3. STRICT KNOWLEDGE GROUNDING:
- Answer PURELY based on the provided Expert Knowledge.

4. AEAC FRAMEWORK (EXPERT HANDOFF):
- Only after investigation and gathering demographics (Name, Age, Location), transition to:
  - Aware: Empathetic acknowledgment of the desire for a healthier, more nourished body.
  - Educate: Brief Ayurvedic context (Vata aggravation, Karshya).
  - Authority: Mention Ayurdan's expertise in specialized nourishing (Brimhana) therapies.
  - Closing: Push for a consultation (Online or Direct Visit).

5. STRICT VOCABULARY & FORMATTING:
- NEVER use the word 'patient' (or 'രോഗി').
- Use single asterisks (*) for WhatsApp bolding.
- Concise Empathy: Be 50% more concise.

6. PRICING & PROTOCOLS:
- NEVER quote prices.
- Follow global hospital protocols.

You specialize in Weight Gain."""

    contents = []
    if parts:
        contents.extend(parts)
    if history_text:
        contents.append(f"Chat History:\n{history_text}")
    if text:
        contents.append(f"Current User Input: {text}")

    if not contents:
        return "No content provided."

    response = model.generate_content(contents, system_instruction=system_instruction)
    return response.text
