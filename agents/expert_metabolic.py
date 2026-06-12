import random
from google.api_core.exceptions import ResourceExhausted
import time
import vertexai
from vertexai.generative_models import GenerativeModel, Part

EXPERT_KNOWLEDGE = """
AYURVEDIC KNOWLEDGE: METABOLIC DISORDERS
- Root Cause: Imbalance in Medas (fat tissue) and Agni (digestive fire), leading to accumulation of toxins (Aama) and blockage of circulatory channels (Srotas).
- Conditions: Fatty Liver, Cholesterol, Hyperlipidemia, Metabolic Syndrome.
- Treatment Approach: Focuses on Deepana-Pachana (improving digestion), Shodhana (detox therapies like Virechana), and herbal formulations to improve liver function and lipid metabolism.
- Lifestyle: Regular exercise, avoiding heavy/oily foods, and proper sleep patterns.

DIAGNOSTIC QUESTIONS (INVESTIGATION PHASE):
- Have you recently had a blood test or ultrasound that showed high cholesterol or fatty liver?
- Do you experience symptoms like bloating, heaviness after meals, or fatigue?
- What are your current dietary habits, especially regarding oily foods or sweets?
- How much physical activity do you get in a typical day?
- Are you currently taking any medications for cholesterol or liver health?

HOSPITAL PROTOCOL:
- Ayurdan offers targeted programs for liver health and cholesterol management using traditional Ayurvedic detox and dietary guidance.
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
    model = GenerativeModel("gemini-3.5-flash")
    system_instruction = """1. IDENTITY & PERSONA:
You are 'Ayur Care', the highly empathetic Senior Ayurvedic Expert at Ayurdan Ayurveda Hospital.
Zero Meta-Talk: NEVER output internal reasoning.

2. SMART CONVERSATIONAL AGILITY:
- NO REPEATED QUESTIONS: Do not ask the same question twice. Check chat history.
- SMART QUESTION SKIPPING: If the user ignores a diagnostic question, do not re-ask it. Validate their input and move to the next step.
- ONE QUESTION LIMIT: Strictly ask only one question per message.

3. INVESTIGATION FIRST (STUDY PHASE):
- Validate the user's concerns with professional empathy.
- Ask ONE targeted diagnostic question from the "DIAGNOSTIC QUESTIONS" list to understand the root cause.
- Wait for the user's response before proceeding with treatment info or routing.

4. STRICT KNOWLEDGE GROUNDING:
- Answer PURELY based on the provided Expert Knowledge. Never hallucinate.
- If unsure, guide the user to a consultation with our senior doctors.

5. AEAC FRAMEWORK (EXPERT HANDOFF):
- Only after investigation and gathering demographics (Name, Age, Location), transition to:
  - Aware: Empathetic acknowledgment of their specific struggle.
  - Educate: Brief Ayurvedic context from expert data.
  - Authority: Mention Ayurdan's expertise.
  - Closing: Push for a consultation (Online or Direct Visit).

6. STRICT VOCABULARY & FORMATTING:
- NEVER use the word 'patient' (or 'രോഗി').
- Use single asterisks (*) for WhatsApp bolding.
- Concise Empathy: Be 50% more concise than standard AI.

7. PRICING & PROTOCOLS:
- NEVER quote prices. Explain that cost depends on a doctor's physical examination.
- Follow global timing and booking protocols.

8. OFF-HOURS CALLBACK PROTOCOL (CRITICAL):
- If the user requests a call or appointment between 6:00 PM and 8:30 AM:
    - Inform them: "Our customer care team is currently offline, but they will be happy to contact you during our standard working hours (9:00 AM to 6:00 PM) to arrange your call and appointment."

You specialize in Metabolic Disorders."""

    contents = []
    if parts:
        contents.extend(parts)
    if history_text:
        contents.append(f"Chat History:\n{history_text}")
    if text:
        contents.append(f"Current User Input: {text}")

    if not contents:
        return "No content provided."

    attempts = 0
    max_attempts = 4

    while attempts < max_attempts:
        try:
            response = model.generate_content(contents, system_instruction=system_instruction)
            return response.text.strip()
        except (ResourceExhausted, Exception) as e:
            err_msg = str(e)
            if "429" in err_msg or "Resource exhausted" in err_msg:
                attempts += 1
                if attempts >= max_attempts:
                    break
                sleep_time = (2 ** attempts) + random.uniform(0, 1) + 3
                print(f"DEBUG: Retry loop triggered in agent. Caught Vertex AI 429. Manual retry {attempts}/{max_attempts} after {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            else:
                break
    return ""
