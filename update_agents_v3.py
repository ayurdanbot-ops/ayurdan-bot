import os
import re

agents = [
    'expert_psoriasis.py', 'expert_allergy.py', 'expert_arthritis.py',
    'expert_backpain.py', 'expert_diabetes.py', 'expert_gynaecology.py',
    'expert_metabolic.py', 'expert_neurology.py', 'expert_anorectal.py',
    'expert_weight_loss.py', 'expert_weight_gain.py', 'expert_kadambary_cosmetic.py',
    'expert_post_delivery.py', 'expert_detoxification.py', 'expert_rejuvenation.py'
]

def clean_instruction(instr):
    # Remove duplicates and clean up sections
    lines = instr.split('\n')
    new_lines = []
    seen = set()
    for line in lines:
        l = line.strip()
        if l.startswith("6. PRICING") or l.startswith("7. PRICING"):
             if "6. PRICING" in seen or "7. PRICING" in seen:
                 continue
        if l in ["- NEVER quote prices.", "- Follow global timing and booking protocols.", "- Follow the global hospital timing and booking protocols.", "- NEVER quote prices. Explain that cost depends on a doctor's physical examination."]:
            if l in seen:
                continue
        new_lines.append(line)
        if l: seen.add(l)
    return '\n'.join(new_lines)

for agent in agents:
    path = os.path.join('agents', agent)
    if not os.path.exists(path):
        continue

    with open(path, 'r') as f:
        content = f.read()

    # Define the new system instruction template based on the most common structure
    # We will use regex to find the system_instruction block

    match = re.search(r'system_instruction = """(.*?)"""', content, re.DOTALL)
    if match:
        old_instr = match.group(1)

        # Build the refined instruction
        new_instr = old_instr

        # Ensure rules are present
        if "NO REPEATED QUESTIONS" not in new_instr:
            # Inject smoothing rules at section 2
            new_instr = re.sub(r'2\..*?\n',
                "2. SMART CONVERSATIONAL AGILITY:\n- NO REPEATED QUESTIONS: Do not ask the same question twice. Check chat history.\n- SMART QUESTION SKIPPING: If the user ignores a diagnostic question, do not re-ask it. Validate their input and move to the next step.\n- ONE QUESTION LIMIT: Strictly ask only one question per message.\n\n",
                new_instr)

        if "OFF-HOURS CALLBACK PROTOCOL" not in new_instr:
             # Inject off-hours rule at the end of protocols
             new_instr = re.sub(r'(6\..*?PRICING & PROTOCOLS:.*?\n)(.*?\n)*',
                 r'\1- NEVER quote prices.\n- Follow global timing and booking protocols.\n\n7. OFF-HOURS CALLBACK PROTOCOL (CRITICAL):\n- If the user requests a call or appointment between 6:00 PM and 8:30 AM:\n    - Inform them: "Our customer care team is currently offline, but they will be happy to contact you during our standard working hours (9:00 AM to 6:00 PM) to arrange your call and appointment."\n',
                 new_instr)

        content = content.replace(old_instr, new_instr)

    with open(path, 'w') as f:
        f.write(content)
