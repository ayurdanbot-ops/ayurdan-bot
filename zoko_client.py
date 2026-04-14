import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_zoko_message(phone_number: str, text: str):
    zoko_api_key = os.getenv("ZOKO_API_KEY")
    if not zoko_api_key:
        print("ZOKO_API_KEY not found in environment variables.")
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
        return True
    except Exception as e:
        print(f"Failed to send Zoko message: {e}")
        return False
