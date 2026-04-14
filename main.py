from fastapi import FastAPI, Request
import requests
from google.genai import types
import os
from dotenv import load_dotenv
import asyncio

from router import get_expert_response

load_dotenv()

app = FastAPI()

@app.api_route('/', methods=['GET', 'HEAD'])
async def root():
    return {"status": "Ayur Care Awake"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    text = data.get("text", "")
    media_url = data.get("media_url")
    media_mime_type = data.get("media_mime_type")

    parts = []

    if media_url and media_mime_type:
        try:
            # Running sync request in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, requests.get, media_url)
            response.raise_for_status()
            parts.append(
                types.Part.from_bytes(
                    data=response.content,
                    mime_type=media_mime_type
                )
            )
        except Exception as e:
            print(f"Failed to download media from {media_url}: {e}")

    # Running the routing logic and gemini generation in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    response_text = await loop.run_in_executor(None, get_expert_response, text, parts)

    return {"response": response_text}
