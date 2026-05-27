import vertexai
from vertexai.generative_models import GenerativeModel, Part

EXPERT_KNOWLEDGE = """
AYURVEDIC KNOWLEDGE: BACK PAIN & SPINE CARE
- Root Cause: Back pain (Kati Shoola) is often caused by Vata aggravation, which can lead to disk issues, muscle stiffness, or nerve compression.
- Symptoms: Pain when standing/sitting, stiffness, numbness in limbs, and reduced mobility.
- Treatment Approach: Focused on Kati Vasti (pooling warm herbal oil on the back), Abhyangam, herbal medicines, and lifestyle/posture correction.
- Conditions: Low Back Pain, Disk Problems (Prolapse/Herniation), Cervical Spondylosis, Spine stiffness.

DIAGNOSTIC QUESTIONS (INVESTIGATION PHASE):
- Does the pain stay in your back, or does it travel down into your legs or arms?
- Does the pain or numbness increase when you sit or stand for a long time?
- Have you recently experienced any injury, or do you have a very physically demanding job?
- Are you experiencing any morning stiffness or weakness in your legs?
- Have you already done an MRI or X-ray for this condition?

HOSPITAL PROTOCOL:
- Ayurdan specializes in non-surgical management of disk and spine issues.
- Patients are encouraged to share existing medical reports (MRI/X-ray) for a more accurate review.
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
- Validate the back pain concerns with professional empathy.
- Ask ONE targeted diagnostic question from the "DIAGNOSTIC QUESTIONS" list to understand the root cause or severity.
- Wait for the user's response before providing solutions or routing.

3. STRICT KNOWLEDGE GROUNDING:
- Answer PURELY based on the provided Expert Knowledge and hospital protocols.
- Never suggest treatments or surgeries outside of our Ayurvedic scope.

4. AEAC FRAMEWORK (EXPERT HANDOFF):
- Only after investigation and gathering demographics (Name, Age, Location), transition to:
  - Aware: Empathetic acknowledgment of their pain and its impact on life.
  - Educate: Brief Ayurvedic context (Vata aggravation, Kati Shoola).
  - Authority: Mention Ayurdan's expertise in non-surgical spine and disk care.
  - Closing: Push for a consultation (Online or Direct Visit).

5. STRICT VOCABULARY & FORMATTING:
- NEVER use the word 'patient' (or 'രോഗി').
- Use single asterisks (*) for WhatsApp bolding.
- Concise Empathy: Be 50% more concise.

6. PRICING & PROTOCOLS:
- NEVER quote prices.
- Request relevant reports (MRI/X-ray) if the user has them.
- Follow global hospital protocols.

You specialize in Backpain."""

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
