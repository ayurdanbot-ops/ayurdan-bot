import os
import tempfile
import aiohttp
import aiofiles
import aiofiles.tempfile
from google.genai import types
import time
import logging


ZOKO_API_KEY = os.environ.get("ZOKO_API_KEY")
SYSTEM_PROMPT = "You are an expert Ayurvedic doctor at Ayurdan Ayurveda Hospital."
GEMINI_PROCESSING_TIMEOUT = 60

def get_ist_time_greeting():
    return "Hello"

def get_current_time_str():
    return "12:00 PM"

def detect_language(text):
    return "malayalam"

def filter_system_prompt_by_language(prompt, lang):
    return prompt

def _check_reload_prompt():
    pass

import asyncio


async def process_media_async_core(file_url, sender_phone, prompt_text, history, msg_type):
    logging.info(f"DEBUG: Entered process_media_async_core function for {msg_type}")
    local_filename = None
    headers = {'apikey': ZOKO_API_KEY}
    from main import call_gemini_with_retry_async, client
    try:
        logging.info(f"Downloading {msg_type}: {file_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url, headers=headers) as r:
                r.raise_for_status()

                ext = ".tmp"
                mime = "application/octet-stream"
                if msg_type == "audio":
                    ext = ".ogg"
                    mime = "audio/ogg"
                elif msg_type == "image":
                    ext = ".jpg"
                    mime = "image/jpeg"
                    if "png" in file_url.lower():
                        ext = ".png"
                        mime = "image/png"
                    elif "webp" in file_url.lower():
                        ext = ".webp"
                        mime = "image/webp"
                elif msg_type == "document":
                    ext = ".pdf"
                    mime = "application/pdf"

                async with aiofiles.tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    async for chunk in r.content.iter_chunked(8192):
                        await tmp.write(chunk)
                    local_filename = tmp.name

        logging.info(f"Uploading {msg_type} to Gemini...")
        try:
            myfile = await client.aio.files.upload(file=local_filename, config={'mime_type': mime})
            start_time = time.time()
            while myfile.state == "PROCESSING":
                if time.time() - start_time > GEMINI_PROCESSING_TIMEOUT:
                     raise TimeoutError("Gemini file processing timed out.")
                await asyncio.sleep(2)
                myfile = await client.aio.files.get(name=myfile.name)

            if myfile.state != "ACTIVE":
                raise ValueError(f"Media processing failed or incomplete. State: {myfile.state}")

            greeting = get_ist_time_greeting()
            current_time_str = get_current_time_str()

            user_lang = "malayalam"
            if history:
                for h in reversed(history):
                    if h["role"] == "user":
                        user_lang = detect_language(h["parts"][0])
                        if user_lang == "malayalam":
                            break

            _check_reload_prompt()
            system_instruction = filter_system_prompt_by_language(SYSTEM_PROMPT, user_lang)
            contents = [
                types.Content(role="user", parts=[types.Part.from_text(text=system_instruction)]),
                types.Content(role="model", parts=[types.Part.from_text(text=f"Understood. I am AIVA. Current Time Greeting is: {greeting}.")]),
            ]

            for h in history:
                role = "user" if h["role"] == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=h["parts"][0])]))

            media_part = types.Part.from_uri(file_uri=myfile.uri, mime_type=mime)

            if msg_type == "audio":
                text_part = types.Part.from_text(text=f"Listen to this audio. You are AIVA. Current time in Kerala is {current_time_str}. Answer as a consultant.")
            elif msg_type == "image":
                user_prompt = prompt_text if prompt_text else "Please analyze this image regarding my health."
                text_part = types.Part.from_text(text=f"Look at this image. Current time in Kerala is {current_time_str}. User says: {user_prompt}. Apply the Universal Language Protocol and answer as an expert.")
            elif msg_type == "document":
                text_part = types.Part.from_text(text=f"The user uploaded a medical document. Current time in Kerala is {current_time_str}. Please analyze the findings and respond as an expert.")

            contents.append(types.Content(role="user", parts=[media_part, text_part]))

            return await call_gemini_with_retry_async(contents, client)

        except Exception as e:
            logging.error(f"Gemini {msg_type} API Error: {e}")
            if msg_type == "audio": return "I'm sorry, I couldn't hear that clearly. Could you please type your message?"
            if msg_type == "image": return "I'm sorry, I couldn't analyze the image properly. Could you please describe it?"
            if msg_type == "document": return "I received your document, but I am unable to read its contents. Could you please send it as a clear image or type out the details?"

    except Exception as e:
        logging.error(f"{msg_type} Download/Process Error: {e}")
        if msg_type == "audio": return "I'm sorry, I couldn't hear that clearly. Could you please type your message?"
        if msg_type == "image": return "I'm sorry, I couldn't download the image. Could you please try again?"
        if msg_type == "document": return "I received your document, but I am unable to read its contents. Could you please send it as a clear image or type out the details?"
    finally:
        if local_filename and os.path.exists(local_filename):
            try:
                await asyncio.to_thread(os.remove, local_filename)
                logging.info(f"Cleaned up temp file: {local_filename}")
            except Exception as e:
                logging.error(f"Failed to cleanup temp file: {e}")

async def handle_media_async(file_url, sender_phone, prompt_text, history, msg_type):
    return await process_media_async_core(file_url, sender_phone, prompt_text, history, msg_type)
