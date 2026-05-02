from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
import requests
import gc
from google.genai import types

from agents.router import classify_intent
from agents import (
    expert_backpain,
    expert_psoriasis,
    expert_anorectal,
    expert_post_delivery,
    expert_rejuvenation,
    expert_weight,
    expert_hair,
    expert_kadambary,
    expert_diabetes
)
import memory_manager

app = FastAPI()

class WebhookRequest(BaseModel):
    user_id: Optional[str] = "default_user" # Added to support memory manager
    message: Optional[str] = ""
    media_url: Optional[str] = None
    mime_type: Optional[str] = None

EXPERT_MAP = {
    "BACK_PAIN": expert_backpain.generate_response,
    "PSORIASIS": expert_psoriasis.generate_response,
    "ANORECTAL": expert_anorectal.generate_response,
    "POST_DELIVERY": expert_post_delivery.generate_response,
    "REJUVENATION": expert_rejuvenation.generate_response,
    "WEIGHT_MGT": expert_weight.generate_response,
    "HAIR_CARE": expert_hair.generate_response,
    "KADAMBARY_COSMETIC": expert_kadambary.generate_response,
    "DIABETES": expert_diabetes.generate_response
}

@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"status": "Ayur Care Server Awake"}

@app.post("/webhook")
def webhook(request: WebhookRequest):
    contents = []

    if request.message:
        contents.append(request.message)

    if request.media_url and request.mime_type:
        try:
            # Download the media
            media_response = requests.get(request.media_url, timeout=10)
            if media_response.status_code == 200:
                media_part = types.Part.from_bytes(data=media_response.content, mime_type=request.mime_type)
                contents.append(media_part)
        except Exception as e:
            print(f"Error downloading media: {e}")

    if not contents:
        return {"error": "No message or media provided"}

    # Build complete contents payload including history
    user_id = request.user_id
    history = memory_manager.get_history(user_id)

    full_payload = []
    for hist_msg in history:
        full_payload.append(hist_msg['text'])

    # Add current message
    full_payload.extend(contents)

    intent = classify_intent(full_payload)

    if intent in EXPERT_MAP:
        response_text = EXPERT_MAP[intent](full_payload)
    else:
        # Default or GENERAL_INQUIRY fallback
        response_text = "Thank you for reaching out to Ayurdan Ayurveda Hospital. How can we assist you today?"

    # Store interaction in memory
    memory_manager.add_message(user_id, {"role": "user", "text": request.message or "[Media Payload]"})
    memory_manager.add_message(user_id, {"role": "model", "text": response_text})

    # Aggressive Python Garbage Collection to prevent OOM
    gc.collect()

    return {
        "intent": intent,
        "response": response_text
    }
