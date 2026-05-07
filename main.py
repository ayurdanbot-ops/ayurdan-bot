import logging
import traceback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)
logging.getLogger().setLevel(logging.INFO)
from fastapi import FastAPI, Request
import requests
from google.genai import types
import os

import tempfile
import time
from google import genai

from dotenv import load_dotenv
import asyncio
import gc

from agents.router import get_expert_response
from zoko_client import send_zoko_message
from memory_manager import get_context, add_interaction, clean_expired_sessions
from media_downloader import download_whatsapp_media

load_dotenv()


client = genai.Client()


# Gemini 3 Flash Primary Config
flash_config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(
        thinking_level="minimal",
        include_thoughts=False
    )
)

# Gemini 2.5 Pro Fallback Config
pro_config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(
        include_thoughts=False,
        thinking_budget=1024
    )
)

def call_gemini_with_retry(contents, client):
    raw_text = ""
    try:
        # 1. Attempt with Primary Model (Stable Flash)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=flash_config
        )
        raw_text = response.text
    except Exception as e:
        err_str = str(e).lower()
        # 2. Handle Quota (429) OR Server Overload (503) via Fallback to Pro
        if "429" in err_str or "quota" in err_str or "503" in err_str or "unavailable" in err_str:
            print("FLASH OVERLOAD/QUOTA EXCEEDED (429/503). Falling back to Pro...")
            try:
                # Nested fallback to Pro
                response = client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=contents,
                    config=pro_config
                )
                raw_text = response.text
            except Exception as pro_e:
                print(f"CRITICAL SDK ERROR (Pro Fallback Failed): {str(pro_e)}")
                return "I am just double-checking your details with our senior experts. Give me just a moment, and I will get right back to you!"
        else:
            # 3. Handle Other Errors immediately
            print(f"CRITICAL SDK ERROR: {str(e)}")
            logging.error(f"Gemini Error: {e}")
            return "I am just double-checking your details with our senior experts. Give me just a moment, and I will get right back to you!"

    return raw_text.strip()


from media_handlers import process_audio, process_image, process_pdf

app = FastAPI()




@app.api_route('/', methods=['GET', 'HEAD'])
def root():
    return {"status": "Ayur Care Awake"}

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    logging.info(f'INCOMING ZOKO PAYLOAD: {payload}')

    phone_number = payload.get('platformSenderId')
    user_message = payload.get('text')
    message_type = payload.get('type')

    if not phone_number:
        return {"status": "ignored, missing phone number"}

    media_id = payload.get("media_id")
    media_url = payload.get("media_url")
    media_mime_type = payload.get("media_mime_type")

    if message_type == 'audio':
        send_zoko_message(phone_number, "Listening to your message... 🎧")
    elif message_type == 'image':
        send_zoko_message(phone_number, "Analyzing your image, please wait... 🔍")
    elif message_type == 'document':
        send_zoko_message(phone_number, "Reading your document, please wait... 📄")

    if not user_message and not media_url and not media_id:
        return {"status": "ignored, missing data"}

    parts = []

    try:
        from memory_manager import get_context, hash_user_id, chat_history
        from agents.router import get_receptionist_prompt, get_expert_response
        from memory_manager import get_active_expert

        history_text, state_notes = get_context(phone_number)

        # Prepare variables for the exact conditional block provided by the user
        msg_type = message_type
        file_url = media_url
        sender_phone = phone_number
        text_body = user_message

        hashed_id = hash_user_id(phone_number)
        raw_history = chat_history.get(hashed_id, [])
        # Format the history to match the expected format for `media_handlers.py`
        # h["parts"][0] and h["role"] -> "user"/"model"
        history = [{"role": h["role"], "parts": [h["content"]]} for h in raw_history]

        user_input_for_history = ""

        def send_whatsapp_message(phone, msg, type):
            send_zoko_message("+" + phone, msg)

        def get_ai_response(sender, text, hist):
            history_text, state_notes = get_context("+" + sender)
            return get_expert_response("+" + sender, text, [], history_text, state_notes)

        # Image, Audio, PDF vs Text Logic
        if msg_type == "document" and file_url and file_url.lower().endswith(".pdf"):
            send_whatsapp_message(sender_phone.replace("+", ""), "Reading your document... 📄", "text")
            response_text = process_pdf(file_url, sender_phone, history)
            if not user_input_for_history: user_input_for_history = "[Sent a PDF document]"
        elif msg_type == "image" and file_url:
            send_whatsapp_message(sender_phone.replace("+", ""), "Analyzing your image... 👁️", "text")
            response_text = process_image(file_url, sender_phone, text_body, history)
            if not user_input_for_history: user_input_for_history = "[Sent an image]"
        elif msg_type == "audio" and file_url:
            send_whatsapp_message(sender_phone.replace("+", ""), "Listening... 🎧", "text")
            response_text = process_audio(file_url, sender_phone, history)
            if not user_input_for_history: user_input_for_history = "[Sent an audio message]"
        elif text_body or msg_type == "text":
            response_text = get_ai_response(sender_phone, text_body, history)

        if user_input_for_history:
            user_message = user_input_for_history

    except Exception as e:
        logging.error("Pipeline Error", exc_info=True)
        fallback_msg = "ക്ഷമിക്കണം, സാങ്കേതിക തകരാർ കാരണം ഈ ഫയൽ പരിശോധിക്കാൻ കഴിഞ്ഞില്ല. ദയവായി നിങ്ങളുടെ ബുദ്ധിമുട്ടുകൾ ടൈപ്പ് ചെയ്ത് അയക്കാമോ?"
        send_zoko_message(phone_number, fallback_msg)
        return {"status": "success"}



    # Save the interaction to update history and patient state
    add_interaction(phone_number, user_message, response_text)

    # Use background tasks to prevent waiting on outgoing I/O for webhook ack
    send_zoko_message(phone_number, response_text)
    clean_expired_sessions()

    gc.collect()
    return {"status": "success"}
