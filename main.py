from fastapi import FastAPI, Request, BackgroundTasks
import requests
from google.genai import types
import os
from dotenv import load_dotenv
import asyncio

from agents.router import get_expert_response
from zoko_client import send_zoko_message

load_dotenv()

app = FastAPI()

@app.api_route('/', methods=['GET', 'HEAD'])
def root():
    return {"status": "Ayur Care Awake"}

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    # Simple Zoko payload extraction logic
    # Assuming zoko sends standard webhook structure like { "message": { "text": "hello", "sender": "123" } }
    # Or based on instruction 'extract phone number and message/media'.

    phone_number = data.get("sender") or data.get("phone") or data.get("recipient")

    # Try to find message details
    text = data.get("text", "")
    media_url = data.get("media_url")
    media_mime_type = data.get("media_mime_type")

    # If the payload is nested like Zoko's typically are
    if "message" in data and isinstance(data["message"], dict):
        text = text or data["message"].get("text", "")
        media_url = media_url or data["message"].get("url")
        media_mime_type = media_mime_type or data["message"].get("mimeType")
        phone_number = phone_number or data.get("sender")

    if not phone_number:
        # Just return early if it's a test payload or missing required data to reply
        return {"status": "ignored", "reason": "no phone number provided"}

    parts = []

    if media_url:
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, requests.get, media_url)
            response.raise_for_status()

            # Default to jpeg if mime type isn't present to satisfy types.Part
            mime = media_mime_type or "image/jpeg"

            parts.append(
                types.Part.from_bytes(
                    data=response.content,
                    mime_type=mime
                )
            )
        except Exception as e:
            print(f"Failed to download media from {media_url}: {e}")

    # Running the routing logic and gemini generation in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    response_text = await loop.run_in_executor(None, get_expert_response, text, parts)

    # Use background tasks to prevent waiting on outgoing I/O for webhook ack
    background_tasks.add_task(send_zoko_message, phone_number, response_text)

    return {"status": "success"}
