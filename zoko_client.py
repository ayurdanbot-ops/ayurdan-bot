import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_zoko_message(phone_number: str, text: str):
    zoko_api_key = os.environ.get("ZOKO_API_KEY")
    if not zoko_api_key:
        print("ZOKO_API_KEY configuration is missing.")
        return False

    url = "https://chat.zoko.io/v2/message"
    headers = {
        "apikey": zoko_api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "channel": "whatsapp",
        "recipient": phone_number,
        "type": "text",
        "message": text
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        # Removed detailed response logging to prevent exposing sensitive downstream context
        print("Successfully dispatched message via Zoko.")
        return True
    except requests.exceptions.RequestException:
        # Removed the error text and full exception logging to prevent header/payload leakage
        print("Failed to dispatch message via Zoko due to a network or validation error.")
        return False
