import os
import requests

ZOKO_API_KEY = os.environ.get("ZOKO_API_KEY")

def send_message(phone_number: str, text: str):
    # Placeholder for Zoko API integration
    print(f"Sending via Zoko to {phone_number}: {text}")
    return True
