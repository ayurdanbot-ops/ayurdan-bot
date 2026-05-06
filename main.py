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

SECURE_CACHE_DIR = '/tmp/bot_media_cache/'
os.makedirs(SECURE_CACHE_DIR, exist_ok=True)


def wait_for_file_processing(file_obj, timeout=60):
    start_time = time.time()
    while file_obj.state == "PROCESSING":
        if time.time() - start_time > timeout:
            raise TimeoutError("File processing timeout")
        time.sleep(2)
        file_obj = client.files.get(name=file_obj.name)

    if file_obj.state != "ACTIVE":
        raise ValueError(f"File processing failed: {file_obj.state}")

    return file_obj


def process_audio(file_url, history_text, system_prompt):
    logging.info("Checkpoint 1: Media detected in webhook (Audio)")
    zoko_api_key = os.environ.get("ZOKO_API_KEY")
    headers = {"apikey": zoko_api_key} if zoko_api_key else {}

    temp_audio_path = None
    try:
        with requests.get(file_url, headers=headers, timeout=15, stream=True) as response:
            logging.info(f"Audio Download HTTP Status: {response.status_code}")
            response.raise_for_status()
            logging.info("Checkpoint 2: Download successful (Audio)")

            with tempfile.NamedTemporaryFile(dir=SECURE_CACHE_DIR, delete=False, suffix=".ogg") as temp_audio:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_audio.write(chunk)
            temp_audio_path = temp_audio.name

        logging.info("Checkpoint 3: Gemini File API upload started (Audio)")
        uploaded_file = client.files.upload(file=temp_audio_path, config={'mime_type': 'audio/ogg'})
        uploaded_file = wait_for_file_processing(uploaded_file)

        contents = []
        if system_prompt:
            contents.append(system_prompt)
        if history_text:
            contents.append(f"Chat History:\n{history_text}")
        contents.append("Please analyze this audio message and respond.")
        contents.append(uploaded_file)

        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=contents
        )
        return response.text.strip()

    except Exception as e:
        print(f"Audio processing error: {e}")
        return "I'm sorry, I couldn't hear that clearly. Could you please type your message?"
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            logging.info(f"Deleted cached audio file: {temp_audio_path}")


def process_image(file_url, caption, history_text, system_prompt):
    logging.info("Checkpoint 1: Media detected in webhook (Image)")
    zoko_api_key = os.environ.get("ZOKO_API_KEY")
    headers = {"apikey": zoko_api_key} if zoko_api_key else {}

    # Detect extension
    ext = ".jpg"
    if ".png" in file_url.lower(): ext = ".png"
    elif ".webp" in file_url.lower(): ext = ".webp"

    temp_img_path = None
    try:
        with requests.get(file_url, headers=headers, timeout=15, stream=True) as response:
            logging.info(f"Image Download HTTP Status: {response.status_code}")
            response.raise_for_status()
            logging.info("Checkpoint 2: Download successful (Image)")

            with tempfile.NamedTemporaryFile(dir=SECURE_CACHE_DIR, delete=False, suffix=ext) as temp_img:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_img.write(chunk)
            temp_img_path = temp_img.name

        logging.info("Checkpoint 3: Gemini File API upload started (Image)")
        uploaded_file = client.files.upload(file=temp_img_path)
        uploaded_file = wait_for_file_processing(uploaded_file)

        contents = []
        if system_prompt:
            contents.append(system_prompt)
        if history_text:
            contents.append(f"Chat History:\n{history_text}")

        instruction = "Look at this image and analyze it regarding the user's health query"
        if caption:
            instruction += f"\nUser Caption: {caption}"

        contents.append(instruction)
        contents.append(uploaded_file)

        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=contents
        )
        return response.text.strip()

    except Exception as e:
        print(f"Image processing error: {e}")
        return "I'm sorry, I couldn't analyze the image properly. Could you please describe it?"
    finally:
        if temp_img_path and os.path.exists(temp_img_path):
            os.remove(temp_img_path)
            logging.info(f"Deleted cached image file: {temp_img_path}")


def process_pdf(file_url, history_text, system_prompt):
    logging.info("Checkpoint 1: Media detected in webhook (PDF)")
    zoko_api_key = os.environ.get("ZOKO_API_KEY")
    headers = {"apikey": zoko_api_key} if zoko_api_key else {}

    temp_pdf_path = None
    try:
        with requests.get(file_url, headers=headers, timeout=15, stream=True) as response:
            logging.info(f"PDF Download HTTP Status: {response.status_code}")
            response.raise_for_status()
            logging.info("Checkpoint 2: Download successful (PDF)")

            with tempfile.NamedTemporaryFile(dir=SECURE_CACHE_DIR, delete=False, suffix=".pdf") as temp_pdf:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name

        logging.info("Checkpoint 3: Gemini File API upload started (PDF)")
        uploaded_file = client.files.upload(file=temp_pdf_path, config={'mime_type': 'application/pdf'})
        uploaded_file = wait_for_file_processing(uploaded_file)

        contents = []
        if system_prompt:
            contents.append(system_prompt)
        if history_text:
            contents.append(f"Chat History:\n{history_text}")

        contents.append("The user uploaded a medical document. Please analyze the findings and respond as an expert.")
        contents.append(uploaded_file)

        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=contents
        )
        return response.text.strip()

    except Exception as e:
        print(f"PDF processing error: {e}")
        return "I received your document, but I am unable to read its contents. Could you please send it as a clear image or type out the details?"
    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            logging.info(f"Deleted cached PDF file: {temp_pdf_path}")

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
        # Retrieve context
        history_text, state_notes = get_context(phone_number)


        from agents.router import get_receptionist_prompt
        from memory_manager import get_active_expert

        active_expert = get_active_expert(phone_number)

        system_prompt = None
        if active_expert:
            # We can't easily dynamically pull the exact expert prompt without modifying their code.
            # But the requirement states: "Send the file to Gemini along with conversation history and system prompt."
            # Since the user specifically requested not to touch expert files, we will try to pass a generic or receptionist prompt,
            # actually wait, let's just pass the receptionist prompt if no expert.
            # If there IS an expert, maybe we should construct a generic system prompt for the MoE routing handoff.
            # Or we can just import the expert module and try to get its prompt? No, they use EXPERT_KNOWLEDGE constant.
            # Use a safe fallback for the active expert prompt instead of hardcoded imports to prevent ModuleNotFoundError
            # Since we only get routing tags, we can rely on a generalized medical prompt if we can't safely extract EXPERT_KNOWLEDGE.
            # To adhere to the "Zero Touch" mandate, we will just use a generic Ayurvedic knowledge prompt for media.
            system_prompt = "You are an expert Ayurvedic doctor at Ayurdan Ayurveda Hospital. You evaluate media accurately and safely."
        else:
            system_prompt = get_receptionist_prompt()

        if message_type == "audio" and media_url:
            response_text = process_audio(media_url, history_text, system_prompt)
            user_message = "[Sent an audio message]"
        elif message_type == "image" and media_url:
            response_text = process_image(media_url, user_message, history_text, system_prompt)
            user_message = "[Sent an image]"
        elif message_type == "document" and media_url and media_url.lower().endswith(".pdf"):
            response_text = process_pdf(media_url, history_text, system_prompt)
            user_message = "[Sent a PDF document]"
        else:
            response_text = get_expert_response(
                phone_number,
                user_message,
                [],
                history_text,
                state_notes
            )

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
