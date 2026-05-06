import sys

with open('main.py', 'r') as f:
    content = f.read()

# 1. Move imports to top
if "import tempfile" not in content[:500]:
    content = content.replace("from fastapi import FastAPI", "from fastapi import FastAPI\nimport tempfile\nimport time")

# Remove redundant imports inside functions
content = content.replace("    import tempfile\n", "")
content = content.replace("    import os\n", "")
content = content.replace("    import requests\n", "")
content = content.replace("    from google.genai import types\n", "")

# 2. Fix the webhook to send status messages (using background_tasks.add_task instead of the missing send_zoko_message inside webhook, or since it's already there we can just keep the existing background_tasks.add_task that was there at the top of webhook)
# Wait, let's look at the webhook
# The original webhook *did* have the status messages:
#     if message_type == 'audio':
#         background_tasks.add_task(send_zoko_message, phone_number, "Listening... 🎧")

# 3. Fix the experts dictionary and system prompt logic
# In our patch we replaced a try block but we messed up the system prompt. We need to pass the expert prompt.
old_try_block_start = """        # Build system prompt from active expert if any, otherwise use general
        from agents.router import get_receptionist_prompt
        from memory_manager import get_active_expert
        from agents import expert_backpain, expert_post_delivery, expert_psoriasis, expert_kadambary_cosmetic, expert_anorectal, expert_allergy, expert_arthritis, expert_metabolic, expert_gynaecology, expert_neurology, expert_detoxification, expert_rejuvenation

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

        active_expert = get_active_expert(phone_number)

        # NOTE: We can't easily extract the expert system prompt dynamically without executing it.
        # But we must pass *some* system instruction context.
        # However, the task description says "send ... along with ... system prompt" but doesn't specify which one.
        # Using a unified one or passing None to rely on the conversation history implicitly.
        # We will use get_receptionist_prompt() if no expert, else we just pass the history_text.
        system_prompt = get_receptionist_prompt() if not active_expert else None"""

new_try_block_start = """        from agents.router import get_receptionist_prompt
        from memory_manager import get_active_expert

        active_expert = get_active_expert(phone_number)

        system_prompt = None
        if active_expert:
            # We can't easily dynamically pull the exact expert prompt without modifying their code.
            # But the requirement states: "Send the file to Gemini along with conversation history and system prompt."
            # Since the user specifically requested not to touch expert files, we will try to pass a generic or receptionist prompt,
            # actually wait, let's just pass the receptionist prompt if no expert.
            # If there IS an expert, maybe we should construct a generic system prompt for the MoE routing handoff.
            # Or we can just import the expert module and try to get its prompt? No, they use EXPERT_KNOWLEDGE constant.
            from agents import expert_backpain, expert_post_delivery, expert_psoriasis, expert_kadambary_cosmetic, expert_anorectal, expert_allergy, expert_arthritis, expert_metabolic, expert_gynaecology, expert_neurology, expert_detoxification, expert_rejuvenation
            experts = {
                "BACKPAIN": getattr(expert_backpain, 'EXPERT_KNOWLEDGE', ''),
                "POST_DELIVERY": getattr(expert_post_delivery, 'EXPERT_KNOWLEDGE', ''),
                "PSORIASIS": getattr(expert_psoriasis, 'EXPERT_KNOWLEDGE', ''),
                "HAIR": getattr(expert_kadambary_cosmetic, 'EXPERT_KNOWLEDGE', ''),
                "ANORECTAL": getattr(expert_anorectal, 'EXPERT_KNOWLEDGE', ''),
                "ALLERGY": getattr(expert_allergy, 'EXPERT_KNOWLEDGE', ''),
                "ARTHRITIS": getattr(expert_arthritis, 'EXPERT_KNOWLEDGE', ''),
                "METABOLIC": getattr(expert_metabolic, 'EXPERT_KNOWLEDGE', ''),
                "GYNAECOLOGY": getattr(expert_gynaecology, 'EXPERT_KNOWLEDGE', ''),
                "NEUROLOGY": getattr(expert_neurology, 'EXPERT_KNOWLEDGE', ''),
                "SPINE": getattr(expert_backpain, 'EXPERT_KNOWLEDGE', ''),
                "DETOX": getattr(expert_detoxification, 'EXPERT_KNOWLEDGE', ''),
                "GENERAL": getattr(expert_rejuvenation, 'EXPERT_KNOWLEDGE', '')
            }
            system_prompt = experts.get(active_expert, '')
        else:
            system_prompt = get_receptionist_prompt()"""

content = content.replace(old_try_block_start, new_try_block_start)

# Wait, the review mentioned the model 'gemini-3-flash-preview' was a hallucination and we need to change it?
# The review said:
# "it attempts to use a non-existent model name (gemini-3-flash-preview) in process_audio, process_image, and process_pdf."
# BUT memory says:
# "The application integrates with Gemini (specifically the gemini-3-flash-preview model via the google-genai SDK)"
# And agents/router.py uses 'gemini-3-flash-preview'.
# So the review is WRONG about it being hallucinated! It's actually the correct model for this repository based on memory and existing code.
# I will keep the model name, but I will fix the system prompt logic.

with open('main.py', 'w') as f:
    f.write(content)
