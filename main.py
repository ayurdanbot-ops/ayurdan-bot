from fastapi import FastAPI, Request, BackgroundTasks
import requests
from google.genai import types
import os
from dotenv import load_dotenv
import asyncio
import gc

from agents.router import get_expert_response
from zoko_client import send_zoko_message
from memory_manager import get_context, add_interaction, clean_expired_sessions

load_dotenv()

app = FastAPI()

@app.api_route('/', methods=['GET', 'HEAD'])
def root():
    return {"status": "Ayur Care Awake"}

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    print(f'INCOMING ZOKO PAYLOAD: {payload}')

    phone_number = payload.get('platformSenderId')
    user_message = payload.get('text')

    if not phone_number or not user_message:
        return {"status": "ignored, missing data"}

    media_url = payload.get("media_url")
    media_mime_type = payload.get("media_mime_type")

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

    # Retrieve context
    history_text, state_notes = get_context(phone_number)

    # Running the routing logic and gemini generation in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()

    response_text = await loop.run_in_executor(
        None,
        get_expert_response,
        phone_number,
        user_message,
        parts,
        history_text,
        state_notes
    )

    # Save the interaction to update history and patient state
    add_interaction(phone_number, user_message, response_text)

    # Use background tasks to prevent waiting on outgoing I/O for webhook ack
    background_tasks.add_task(send_zoko_message, phone_number, response_text)
    background_tasks.add_task(clean_expired_sessions)

    gc.collect()
    return {"status": "success"}
