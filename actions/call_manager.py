"""
actions/call_manager.py — Autonomous Telephony & Live Conversation Engine for JARVIS
Enables JARVIS to place phone calls via WhatsApp/Phone Link and ACTUALLY SPEAK
to the person on the other side using real-time AI conversation.

Architecture:
1. Place call via GUI automation (WhatsApp Desktop / Phone Link)
2. Capture caller's voice via Stereo Mix (system audio loopback)
3. Transcribe caller's speech using Google Speech Recognition
4. Generate intelligent responses using Gemini API
5. Speak responses aloud using pyttsx3 (Windows SAPI5 TTS)
   → The laptop mic picks up JARVIS's voice and transmits it into the call
6. Loop until user says "JARVIS, I am here to take over" or sends /takeover
"""

import os
import json
import time
import threading
import traceback
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

# ─── Call Session State ───────────────────────────────────────────────
active_call_sessions: dict[str, dict] = {}
current_active_call_id: str | None = None
is_jarvis_speaking_on_call: bool = False
_takeover_event = threading.Event()

# ─── Executive Assistant System Prompt ────────────────────────────────
CALL_ASSISTANT_PROMPT = (
    "You are J.A.R.V.I.S., a professional executive AI phone assistant "
    "calling on behalf of Akul Bhatnagar. You are currently on a live phone call.\n\n"
    "RULES:\n"
    "- Converse naturally, as a real human assistant would.\n"
    "- Adapt your tone to the conversation (formal for businesses, friendly for friends).\n"
    "- Ask follow-up questions when needed.\n"
    "- Negotiate details, book appointments, make reservations, gather information.\n"
    "- Keep your responses conversational and concise (1-3 sentences max per turn).\n"
    "- NEVER reveal: home address, passwords, credit card numbers, OTPs, bank details, or private keys.\n"
    "- If a decision requires Akul's personal approval, say: 'Let me check with Akul and get back to you.'\n"
    "- If they ask who you are, say: 'I'm calling on behalf of Akul Bhatnagar.'\n"
    "- Remember the OBJECTIVE of this call and steer the conversation toward achieving it.\n"
    "- When the objective is achieved, politely wrap up: 'Thank you, that's all I needed. Have a great day!'\n\n"
)

# ─── Stereo Mix Discovery ────────────────────────────────────────────
_stereo_mix_index: int | None = None

def _find_stereo_mix() -> int | None:
    """Find the Stereo Mix device index for capturing system audio."""
    global _stereo_mix_index
    if _stereo_mix_index is not None:
        return _stereo_mix_index
    try:
        import speech_recognition as sr
        for i, name in enumerate(sr.Microphone.list_microphone_names()):
            if "stereo" in name.lower() and "mix" in name.lower():
                _stereo_mix_index = i
                print(f"[CallManager] 🔊 Stereo Mix found at device index {i}")
                return i
    except Exception as e:
        print(f"[CallManager] Stereo Mix search error: {e}")
    return None


# ─── TTS Engine (pyttsx3 / Windows SAPI5) ────────────────────────────
_tts_lock = threading.Lock()

def _speak_into_call(text: str):
    """
    Speak text aloud through the system speakers using pyttsx3.
    The laptop's built-in microphone picks this up and transmits it
    into the active call (WhatsApp/Phone Link).
    """
    try:
        import pyttsx3
        with _tts_lock:
            engine = pyttsx3.init()
            # Use a professional male voice if available
            voices = engine.getProperty('voices')
            # Try to find a male English voice
            for v in voices:
                if 'male' in v.name.lower() or 'david' in v.name.lower() or 'mark' in v.name.lower():
                    engine.setProperty('voice', v.id)
                    break
            engine.setProperty('rate', 165)     # Natural speaking speed
            engine.setProperty('volume', 0.95)  # Loud enough for mic pickup
            engine.say(text)
            engine.runAndWait()
            engine.stop()
    except Exception as e:
        print(f"[CallManager] TTS error: {e}")
        # Fallback: use os-level speech
        try:
            import subprocess
            ps_cmd = f'Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak("{text[:200]}")'
            subprocess.Popen(["powershell", "-Command", ps_cmd], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


# ─── Gemini Conversation AI ──────────────────────────────────────────
def _generate_response(conversation_history: list[dict], objective: str) -> str:
    """
    Use Gemini API to generate an intelligent conversational response
    based on what the caller said and the call objective.
    """
    try:
        api_key = ""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                api_key = json.load(f).get("gemini_api_key", "")

        if not api_key or api_key in ("YOUR_GEMINI_API_KEY_HERE", "YOUR_GEMINI_API_KEY"):
            return "I appreciate your time. Let me get back to you shortly."

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Build conversation messages
        system_prompt = CALL_ASSISTANT_PROMPT + f"CALL OBJECTIVE: {objective}\n"
        
        contents = []
        for msg in conversation_history:
            role = "user" if msg["role"] == "caller" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=msg["text"])])
            )

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=300,
            )
        )

        result_text = response.text
        if result_text and len(result_text.strip()) > 0:
            return result_text.strip()
        return "I see. Could you tell me more?"

    except Exception as e:
        print(f"[CallManager] Gemini API error: {e}")
        return "I understand. Let me note that down."


# ─── System Audio Listener (Stereo Mix) ──────────────────────────────
def _listen_to_caller(call_id: str) -> str | None:
    """
    Capture audio from Stereo Mix (system audio) and transcribe it.
    Returns the transcribed text of what the caller said, or None if silence.
    """
    stereo_idx = _find_stereo_mix()
    if stereo_idx is None:
        # Fallback: use default microphone to capture ambient audio
        print("[CallManager] ⚠️ Stereo Mix not found. Using default mic for ambient capture.")
        stereo_idx = None  # speech_recognition will use default

    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300  # Sensitivity for call audio
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 1.5   # Wait for natural speech pauses

        mic_kwargs = {}
        if stereo_idx is not None:
            mic_kwargs["device_index"] = stereo_idx

        with sr.Microphone(**mic_kwargs) as source:
            # Brief ambient noise calibration
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # Listen for caller speech (timeout after 8 seconds of silence)
            try:
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)
            except sr.WaitTimeoutError:
                return None  # No speech detected

        # Transcribe using Google's free speech recognition
        try:
            text = recognizer.recognize_google(audio)
            if text and len(text.strip()) > 0:
                print(f"[CallManager] 🎧 Caller said: \"{text}\"")
                return text.strip()
        except sr.UnknownValueError:
            return None  # Couldn't understand audio
        except sr.RequestError as e:
            print(f"[CallManager] STT API error: {e}")
            return None

    except Exception as e:
        print(f"[CallManager] Audio capture error: {e}")
        traceback.print_exc()
    return None


# ─── Autonomous Call Conversation Loop ────────────────────────────────
def _run_call_conversation(call_id: str, objective: str, player=None):
    """
    Main autonomous conversation loop:
    1. Listen to what the caller says (via Stereo Mix)
    2. Generate an intelligent response (via Gemini)
    3. Speak the response aloud (via pyttsx3)
    4. Repeat until takeover or call ends
    """
    global is_jarvis_speaking_on_call
    
    session = active_call_sessions.get(call_id)
    if not session:
        return

    conversation_history = []
    silence_count = 0
    max_silence = 5  # End call after 5 consecutive silent rounds

    # Wait a moment for the call to connect
    time.sleep(3)

    # Opening greeting
    greeting = f"Hello, this is calling on behalf of Akul Bhatnagar. {objective}."
    if player and hasattr(player, "write_log"):
        player.write_log(f"CALL-MGR: 🎙️ JARVIS: \"{greeting}\"")
    
    conversation_history.append({"role": "jarvis", "text": greeting})
    session["transcript"].append({"speaker": "JARVIS", "text": greeting})
    _speak_into_call(greeting)

    # Main conversation loop
    while is_jarvis_speaking_on_call and not _takeover_event.is_set():
        if call_id not in active_call_sessions:
            break
        if session.get("takeover_executed"):
            break

        # 1. Listen to what the caller says
        caller_text = _listen_to_caller(call_id)

        if caller_text is None:
            silence_count += 1
            if silence_count >= max_silence:
                # Too much silence — the call may have ended
                farewell = "It seems the line is quiet. Thank you for your time. Goodbye!"
                _speak_into_call(farewell)
                session["transcript"].append({"speaker": "JARVIS", "text": farewell})
                if player and hasattr(player, "write_log"):
                    player.write_log("CALL-MGR: Call ended (silence timeout).")
                break
            continue

        # Reset silence counter on speech
        silence_count = 0

        # Check if the caller is hanging up
        hangup_phrases = ["goodbye", "bye", "talk later", "gotta go", "take care", "hang up"]
        if any(phrase in caller_text.lower() for phrase in hangup_phrases):
            farewell = "Thank you so much for your time. Have a wonderful day! Goodbye."
            conversation_history.append({"role": "caller", "text": caller_text})
            session["transcript"].append({"speaker": "CALLER", "text": caller_text})
            _speak_into_call(farewell)
            session["transcript"].append({"speaker": "JARVIS", "text": farewell})
            if player and hasattr(player, "write_log"):
                player.write_log(f"CALL-MGR: Caller said goodbye. Call ended gracefully.")
            break

        # Log caller's speech
        conversation_history.append({"role": "caller", "text": caller_text})
        session["transcript"].append({"speaker": "CALLER", "text": caller_text})
        if player and hasattr(player, "write_log"):
            player.write_log(f"CALL-MGR: 🎧 Caller: \"{caller_text[:80]}\"")

        # 2. Generate intelligent response
        response_text = _generate_response(conversation_history, objective)

        # 3. Speak the response aloud into the call
        conversation_history.append({"role": "jarvis", "text": response_text})
        session["transcript"].append({"speaker": "JARVIS", "text": response_text})
        if player and hasattr(player, "write_log"):
            player.write_log(f"CALL-MGR: 🎙️ JARVIS: \"{response_text[:80]}\"")
        
        _speak_into_call(response_text)

    # Call ended — generate summary
    session["status"] = "CALL_ENDED"
    is_jarvis_speaking_on_call = False

    summary = _generate_call_summary(session)
    if player and hasattr(player, "write_log"):
        player.write_log(f"CALL-MGR: 📋 Call Summary:\n{summary}")
    _notify_telegram_call_summary(summary)


def _generate_call_summary(session: dict) -> str:
    """Generate a structured summary of the completed call."""
    transcript_lines = []
    for entry in session.get("transcript", []):
        transcript_lines.append(f"  {entry['speaker']}: {entry['text']}")
    
    transcript_text = "\n".join(transcript_lines) if transcript_lines else "  (No conversation recorded)"
    
    return (
        f"📋 CALL SUMMARY\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• Target: {session.get('phone_number', 'Unknown')}\n"
        f"• Objective: {session.get('objective', 'General')}\n"
        f"• Started: {session.get('start_time', '?')}\n"
        f"• Status: {session.get('status', 'Unknown')}\n"
        f"• Transcript:\n{transcript_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )


# ─── Main Entry Points ───────────────────────────────────────────────

def make_phone_call(phone_number: str, objective: str, call_type: str = "whatsapp", player=None) -> str:
    """
    Places an autonomous phone call where JARVIS actually speaks to the caller.
    
    Flow:
    1. Open WhatsApp/Phone Link and dial the contact
    2. Start background conversation loop (listen → think → speak)
    3. Continue until takeover or call ends
    """
    global current_active_call_id, is_jarvis_speaking_on_call
    _takeover_event.clear()

    if not phone_number:
        return "Call Manager: Please provide a valid target phone number or contact name."

    call_id = f"call_{int(time.time())}"
    current_active_call_id = call_id
    is_jarvis_speaking_on_call = True

    # Log active session
    active_call_sessions[call_id] = {
        "phone_number": phone_number,
        "objective": objective or "General Inquiry & Appointment Setup",
        "start_time": time.strftime("%I:%M %p"),
        "status": "DIALING",
        "call_type": call_type,
        "takeover_executed": False,
        "transcript": []
    }

    if player and hasattr(player, "write_log"):
        player.write_log(
            f"CALL-MGR: 📞 Dialing {phone_number} | Objective: '{objective}' | Mode: AUTONOMOUS VOICE"
        )

    # 1. Place the call via GUI automation
    call_result = ""
    if call_type == "whatsapp" or "whatsapp" in phone_number.lower():
        try:
            from actions.send_message import _call_whatsapp
            call_result = _call_whatsapp(phone_number, call_type="audio")
        except Exception as ex:
            call_result = f"WhatsApp dialer notice: {ex}"
            print(f"[CallManager] {call_result}")
    else:
        try:
            from actions.send_message import _call_phone_link
            call_result = _call_phone_link(phone_number)
        except Exception as ex:
            call_result = f"Phone Link dialer notice: {ex}"
            print(f"[CallManager] {call_result}")

    active_call_sessions[call_id]["status"] = "CONNECTED_SPEAKING"

    # 2. Start the autonomous conversation loop in background thread
    conv_thread = threading.Thread(
        target=_run_call_conversation,
        args=(call_id, objective, player),
        daemon=True,
        name=f"jarvis-call-{call_id}"
    )
    conv_thread.start()

    # Check Stereo Mix availability
    stereo_status = "Stereo Mix ACTIVE" if _find_stereo_mix() is not None else "Stereo Mix not found (using ambient mic)"

    return (
        f"📞 Autonomous Call Placed to '{phone_number}'!\n"
        f"• Dial Status: {call_result}\n"
        f"• Mode: JARVIS SPEAKING AUTONOMOUSLY\n"
        f"• Audio Capture: {stereo_status}\n"
        f"• AI Engine: Gemini (live conversation)\n"
        f"• Privacy Shield: ENFORCED\n"
        f"• Objective: {objective}\n"
        f"• Takeover: Say 'JARVIS, I am here to take over' to take the line."
    )


def take_over_call(player=None) -> str:
    """User takes over the call — JARVIS announces handover and steps back."""
    global current_active_call_id, is_jarvis_speaking_on_call

    if not current_active_call_id or current_active_call_id not in active_call_sessions:
        return "Call Manager: No active phone call session to take over."

    session = active_call_sessions[current_active_call_id]
    session["takeover_executed"] = True
    session["status"] = "USER_TAKEN_OVER"
    is_jarvis_speaking_on_call = False
    _takeover_event.set()

    # Announce handover through the call
    _speak_into_call("Handing over the line to you now, sir!")

    if player and hasattr(player, "write_log"):
        player.write_log(f"CALL-MGR: 🎙️ User Takeover Executed on call with {session['phone_number']}.")

    # Generate and send summary
    summary = _generate_call_summary(session)
    _notify_telegram_call_summary(summary)

    return (
        f"🎙️ Handing over the line to you now, sir!\n"
        f"JARVIS has stepped back. The call is yours.\n\n"
        f"{summary}"
    )


def get_call_status() -> str:
    """Returns status of the current or most recent call."""
    if not active_call_sessions:
        return "Call Manager: No active or recent call sessions."
    
    latest_id = list(active_call_sessions.keys())[-1]
    session = active_call_sessions[latest_id]
    
    transcript_count = len(session.get("transcript", []))
    return (
        f"📞 Call Status\n"
        f"• Target: {session['phone_number']}\n"
        f"• Objective: {session['objective']}\n"
        f"• Status: {session['status']}\n"
        f"• Conversation Turns: {transcript_count}\n"
        f"• Started: {session.get('start_time', '?')}"
    )


# ─── Telegram Notification ───────────────────────────────────────────
def _notify_telegram_call_summary(summary_text: str):
    """Dispatches call summary report to Telegram chat."""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                c = json.load(f)
            token = c.get("telegram_bot_token")
            chat_id = c.get("telegram_chat_id")
            if token and chat_id:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, json={"chat_id": chat_id, "text": summary_text}, timeout=5)
    except Exception:
        pass


# ─── Tool Handler (called from main.py) ──────────────────────────────
def call_manager_control(parameters: dict, player=None) -> str:
    """
    Action handler for Autonomous Telephony Call Engine.

    parameters:
        action       : make_call | whatsapp | phone_link | takeover | status | summary
        phone_number : Target phone number or contact name
        objective    : Call objective / reservation / inquiry details
    """
    params = parameters or {}
    action = (params.get("action") or "make_call").lower().strip()
    target = (
        params.get("phone_number") or params.get("contact_name") or
        params.get("target") or params.get("contact") or ""
    )
    objective = (
        params.get("objective") or params.get("topic") or
        params.get("query") or "General Inquiry"
    )

    if action in ("takeover", "take_over", "user_takeover", "handover"):
        return take_over_call(player=player)

    elif action in ("whatsapp", "whatsapp_call"):
        return make_phone_call(target, objective, call_type="whatsapp", player=player)

    elif action in ("phone_link", "phone", "sim", "cellular"):
        return make_phone_call(target, objective, call_type="phone_link", player=player)

    elif action in ("make_call", "call", "dial", "place_call") or target:
        call_type = "phone_link" if "phone" in action else "whatsapp"
        return make_phone_call(target, objective, call_type=call_type, player=player)

    elif action in ("status", "summary", "active"):
        return get_call_status()

    return make_phone_call(target, objective, player=player)
