import re

with open('app.py', 'r') as f:
    content = f.read()

new_func = """def call_gemini_with_retry(contents, system_prompt=None):
    max_retries = 3
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            if system_prompt:
                dynamic_model = GenerativeModel("gemini-3-flash-preview", system_instruction=system_prompt)
            else:
                dynamic_model = model

            response = dynamic_model.generate_content(contents)
            return response.text.strip()
        except ResourceExhausted:
            if attempt < max_retries - 1:
                logging.warning(f"Quota exceeded. Retrying in {retry_delay}s... (Attempt {attempt + 1})")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                return "I am receiving too many requests right now. Please give me a moment and try asking again!"
        except Exception as e:
            logging.error(f"Vertex AI Error: {e}")
            return "I am just double-checking your details with our senior experts. Give me just a moment, and I will get right back to you!\""
"""

pattern = r"def call_gemini_with_retry\(contents, system_prompt=None\):.*?return \"I am just double-checking your details with our senior experts. Give me just a moment, and I will get right back to you!\""
content = re.sub(pattern, new_func, content, flags=re.DOTALL)

with open('app.py', 'w') as f:
    f.write(content)
