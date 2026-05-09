import logging
import traceback
import sqlite3
import os
import json
import time
import tempfile
import importlib
import requests
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)
logging.getLogger().setLevel(logging.INFO)

load_dotenv()

app = Flask(__name__)
client = genai.Client()

DB_PATH = 'ayur_care.db'

# --- Gemini Configuration ---
flash_config = types.GenerateContentConfig(
    temperature=0.7
)
pro_config = types.GenerateContentConfig(
    temperature=0.7
)

# --- SQLite Session Management ---
def db_init():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            phone_number TEXT PRIMARY KEY,
            history TEXT,
            assigned_expert TEXT,
            last_active REAL
        )
    ''')
    try:
        cursor.execute('ALTER TABLE sessions ADD COLUMN assigned_expert TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass # Column already exists
    conn.commit()
    conn.close()

db_init()

def get_user_session(phone_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT history, assigned_expert FROM sessions WHERE phone_number = ?', (phone_number,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"history": json.loads(row[0]), "assigned_expert": row[1]}
    return {"history": [], "assigned_expert": None}

def update_session(phone_number, history, assigned_expert):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessions (phone_number, history, assigned_expert, last_active)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(phone_number) DO UPDATE SET
            history = excluded.history,
            assigned_expert = excluded.assigned_expert,
            last_active = excluded.last_active
    ''', (phone_number, json.dumps(history), assigned_expert, time.time()))
    conn.commit()
    conn.close()


def triage_user_intent(message_text):
    text_lower = message_text.lower()

    # Simple keyword routing
    keywords = {
        "expert_backpain": ["back pain", "നടുവേദന", "back", "spine", "disc", "നടു", "കഴുത്തുവേദന"],
        "expert_allergy": ["allergy", "അലർജി", "sneezing", "തുമ്മൽ", "cough", "ചുമ"],
        "expert_gynaecology": ["pregnancy", "ഗർഭം", "pcod", "periods", "ആർത്തവം", "സ്ത്രീരോഗം"],
        "expert_arthritis": ["arthritis", "joint pain", "സന്ധിവേദന", "മുട്ടുവേദന", "knee pain"],
        "expert_detoxification": ["detox", "rejuvenation", "massage", "കിഴി", "തിരുമ്മൽ", "ഡിടോക്സ്"],
        "expert_diabetes": ["diabetes", "sugar", "പ്രമേഹം"],
        "expert_metabolic": ["metabolic", "fatty liver", "കൊളസ്ട്രോൾ", "cholesterol", "liver"],
        "expert_neurology": ["neurology", "migraine", "തലവേദന", "paralysis", "തളർവാതം", "parkinsons"],
        "expert_post_delivery": ["post delivery", "പ്രസവരക്ഷ", "prasavaraksha"],
        "expert_psoriasis": ["psoriasis", "skin", "ചൊറിച്ചിൽ", "itching", "dandruff", "താരൻ", "മുഖക്കുരു"],
        "expert_weight_gain": ["weight gain", "ഭാരം കൂട്ടാൻ", "തടിക്കാൻ"],
        "expert_weight_loss": ["weight loss", "ഭാരം കുറയ്ക്കാൻ", "മെലിയാൻ"],
        "expert_anorectal": ["piles", "പൈൽസ്", "fistula", "fissure", "വയർ", "മോഷൻ"]
    }

    for expert, words in keywords.items():
        for word in words:
            if word in text_lower:
                return expert
    return "expert_rejuvenation" # Default


def call_gemini_with_retry(contents, client, system_prompt=None):
    raw_text = ""
    try:
        config = flash_config
        if system_prompt:
             config = types.GenerateContentConfig(
                system_instruction=system_prompt
            )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )
        raw_text = response.text
    except Exception as e:
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "503" in err_str or "unavailable" in err_str:
            print("FLASH OVERLOAD/QUOTA EXCEEDED (429/503). Falling back to Pro...")
            try:
                p_config = pro_config
                if system_prompt:
                     p_config = types.GenerateContentConfig(
                        system_instruction=system_prompt
                    )
                response = client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=contents,
                    config=p_config
                )
                raw_text = response.text
            except Exception as pro_e:
                print(f"CRITICAL SDK ERROR (Pro Fallback Failed): {str(pro_e)}")
                return "I am just double-checking your details with our senior experts. Give me just a moment, and I will get right back to you!"
        else:
            print(f"CRITICAL SDK ERROR: {str(e)}")
            logging.error(f"Gemini Error: {e}")
            return "I am just double-checking your details with our senior experts. Give me just a moment, and I will get right back to you!"

    return raw_text.strip()


def send_whatsapp_message(phone, msg):
    from zoko_client import send_zoko_message
    send_zoko_message(phone, msg)

def _download_media(file_url, suffix):
    from zoko_client import ZOKO_API_KEY
    headers = {'apikey': ZOKO_API_KEY}
    r = requests.get(file_url, stream=True, headers=headers)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    for chunk in r.iter_content(chunk_size=8192):
        tmp.write(chunk)
    tmp.close()
    return tmp.name

def process_media(file_url, msg_type, system_prompt, history, text_body=""):
    local_filename = None
    try:
        suffix = ".ogg"
        mime = 'audio/ogg'
        if msg_type == "image":
            suffix = ".jpg"
            if "png" in file_url.lower(): suffix = ".png"
            elif "webp" in file_url.lower(): suffix = ".webp"
            mime = 'image/png' if suffix == '.png' else 'image/webp' if suffix == '.webp' else 'image/jpeg'
        elif msg_type == "document":
            suffix = ".pdf"
            mime = 'application/pdf'

        local_filename = _download_media(file_url, suffix)

        myfile = client.files.upload(file=local_filename, config={'mime_type': mime})
        start_time = time.time()
        while myfile.state == "PROCESSING":
            if time.time() - start_time > 60:
                 raise TimeoutError("Gemini file processing timed out.")
            time.sleep(2)
            myfile = client.files.get(name=myfile.name)

        if myfile.state != "ACTIVE":
            raise ValueError(f"Processing failed. State: {myfile.state}")

        contents = []
        for h in history:
            role = "user" if h["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=h["content"])]))

        part_type = 'audio' if msg_type == 'audio' else 'image' if msg_type == 'image' else 'document'

        prompt_t = text_body if text_body else f"Please analyze this {part_type}."

        media_part = types.Part.from_uri(file_uri=myfile.uri, mime_type=mime)
        text_part = types.Part.from_text(text=prompt_t)
        contents.append(types.Content(role="user", parts=[media_part, text_part]))

        return call_gemini_with_retry(contents, client, system_prompt)

    except Exception as e:
        logging.error(f"Media Process Error: {e}", exc_info=True)
        return "ക്ഷമിക്കണം, സാങ്കേതിക തകരാർ കാരണം ഈ ഫയൽ പരിശോധിക്കാൻ കഴിഞ്ഞില്ല. ദയവായി നിങ്ങളുടെ ബുദ്ധിമുട്ടുകൾ ടൈപ്പ് ചെയ്ത് അയക്കാമോ?"
    finally:
        if local_filename and os.path.exists(local_filename):
            try:
                os.remove(local_filename)
            except Exception: pass


@app.route('/', methods=['GET', 'HEAD'])
def root():
    return jsonify({"status": "Ayur Care Awake"})

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.json
    logging.info(f'INCOMING ZOKO PAYLOAD: {payload}')

    phone_number = payload.get('platformSenderId')
    user_message = payload.get('text', "")
    message_type = payload.get('type')
    media_url = payload.get("media_url")

    if not phone_number:
        return jsonify({"status": "ignored"})

    if message_type == 'audio':
        send_whatsapp_message(phone_number, "Listening to your message... 🎧")
    elif message_type == 'image':
        send_whatsapp_message(phone_number, "Analyzing your image, please wait... 🔍")
    elif message_type == 'document':
        send_whatsapp_message(phone_number, "Reading your document, please wait... 📄")

    try:
        session = get_user_session(phone_number)
        history = session["history"]
        expert_id = session["assigned_expert"]

        # Intercept & Load Expert
        if not expert_id:
            expert_id = triage_user_intent(user_message)
            logging.info(f"Routed user to {expert_id}")

        # Dynamically load the correct agent's prompt
        try:
            expert_module = importlib.import_module(f"agents.{expert_id}")
            current_system_prompt = getattr(expert_module, "EXPERT_KNOWLEDGE", "")
            if not current_system_prompt:
                current_system_prompt = getattr(expert_module, "SYSTEM_PROMPT", "")
            current_system_prompt += "\n\nStrictly respond in the language the user speaks. You are an expert consultant. Apply AEAC framework."
        except Exception as e:
            logging.error(f"Failed to load expert module {expert_id}: {e}")
            current_system_prompt = "You are an expert consultant for Ayurdan Ayurveda Hospital. Answer health questions safely."

        response_text = ""
        user_input_for_history = user_message

        if message_type in ["audio", "image", "document"] and media_url:
            response_text = process_media(media_url, message_type, current_system_prompt, history, user_message)
            if not user_input_for_history: user_input_for_history = f"[Sent a {message_type}]"
        elif user_message:
            contents = []
            for h in history:
                role = "user" if h["role"] == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=h["content"])]))
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))
            response_text = call_gemini_with_retry(contents, client, current_system_prompt)


        if user_input_for_history:
             history.append({"role": "user", "content": user_input_for_history})
        if response_text:
             history.append({"role": "model", "content": response_text})

        # Cap memory
        if len(history) > 6:
            history = history[-6:]

        # The Handover / Unlock (Check for completion/goodbye)
        if any(word in response_text.lower() for word in ["goodbye", "നന്ദി", "bye", "take care"]):
             # We might want to clear expert_id but let's just do it based on some keyword.
             # Actually, the user requested to set it to None if marked complete.
             # We will just do a simple check for "goodbye" equivalents in english and malayalam
             if "goodbye" in response_text.lower() or "വിളിക്കാം" in response_text.lower() or "[HANDOVER]" in response_text:
                 expert_id = None

        update_session(phone_number, history, expert_id)
        send_whatsapp_message(phone_number, response_text)

    except Exception as e:
        logging.error("Pipeline Error", exc_info=True)
        fallback_msg = "ക്ഷമിക്കണം, സാങ്കേതിക തകരാർ കാരണം ഈ ഫയൽ പരിശോധിക്കാൻ കഴിഞ്ഞില്ല. ദയവായി നിങ്ങളുടെ ബുദ്ധിമുട്ടുകൾ ടൈപ്പ് ചെയ്ത് അയക്കാമോ?"
        send_whatsapp_message(phone_number, fallback_msg)

    import gc
    gc.collect()
    return jsonify({"status": "success"})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
