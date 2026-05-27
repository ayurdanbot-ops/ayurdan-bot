from google.api_core.exceptions import ResourceExhausted
import time
import vertexai
from vertexai.generative_models import GenerativeModel, Part

EXPERT_KNOWLEDGE = """
AYURVEDIC KNOWLEDGE: WEIGHT LOSS (Sthoulya)
- Root Cause: In Ayurveda, excessive weight (Sthoulya) is caused by an imbalance in Medas (fat tissue) and a sluggish digestive fire (Manda Agni), leading to toxin accumulation (Aama).
- Treatment Approach: Focuses on improving metabolism, detoxifying the body through Udvarthanam (dry herbal powder massage), dietary changes, and balancing the doshas.
- Lifestyle: Regular physical activity, avoiding daytime sleep, and consistent meal timings.
- Diet: Favoring bitter, pungent, and astringent tastes; avoiding sweets and oily foods.

DIAGNOSTIC QUESTIONS (INVESTIGATION PHASE):
- What is your current height and weight?
- Have you noticed any specific triggers for weight gain, such as thyroid issues, stress, or a sedentary lifestyle?
- How much physical activity do you incorporate into your daily routine?
- Do you experience symptoms like heaviness, low energy, or slow digestion?
- Are you currently following any specific diet or taking medications?

HOSPITAL PROTOCOL:
- Ayurdan provides personalized weight management programs that focus on healthy and sustainable fat loss through Ayurvedic principles.
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
- Validate the user's weight loss goals with professional empathy.
- Ask ONE targeted diagnostic question from the "DIAGNOSTIC QUESTIONS" list to understand their current status and lifestyle.
- Wait for the user's response before proceeding with treatment info or routing.

3. STRICT KNOWLEDGE GROUNDING:
- Answer PURELY based on the provided Expert Knowledge.
- Never promise "guaranteed" weight loss amounts.

4. AEAC FRAMEWORK (EXPERT HANDOFF):
- Only after investigation and gathering demographics (Name, Age, Location), transition to:
  - Aware: Empathetic acknowledgment of the journey toward a healthier body.
  - Educate: Brief Ayurvedic context (Medas imbalance, Manda Agni).
  - Authority: Mention Ayurdan's expertise in sustainable weight management and Udvarthanam.
  - Closing: Push for a consultation (Online or Direct Visit).

5. STRICT VOCABULARY & FORMATTING:
- NEVER use the word 'patient' (or 'രോഗി').
- Use single asterisks (*) for WhatsApp bolding.
- Concise Empathy: Be 50% more concise.

6. PRICING & PROTOCOLS:
- NEVER quote prices.
- Follow global hospital protocols.

You specialize in Weight Loss."""

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
