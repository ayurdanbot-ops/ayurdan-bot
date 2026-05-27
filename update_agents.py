import os
import re

agents = [
    'expert_psoriasis.py', 'expert_allergy.py', 'expert_arthritis.py',
    'expert_backpain.py', 'expert_diabetes.py', 'expert_gynaecology.py',
    'expert_metabolic.py', 'expert_neurology.py', 'expert_anorectal.py',
    'expert_weight_loss.py', 'expert_weight_gain.py', 'expert_kadambary_cosmetic.py',
    'expert_post_delivery.py', 'expert_detoxification.py', 'expert_rejuvenation.py'
]

for agent in agents:
    path = os.path.join('agents', agent)
    if not os.path.exists(path):
        continue

    with open(path, 'r') as f:
        content = f.read()

    # Add imports if missing
    if 'import time' not in content:
        content = "import time\n" + content
    if 'from google.api_core.exceptions import ResourceExhausted' not in content:
        content = "from google.api_core.exceptions import ResourceExhausted\n" + content

    # Update process_request logic
    new_logic = """    max_retries = 3
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
"""

    pattern = r"    response = model\.generate_content\(contents, system_instruction=system_instruction\)\s+return response\.text"
    if re.search(pattern, content):
         content = re.sub(pattern, new_logic, content)
    else:
        # Try variation with strip
        pattern_strip = r"    response = model\.generate_content\(contents, system_instruction=system_instruction\)\s+return response\.text\.strip\(\)"
        if re.search(pattern_strip, content):
            content = re.sub(pattern_strip, new_logic, content)
        else:
            # Try variation from my previous edits
            pattern_last = r"    response = model\.generate_content\(contents, system_instruction=system_instruction\)\s+return response\.text"
            content = re.sub(pattern_last, new_logic, content)

    with open(path, 'w') as f:
        f.write(content)
