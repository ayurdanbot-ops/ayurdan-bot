import os
import re

agents = [
    'expert_psoriasis.py', 'expert_allergy.py', 'expert_arthritis.py',
    'expert_backpain.py', 'expert_diabetes.py', 'expert_gynaecology.py',
    'expert_metabolic.py', 'expert_neurology.py', 'expert_anorectal.py',
    'expert_weight_loss.py', 'expert_weight_gain.py', 'expert_kadambary_cosmetic.py',
    'expert_post_delivery.py', 'expert_detoxification.py', 'expert_rejuvenation.py'
]

smoothing_rules = """
2. SMART CONVERSATIONAL AGILITY:
- NO REPEATED QUESTIONS: Do not ask the same question twice. Check chat history.
- SMART QUESTION SKIPPING: If the user ignores a diagnostic question, do not re-ask it. Validate their input and move to the next step.
- ONE QUESTION LIMIT: Strictly ask only one question per message.

3. INVESTIGATION FIRST (STUDY PHASE):
"""

off_hours_rule = """
7. OFF-HOURS CALLBACK PROTOCOL (CRITICAL):
- If the user requests a call or appointment between 6:00 PM and 8:30 AM:
    - Inform them: "Our customer care team is currently offline, but they will be happy to contact you during our standard working hours (9:00 AM to 6:00 PM) to arrange your call and appointment."
"""

for agent in agents:
    path = os.path.join('agents', agent)
    if not os.path.exists(path):
        continue

    with open(path, 'r') as f:
        content = f.read()

    # Update smoothing rules
    if '2. INVESTIGATION FIRST' in content:
        content = content.replace('2. INVESTIGATION FIRST', smoothing_rules.strip())

    # Update off-hours protocol
    if '6. PRICING & PROTOCOLS:' in content:
        replacement = "6. PRICING & PROTOCOLS:\n- NEVER quote prices.\n- Follow global timing and booking protocols.\n" + off_hours_rule.strip()
        content = content.replace('6. PRICING & PROTOCOLS:', replacement)
    elif '7. PRICING & PROTOCOLS:' in content:
        replacement = "7. PRICING & PROTOCOLS:\n- NEVER quote prices.\n- Follow global timing and booking protocols.\n" + off_hours_rule.strip()
        content = content.replace('7. PRICING & PROTOCOLS:', replacement)

    with open(path, 'w') as f:
        f.write(content)
