import os
import requests

def download_whatsapp_media(media_id: str) -> bytes:
    token = os.environ.get("WHATSAPP_BEARER_TOKEN")
    if not token:
        print("Warning: WHATSAPP_BEARER_TOKEN is not set.")
        raise Exception("Missing WHATSAPP_BEARER_TOKEN")

    # Step 1: Get media URL
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    media_url = response.json().get("url")
    if not media_url:
        raise Exception("Media URL not found in Graph API response")

    # Step 2: Download actual bytes
    media_response = requests.get(media_url, headers=headers)
    media_response.raise_for_status()

    return media_response.content
