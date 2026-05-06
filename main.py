import logging
import traceback
logging.basicConfig(level=logging.INFO)
from fastapi import FastAPI, Request, BackgroundTasks
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

    try:
        response = requests.get(file_url, headers=headers)
        logging.info(f"Audio Download HTTP Status: {response.status_code}")
        response.raise_for_status()
        logging.info("Checkpoint 2: Download successful (Audio)")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
            temp_audio.write(response.content)
            temp_audio_path = temp_audio.name

        try:
            logging.info("Checkpoint 3: Gemini File API upload started (Audio)")
            uploaded_file = client.files.upload(file=temp_audio_path, mime_type='audio/ogg')
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

        finally:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

    except Exception as e:
        print(f"Audio processing error: {e}")
        return "I'm sorry, I couldn't hear that clearly. Could you please type your message?"


def process_image(file_url, caption, history_text, system_prompt):
    logging.info("Checkpoint 1: Media detected in webhook (Image)")
    zoko_api_key = os.environ.get("ZOKO_API_KEY")
    headers = {"apikey": zoko_api_key} if zoko_api_key else {}

    # Detect extension
    ext = ".jpg"
    if ".png" in file_url.lower(): ext = ".png"
    elif ".webp" in file_url.lower(): ext = ".webp"

    try:
        response = requests.get(file_url, headers=headers)
        logging.info(f"Image Download HTTP Status: {response.status_code}")
        response.raise_for_status()
        logging.info("Checkpoint 2: Download successful (Image)")

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_img:
            temp_img.write(response.content)
            temp_img_path = temp_img.name

        try:
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

        finally:
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)

    except Exception as e:
        print(f"Image processing error: {e}")
        return "I'm sorry, I couldn't analyze the image properly. Could you please describe it?"


def process_pdf(file_url, history_text, system_prompt):
    logging.info("Checkpoint 1: Media detected in webhook (PDF)")
    zoko_api_key = os.environ.get("ZOKO_API_KEY")
    headers = {"apikey": zoko_api_key} if zoko_api_key else {}

    try:
        response = requests.get(file_url, headers=headers)
        logging.info(f"PDF Download HTTP Status: {response.status_code}")
        response.raise_for_status()
        logging.info("Checkpoint 2: Download successful (PDF)")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(response.content)
            temp_pdf_path = temp_pdf.name

        try:
            logging.info("Checkpoint 3: Gemini File API upload started (PDF)")
            uploaded_file = client.files.upload(file=temp_pdf_path, mime_type='application/pdf')
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

        finally:
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    except Exception as e:
        print(f"PDF processing error: {e}")
        return "I received your document, but I am unable to read its contents. Could you please send it as a clear image or type out the details?"

app = FastAPI()




@app.api_route('/', methods=['GET', 'HEAD'])
def root():
    return {"status": "Ayur Care Awake"}

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
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
        background_tasks.add_task(send_zoko_message, phone_number, "Listening... 🎧")
    elif message_type == 'image':
        background_tasks.add_task(send_zoko_message, phone_number, "Analyzing your image... 👁️")
    elif message_type == 'document':
        background_tasks.add_task(send_zoko_message, phone_number, "Reading your document... 📄")

    if not user_message and not media_url and not media_id:
        return {"status": "ignored, missing data"}

    parts = []

    try:
        # Retrieve context
        history_text, state_notes = get_context(phone_number)

        loop = asyncio.get_event_loop()

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
            from agents import expert_backpain, expert_post_delivery, expert_psoriasis, expert_kadambary_cosmetic, expert_anorectal, expert_allergy, expert_arthritis, expert_metabolic, expert_gynaecology, expert_neurology, expert_detoxification, expert_rejuvenation
            experts = {
                "BACKPAIN": getattr(expert_backpain, 'EXPERT_KNOWLEDGE', ''),
                "POST_DELIVERY": getattr(expert_post_delivery, 'EXPERT_KNOWLEDGE', ''),
                "PSORIASIS": getattr(expert_psoriasis, 'EXPERT_KNOWLEDGE', ''),
                "HAIR": getattr(expert_kadambary_cosmetic, 'EXPERT_KNOWLEDGE', ''),
                "ANORECTAL": getattr(expert_anorectal, 'EXPERT_KNOWLEDGE', ''),
                "ALLERGY": getattr(expert_allergy, 'EXPERT_KNOWLEDGE', ''),
                "ARTHRITIS": getattr(expert_arthritis, 'EXPERT_KNOWLEDGE', ''),
                "METABOLIC": getattr(expert_metabolic, 'EXPERT_KNOWLEDGE', ''),
                "GYNAECOLOGY": getattr(expert_gynaecology, 'EXPERT_KNOWLEDGE', ''),
                "NEUROLOGY": getattr(expert_neurology, 'EXPERT_KNOWLEDGE', ''),
                "SPINE": getattr(expert_backpain, 'EXPERT_KNOWLEDGE', ''),
                "DETOX": getattr(expert_detoxification, 'EXPERT_KNOWLEDGE', ''),
                "GENERAL": getattr(expert_rejuvenation, 'EXPERT_KNOWLEDGE', '')
            }
            system_prompt = experts.get(active_expert, '')
        else:
            system_prompt = get_receptionist_prompt()

        if message_type == "audio" and media_url:
            response_text = await loop.run_in_executor(
                None, process_audio, media_url, history_text, system_prompt
            )
            user_message = "[Sent an audio message]"
        elif message_type == "image" and media_url:
            response_text = await loop.run_in_executor(
                None, process_image, media_url, user_message, history_text, system_prompt
            )
            user_message = "[Sent an image]"
        elif message_type == "document" and media_url and media_url.endswith(".pdf"):
            response_text = await loop.run_in_executor(
                None, process_pdf, media_url, history_text, system_prompt
            )
            user_message = "[Sent a PDF document]"
        else:
            response_text = await loop.run_in_executor(
                None,
                get_expert_response,
                phone_number,
                user_message,
                [], # Empty parts since we handle files monolithically now
                history_text,
                state_notes
            )

    except Exception as e:
        logging.error("Pipeline Error", exc_info=True)
        fallback_msg = "ക്ഷമിക്കണം, സാങ്കേതിക തകരാർ കാരണം ഈ ഫയൽ പരിശോധിക്കാൻ കഴിഞ്ഞില്ല. ദയവായി നിങ്ങളുടെ ബുദ്ധിമുട്ടുകൾ ടൈപ്പ് ചെയ്ത് അയക്കാമോ?"
        background_tasks.add_task(send_zoko_message, phone_number, fallback_msg)
        return {"status": "success"}



    # Save the interaction to update history and patient state
    add_interaction(phone_number, user_message, response_text)

    # Use background tasks to prevent waiting on outgoing I/O for webhook ack
    background_tasks.add_task(send_zoko_message, phone_number, response_text)
    background_tasks.add_task(clean_expired_sessions)

    gc.collect()
    return {"status": "success"}
