import logging
import traceback
import sqlite3
import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
import time
import tempfile
import importlib
import requests
from flask import Flask, request, jsonify
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)
logging.getLogger().setLevel(logging.INFO)

load_dotenv()

ZOKO_API_KEY = os.environ.get("ZOKO_API_KEY")

import datetime
from zoneinfo import ZoneInfo


def get_ist_current_time_str() -> str:
    tz = ZoneInfo("Asia/Kolkata")
    return datetime.datetime.now(tz).strftime("%I:%M %p")

def get_ist_time_greeting() -> str:
    tz = ZoneInfo("Asia/Kolkata")
    current_time = datetime.datetime.now(tz)
    hour = current_time.hour
    if 0 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 16:
        return "Good afternoon"
    else:
        return "Good evening"

app = Flask(__name__)

# Initialize Vertex AI
vertexai.init(
    project=os.environ.get("GCP_PROJECT_ID"),
    location="global"
)

model = GenerativeModel("gemini-3.5-flash")

DB_PATH = 'ayur_care.db'

class ProcessedMessagesCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity

    def contains(self, message_id):
        if not message_id:
            return False
        if message_id in self.cache:
            self.cache.move_to_end(message_id)
            return True
        return False

    def add(self, message_id):
        if not message_id:
            return
        self.cache[message_id] = True
        self.cache.move_to_end(message_id)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

processed_messages = ProcessedMessagesCache(1000)
# Webhook Blacklist for spammers
BLACKLIST = {"+919539854269", "919539854269"}


# Global executor for background tasks
executor = ThreadPoolExecutor(max_workers=4)

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
        pass
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
    return "expert_rejuvenation"

def call_gemini_with_retry(contents, system_prompt=None):
    max_retries = 5
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            if system_prompt:
                dynamic_model = GenerativeModel("gemini-3.5-flash", system_instruction=system_prompt)
            else:
                dynamic_model = model

            response = dynamic_model.generate_content(contents)
            return response.text.strip()
        except ResourceExhausted:
            if attempt < max_retries - 1:
                logging.warning(f"Quota exceeded. Retrying in {retry_delay}s... (Attempt {attempt + 1})")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                return ""
        except Exception as e:
            logging.error(f"Vertex AI Error: {e}")
            return ""


def send_whatsapp_message(phone, msg):
    from zoko_client import send_zoko_message
    send_zoko_message(phone, msg)

def _download_media(file_url, suffix):
    headers = {'apikey': ZOKO_API_KEY}
    r = requests.get(file_url, stream=True, headers=headers)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    for chunk in r.iter_content(chunk_size=8192):
        tmp.write(chunk)
    tmp.close()
    return tmp.name

def process_media(file_url, msg_type, system_prompt, history_text, expert_id, text_body=""):
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

        with open(local_filename, "rb") as f:
            raw_media_bytes = f.read()

        media_part = Part.from_data(data=raw_media_bytes, mime_type=mime)

        contents = []
        if history_text:
            contents.append(f"Chat History:\n{history_text}")

        part_type = 'audio' if msg_type == 'audio' else 'image' if msg_type == 'image' else 'document'
        prompt_t = text_body if text_body else f"Please analyze this {part_type}."

        contents.append(media_part)
        contents.append(prompt_t)

        return call_gemini_with_retry(contents, system_prompt)

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
    if not payload:
        return "OK", 200

    sender_id = payload.get("platformSenderId", "")
    if sender_id in BLACKLIST:
        logging.info(f"Blacklisted sender blocked: {sender_id}")
        return "OK", 200
    msg_id = payload.get('id')
    if msg_id and processed_messages.contains(msg_id):
        logging.info(f"Duplicate message ignored: {msg_id}")
        return "OK", 200
    if msg_id:
        processed_messages.add(msg_id)
    executor.submit(handle_message, payload)
    return "OK", 200

def handle_message(payload):
    logging.info(f'INCOMING ZOKO PAYLOAD: {payload}')
    phone_number = payload.get('platformSenderId')
    user_message = payload.get('text', "")
    message_type = payload.get('type')
    media_url = payload.get("fileUrl")

    if not phone_number:
        return

    if message_type == 'audio':
        pass
    elif message_type == 'image':
        pass
    elif message_type == 'document':
        pass

    try:
        session = get_user_session(phone_number)
        history = session["history"]
        expert_id = session["assigned_expert"]

        history_text = "\n".join([f"{'User' if h['role'] == 'user' else 'AI'}: {h['content']}" for h in history])

        if not expert_id:
            expert_id = triage_user_intent(user_message)
            logging.info(f"Routed user to {expert_id}")

        from system_prompt import SYSTEM_PROMPT as BASE_SYSTEM_PROMPT
        try:
            expert_module = importlib.import_module(f"agents.{expert_id}")
            expert_knowledge = getattr(expert_module, "EXPERT_KNOWLEDGE", "")
            hospital_info = getattr(expert_module, "GLOBAL_HOSPITAL_INFO", "")
        except ImportError:
            logging.error(f"Failed to load expert module: {expert_id}")
            expert_knowledge = ""
            hospital_info = ""

        current_system_prompt = f"{BASE_SYSTEM_PROMPT}\n\n*SPECIFIC EXPERT KNOWLEDGE*\n{expert_knowledge}\n\n*HOSPITAL INFO*\n{hospital_info}"
        fresh_greeting = get_ist_time_greeting()
        current_system_prompt = current_system_prompt.replace("{DYNAMIC_GREETING}", fresh_greeting)
        current_time_str = get_ist_current_time_str()
        current_system_prompt = current_system_prompt.replace("{CURRENT_TIME}", current_time_str)

        response_text = ""
        user_input_for_history = user_message

        if message_type in ["audio", "image", "document"] and media_url:
            response_text = process_media(media_url, message_type, current_system_prompt, history_text, expert_id, user_message)
            if not user_input_for_history: user_input_for_history = f"[Sent a {message_type}]"
        elif user_message:
            contents = []
            if history_text:
                contents.append(f"Chat History:\n{history_text}")
            contents.append(f"Current User Input: {user_message}")
            response_text = call_gemini_with_retry(contents, current_system_prompt)

        if user_input_for_history:
             history.append({"role": "user", "content": user_input_for_history})
        if response_text:
             history.append({"role": "model", "content": response_text})

        if len(history) > 20:
            history = history[-20:]

        if any(word in response_text.lower() for word in ["goodbye", "നന്ദി", "bye", "take care"]):
             if "goodbye" in response_text.lower() or "വിളിക്കാം" in response_text.lower() or "[HANDOVER]" in response_text:
                 expert_id = None

        update_session(phone_number, history, expert_id)
        if response_text and isinstance(response_text, str) and response_text.strip():
            send_whatsapp_message(phone_number, response_text.strip())

    except Exception as e:
        logging.error("Pipeline Error", exc_info=True)
        fallback_msg = "ക്ഷമിക്കണം, സാങ്കേതിക തകരാർ കാരണം ഈ ഫയൽ പരിശോധിക്കാൻ കഴിഞ്ഞില്ല. ദയവായി നിങ്ങളുടെ ബുദ്ധിമുട്ടുകൾ ടൈപ്പ് ചെയ്ത് അയക്കാമോ?"
        send_whatsapp_message(phone_number, fallback_msg)

    import gc
    gc.collect()
    return

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
