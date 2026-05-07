import os
import tempfile
import requests
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

def process_audio(file_url, sender_phone, history):
    local_filename = None
    headers = {'apikey': ZOKO_API_KEY}
    from main import call_gemini_with_retry, client
    try:
        logging.info(f"Downloading Audio: {file_url}")
        with requests.get(file_url, stream=True, headers=headers) as r:
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
                for chunk in r.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                local_filename = tmp.name

        logging.info("Uploading Audio to Gemini...")
        try:
            myfile = client.files.upload(file=local_filename, config={'mime_type': 'audio/ogg'})
            start_time = time.time()
            while myfile.state == "PROCESSING":
                if time.time() - start_time > GEMINI_PROCESSING_TIMEOUT:
                     raise TimeoutError("Gemini file processing timed out.")
                time.sleep(2)
                myfile = client.files.get(name=myfile.name)

            if myfile.state != "ACTIVE":
                raise ValueError(f"Audio processing failed or incomplete. State: {myfile.state}")

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

            audio_part = types.Part.from_uri(file_uri=myfile.uri, mime_type='audio/ogg')
            text_part = types.Part.from_text(text=f"Listen to this audio. You are AIVA. Current time in Kerala is {current_time_str}. Answer as a consultant.")
            contents.append(types.Content(role="user", parts=[audio_part, text_part]))

            return call_gemini_with_retry(contents, client)

        except Exception as e:
            logging.error(f"Gemini Audio API Error: {e}")
            return "I'm sorry, I couldn't hear that clearly. Could you please type your message?"

    except Exception as e:
        logging.error(f"Audio Download/Process Error: {e}")
        return "I'm sorry, I couldn't hear that clearly. Could you please type your message?"
    finally:
        if local_filename and os.path.exists(local_filename):
            try:
                os.remove(local_filename)
                logging.info(f"Cleaned up temp file: {local_filename}")
            except Exception as e:
                logging.error(f"Failed to cleanup temp file: {e}")

def process_image(file_url, sender_phone, prompt_text, history):
    local_filename = None
    headers = {'apikey': ZOKO_API_KEY}
    from main import call_gemini_with_retry, client
    try:
        logging.info(f"Downloading Image: {file_url}")
        with requests.get(file_url, stream=True, headers=headers) as r:
            r.raise_for_status()
            ext = ".jpg"
            if "png" in file_url.lower(): ext = ".png"
            elif "webp" in file_url.lower(): ext = ".webp"
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                for chunk in r.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                local_filename = tmp.name

        logging.info("Uploading Image to Gemini...")
        try:
            myfile = client.files.upload(file=local_filename)
            start_time = time.time()
            while myfile.state == "PROCESSING":
                if time.time() - start_time > GEMINI_PROCESSING_TIMEOUT:
                     raise TimeoutError("Gemini file processing timed out.")
                time.sleep(2)
                myfile = client.files.get(name=myfile.name)

            if myfile.state != "ACTIVE":
                raise ValueError(f"Image processing failed or incomplete. State: {myfile.state}")

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

            user_prompt = prompt_text if prompt_text else "Please analyze this image regarding my health."
            image_part = types.Part.from_uri(file_uri=myfile.uri, mime_type='image/jpeg')
            text_part = types.Part.from_text(text=f"Look at this image. Current time in Kerala is {current_time_str}. User says: {user_prompt}. Apply the Universal Language Protocol and answer as an expert.")
            contents.append(types.Content(role="user", parts=[image_part, text_part]))

            return call_gemini_with_retry(contents, client)

        except Exception as e:
            logging.error(f"Gemini Image API Error: {e}")
            return "I'm sorry, I couldn't analyze the image properly. Could you please describe it?"

    except Exception as e:
        logging.error(f"Image Download/Process Error: {e}")
        return "I'm sorry, I couldn't download the image. Could you please try again?"
    finally:
        if local_filename and os.path.exists(local_filename):
            try:
                os.remove(local_filename)
            except Exception: pass

def process_pdf(file_url, sender_phone, history):
    local_filename = None
    headers = {'apikey': ZOKO_API_KEY}
    from main import call_gemini_with_retry, client
    try:
        logging.info(f"Downloading PDF: {file_url}")
        with requests.get(file_url, stream=True, headers=headers) as r:
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                for chunk in r.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                local_filename = tmp.name

        logging.info("Uploading PDF to Gemini...")
        try:
            myfile = client.files.upload(file=local_filename)
            start_time = time.time()
            while myfile.state == "PROCESSING":
                if time.time() - start_time > GEMINI_PROCESSING_TIMEOUT:
                     raise TimeoutError("Gemini file processing timed out.")
                time.sleep(2)
                myfile = client.files.get(name=myfile.name)

            if myfile.state != "ACTIVE":
                raise ValueError(f"PDF processing failed or incomplete. State: {myfile.state}")

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

            pdf_part = types.Part.from_uri(file_uri=myfile.uri, mime_type='application/pdf')
            text_part = types.Part.from_text(text=f"The user uploaded a medical document. Current time in Kerala is {current_time_str}. Please analyze the findings and respond as an expert.")
            contents.append(types.Content(role="user", parts=[pdf_part, text_part]))

            return call_gemini_with_retry(contents, client)

        except Exception as e:
            logging.error(f"Gemini PDF API Error: {e}")
            return "I received your document, but I am unable to read its contents. Could you please send it as a clear image or type out the details?"

    except Exception as e:
        logging.error(f"PDF Download/Process Error: {e}")
        return "I received your document, but I am unable to read its contents. Could you please send it as a clear image or type out the details?"
    finally:
        if local_filename and os.path.exists(local_filename):
            try:
                os.remove(local_filename)
            except Exception: pass
