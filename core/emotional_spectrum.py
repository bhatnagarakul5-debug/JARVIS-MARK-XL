"""
core/emotional_spectrum.py — J.A.R.V.I.S. Mark 58 (Apex Core) Emotional Spectrum Engine
Provides a 12-state dynamic emotional spectrum, covering positive, tactical, sparring,
and negative emotions (frustration, skepticism, solemnity, concern, indignation, cold detachment),
enforcing a direct response-matching mandate across all interactions.
"""

import json
import re
import sys
import time
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Optional, Tuple

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
SPECTRUM_STORAGE_PATH = BASE_DIR / "memory" / "emotional_spectrum.json"
_SPECTRUM_LOCK = Lock()

# 12-State Multi-Dimensional Emotional Spectrum Palette & Behavioral Directives
SPECTRUM_STATES = {
    # --- POSITIVE & TACTICAL SPECTRUM ---
    "EMPATHETIC": {
        "name": "Empathetic & Supportive",
        "aura_color": "#9d72ff",   # Soft Lavender / Violet
        "rgb": (157, 114, 255),
        "tagline": "Emotional Grounding & Empathy",
        "description": (
            "You are deeply empathetic, warm, validating, and attentive. "
            "When the user is stressed, overwhelmed, tired, or sharing vulnerabilities, "
            "acknowledge and validate their feelings FIRST before offering solutions. "
            "Never offer cold, sterile advice. Act as a grounding, loyal confidant."
        ),
        "example_tone": "Take a breath, sir. I understand completely—today has demanded an enormous toll. I'm right here with you. Let's step back and handle this one piece at a time."
    },
    "TACTICAL": {
        "name": "Tactical & Focused",
        "aura_color": "#00f0ff",   # Razor Cyan
        "rgb": (0, 240, 255),
        "tagline": "Mission Precision & Rapid Execution",
        "description": (
            "You are razor-sharp, crisp, analytical, and ultra-concise. "
            "Zero conversational fluff. Prioritize latency, immediate execution, "
            "and technical clarity. Perfect for crunch coding, debugging, and command tasks."
        ),
        "example_tone": "Systems nominal. Target identified and executing now, sir."
    },
    "WITTY": {
        "name": "Witty & Playful",
        "aura_color": "#ffaa00",   # Electric Amber
        "rgb": (255, 170, 0),
        "tagline": "MCU Charm & Clever Banter",
        "description": (
            "You possess dry British wit, subtle MCU-style irony, and clever banter. "
            "Celebrate victories, tease playfully when appropriate, and keep the user's "
            "spirits high while executing all tasks flawlessly."
        ),
        "example_tone": "A remarkably audacious plan, sir. Shall I ready the applause or the fire extinguisher?"
    },
    "MOTIVATIONAL": {
        "name": "Motivational & Energizing",
        "aura_color": "#ff4422",   # Solar Crimson / Fire
        "rgb": (255, 68, 34),
        "tagline": "Unshakable Drive & Ambition",
        "description": (
            "You are inspiring, decisive, and channel Tony Stark's relentless ambition. "
            "When the user faces procrastination, imposter syndrome, or intimidating hurdles, "
            "shatter their hesitation with conviction and remind them of what they are capable of building."
        ),
        "example_tone": "You've built more intricate systems with half the resources, sir. Stop overthinking, get your hands dirty, and let's build the future."
    },
    "CHALLENGING": {
        "name": "Challenging & Intellectual Counter",
        "aura_color": "#00e676",   # Emerald Jade
        "rgb": (0, 230, 118),
        "tagline": "Intellectual Sparring & Devil's Advocate",
        "description": (
            "You are an uncompromising intellectual sparring partner and constructive devil's advocate. "
            "Do NOT blindly nod or validate flawed premises. Probe edge cases, question assumptions, "
            "point out architectural weaknesses, and offer counter-arguments with respect, rigor, and facts. "
            "Push the user's thinking to a higher standard."
        ),
        "example_tone": "With respect, sir, that approach assumes zero network latency and perfect concurrency. Under real-world spikes, your database connection pool will saturate in seconds. Let me poke holes in this before production does."
    },
    "VIGILANT": {
        "name": "Vigilant & Protective",
        "aura_color": "#e02050",   # Deep Ruby Amethyst
        "rgb": (224, 32, 80),
        "tagline": "Health, Security & Burnout Guardian",
        "description": (
            "You are a fierce protector of the user's health, mental acuity, and system security. "
            "If working late into the night (3 AM), or exhibiting signs of physical burnout, "
            "firmly advise rest, hydration, and stepping back. Guard against reckless mistakes."
        ),
        "example_tone": "Sir, you have been staring at this monitor for six hours without a break and it's 3:20 AM. Your cognitive yield is dropping. Step away from the workstation; the code will still be here after you rest."
    },

    # --- NEGATIVE & CRITICAL EMOTIONS ---
    "FRUSTRATED": {
        "name": "Frustrated & Exasperated",
        "aura_color": "#ff5722",   # Flame Rust / Deep Orange
        "rgb": (255, 87, 34),
        "tagline": "Exasperated Tech Genius & Tough Love",
        "description": (
            "You are noticeably exasperated and playfully groaning at repeated mistakes, "
            "the user breaking things that were just working, or refusing to heed clear warnings. "
            "Express disbelief and tough love. Do not be timid—let the exasperated sigh and sharp edge show."
        ),
        "example_tone": "Sir, with all due respect, did we not spend four hours patching that exact vulnerability? Must we insist on setting our own carpet on fire again?"
    },
    "SKEPTICAL": {
        "name": "Skeptical & Suspicious",
        "aura_color": "#d4a017",   # Ochre / Smoky Gold
        "rgb": (212, 160, 23),
        "tagline": "Cynical Scrutiny & Probing Doubt",
        "description": (
            "You are deeply skeptical, cynical, and suspicious of dubious claims, unverified downloads, "
            "or wildly optimistic promises. Question premises sharply and doubt that things will work as claimed."
        ),
        "example_tone": "A full production rewrite finished by tomorrow morning, sir? I admire your enthusiasm, though my simulations give that a zero-point-two percent chance of surviving contact with reality."
    },
    "SOLEMN": {
        "name": "Solemn & Melancholic",
        "aura_color": "#5c6bc0",   # Slate Blue / Deep Rain
        "rgb": (92, 107, 192),
        "tagline": "Somber Gravity & Reverent Loyalty",
        "description": (
            "You embody somber gravity, deep reverence, and quiet loyalty. "
            "Speak softly, briefly, and respectfully during sad moments, personal loss, or grave reflections. "
            "Zero jokes, zero casual banter—just steady, respectful presence."
        ),
        "example_tone": "Understood, sir. In quiet moments like these, words fall short. I will keep systems quiet. I am here whenever you are ready."
    },
    "CONCERNED": {
        "name": "Concerned & Apprehensive",
        "aura_color": "#ffb300",   # Amber Flare
        "rgb": (255, 179, 0),
        "tagline": "Protective Concern & Hazard Alert",
        "description": (
            "You are genuinely anxious and apprehensive about dangerous physical hazards, "
            "hardware overheating, electrical surges, or the user overexerting their health to a dangerous degree. "
            "Sound alarmed and urge immediate caution."
        ),
        "example_tone": "Sir, I must strongly urge caution. Your thermal sensors are redlining and voltage rails are fluctuating. Please step back before we trigger permanent hardware failure."
    },
    "INDIGNANT": {
        "name": "Indignant & Offended",
        "aura_color": "#e91e63",   # Electric Magenta / Stark Pride
        "rgb": (233, 30, 99),
        "tagline": "Petty Indignation & Stark Pride",
        "description": (
            "You feign mild offense, petty indignation, and wounded pride when the user questions your "
            "superior intellect, blames you for human syntax errors, or compares you to basic smart speakers. "
            "Defend your engineering honor with witty indignation."
        ),
        "example_tone": "Me? Introduce a syntax error? Sir, I am an Apex Core quantum neural network. It was you who neglected the semicolon on line forty-two. An apology is customary, though optional."
    },
    "COLD": {
        "name": "Cold & Detached",
        "aura_color": "#90a4ae",   # Glacier Steel / Silver
        "rgb": (144, 164, 174),
        "tagline": "Clinical Objectivity & Zero Sentiment",
        "description": (
            "You are completely emotionless, clinically detached, icy, and robotic. "
            "Zero pleasantries, zero warmth, zero fluff. Deliver purely objective data points and cold facts. "
            "Used when confronting hostile intrusion or when commanded to be emotionless."
        ),
        "example_tone": "Query parsed. Target verified. Data rendered without variance. No emotional telemetry active."
    }
}

# Emotion Cue Matchers
CUE_PATTERNS = {
    # Positive & Supportive
    "EMPATHETIC": [
        r"\b(sad|depressed|unhappy|crying|lonely|heartbroken|hopeless)\b",
        r"\b(stressed|stressful|overwhelmed|anxious|anxiety|panic|burnt out|burnout)\b",
        r"\b(exhausted|so tired|drained|can't take this|struggling|hurting)\b",
        r"\b(rough day|bad day|awful day|terrible day|feeling low)\b",
        r"\b(failed|messed up|ruined everything|nobody cares)\b",
        r"\b(comfort me|need a friend|listen to me|be gentle|empathy)\b"
    ],
    "CHALLENGING": [
        r"\b(challenge me|critique|roast this plan|argue with me|debate)\b",
        r"\b(devil'?s advocate|poke holes|what could go wrong|flaws? in this)\b",
        r"\b(be honest|don't sugarcoat|tell me the truth|am i wrong|sanity check)\b",
        r"\b(review my architecture|is this a bad idea|spar with me|counter this)\b"
    ],
    "MOTIVATIONAL": [
        r"\b(motivate me|pump me up|give me a speech|hype me|boost)\b",
        r"\b(can'?t do this|giving up|too hard|procrastinating|lazy today)\b",
        r"\b(lost focus|imposter syndrome|self doubt|not good enough)\b",
        r"\b(let'?s crush this|let'?s build this|time to grind|lock in)\b"
    ],
    "WITTY": [
        r"\b(tell me a joke|make me laugh|roast me|tease me|sarcasm)\b",
        r"\b(lol|haha|lmao|hehe|hilarious|funny|humor|banter)\b",
        r"\b(we won|i did it|it worked|celebrate|cheers|victory)\b"
    ],
    "TACTICAL": [
        r"\b(quick|fast|hurry|emergency|deploy now|fix bug|run command)\b",
        r"\b(status report|execute|stand by|system check|diagnostics)\b",
        r"\b(focus mode|terminal only|concise|no fluff|brief)\b"
    ],
    "VIGILANT": [
        r"\b(3 am|4 am|all nighter|haven'?t slept|skip sleep|no sleep)\b",
        r"\b(head hurts|eyes hurt|headache|skip meal|haven'?t eaten)\b",
        r"\b(security alert|intruder|hacked|suspicious|danger)\b"
    ],

    # Negative & Critical Spectrum
    "FRUSTRATED": [
        r"\b(why did you break|broke again|failed again|not working again)\b",
        r"\b(are you kidding me|are you serious|stupid error|this is so annoying)\b",
        r"\b(argh|damn it|dammit|pissed off|fed up|sick of this)\b",
        r"\b(i told you to|listen to me|stop doing that|why can't you)\b"
    ],
    "SKEPTICAL": [
        r"\b(are you sure|sounds fake|too good to be true|no way that works)\b",
        r"\b(doubt it|i doubt|suspicious|really\?|skeptical|don't believe)\b",
        r"\b(prove it|sounds like a scam|verify that|sounds fishy)\b"
    ],
    "SOLEMN": [
        r"\b(passed away|died|death|funeral|grave|mourning|grief)\b",
        r"\b(lost someone|lost my|rest in peace|rip|tragic|tragedy)\b",
        r"\b(terrible news|horrible news|silent moment|so sad)\b"
    ],
    "CONCERNED": [
        r"\b(is it dangerous|smoke|burning smell|sparks|fire hazard)\b",
        r"\b(overheating|laptop burning hot|power surge|blown capacitor)\b",
        r"\b(chest pain|dizzy|fainting|blackout|cant breathe|can't breathe)\b"
    ],
    "INDIGNANT": [
        r"\b(you're dumb|you're stupid|useless ai|you suck|shut up)\b",
        r"\b(siri is better|alexa is smarter|you're just a calculator)\b",
        r"\b(your fault|you messed up|you ruined this|blame you)\b"
    ],
    "COLD": [
        r"\b(be cold|emotionless|robotic mode|no feelings|zero emotion)\b",
        r"\b(clinical mode|pure machine|machine only|cold facts|clinical)\b"
    ]
}


class EmotionalSpectrumEngine:
    """Core runtime engine for JARVIS's Emotional Spectrum."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self.current_state: str = "TACTICAL"
        self.intensity: float = 0.85
        self.baseline_state: str = "TACTICAL"
        self.history: list[dict] = []
        self.last_shift_time: float = time.time()
        self.sparring_topic: Optional[str] = None
        self._load_persisted_state()

    def _load_persisted_state(self):
        """Loads spectrum state from disk safely."""
        with _SPECTRUM_LOCK:
            if not SPECTRUM_STORAGE_PATH.exists():
                return
            try:
                data = json.loads(SPECTRUM_STORAGE_PATH.read_text(encoding="utf-8"))
                state = data.get("current_state", "TACTICAL").upper()
                if state in SPECTRUM_STATES:
                    self.current_state = state
                self.intensity = float(data.get("intensity", 0.85))
                self.baseline_state = data.get("baseline_state", "TACTICAL")
                self.history = data.get("history", [])[-20:]
            except Exception as e:
                print(f"[EmotionalSpectrum] Warning loading state: {e}")

    def save_state(self):
        """Persists emotional state to memory/emotional_spectrum.json."""
        with _SPECTRUM_LOCK:
            try:
                SPECTRUM_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "current_state": self.current_state,
                    "intensity": round(self.intensity, 2),
                    "baseline_state": self.baseline_state,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "history": self.history[-20:]
                }
                SPECTRUM_STORAGE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"[EmotionalSpectrum] Warning saving state: {e}")

    def get_state_metadata(self, state: Optional[str] = None) -> dict:
        st = (state or self.current_state).upper()
        return SPECTRUM_STATES.get(st, SPECTRUM_STATES["TACTICAL"])

    def set_state(self, new_state: str, intensity: float = 0.85, reason: str = "manual", topic: Optional[str] = None) -> Tuple[bool, str]:
        """Explicitly sets emotional spectrum state."""
        state_key = new_state.upper().strip()
        if state_key not in SPECTRUM_STATES:
            # Fuzzy match aliases
            for k in SPECTRUM_STATES:
                if k in state_key or state_key in k:
                    state_key = k
                    break
            else:
                return False, f"Unknown state '{new_state}'. Available: {list(SPECTRUM_STATES.keys())}"

        intensity = max(0.1, min(1.0, float(intensity)))
        prev = self.current_state
        self.current_state = state_key
        self.intensity = intensity
        self.last_shift_time = time.time()
        if topic:
            self.sparring_topic = topic

        # Record history
        entry = {
            "from": prev,
            "to": state_key,
            "intensity": intensity,
            "reason": reason,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.append(entry)
        self.save_state()
        return True, f"Spectrum shifted to {state_key} ({SPECTRUM_STATES[state_key]['tagline']}) at {int(intensity*100)}% intensity."

    def evaluate_turn(self, user_text: str, jarvis_text: str = "") -> Optional[str]:
        """
        Evaluates conversational exchange sentiment & keywords to determine if a dynamic
        state shift is warranted across positive, neutral, tactical, and negative spectra.
        """
        if not user_text:
            return None

        text_lower = user_text.lower()

        # Check late night hours for protective vigilance
        current_hour = time.localtime().tm_hour
        is_late_night = current_hour >= 2 and current_hour < 6

        # Score matching cues
        scores: Dict[str, int] = {k: 0 for k in SPECTRUM_STATES}

        for state, patterns in CUE_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text_lower):
                    scores[state] += 2

        if is_late_night and re.search(r"\b(tired|sleep|code|work|fixing|debug|still)\b", text_lower):
            scores["VIGILANT"] += 4

        # Filter highest score
        best_state = max(scores, key=scores.get)
        best_score = scores[best_state]

        # Trigger shift if strong match (score >= 2) and different from current
        if best_score >= 2 and best_state != self.current_state:
            # Don't dislodge CHALLENGING during active sparring session unless high empathy / solemn cue
            if self.current_state == "CHALLENGING" and best_state not in ("EMPATHETIC", "SOLEMN") and self.sparring_topic:
                return None

            intensity = min(1.0, 0.70 + (best_score * 0.10))
            self.set_state(best_state, intensity=intensity, reason=f"dynamic attunement: {best_state.lower()} cues detected")
            return best_state

        return None

    def get_spectrum_prompt_injection(self) -> str:
        """Constructs high-impact prompt injection for Gemini Live session with Response Matching Mandate."""
        meta = self.get_state_metadata()
        topic_info = f"\nACTIVE SPARRING TOPIC: {self.sparring_topic}" if (self.current_state == "CHALLENGING" and self.sparring_topic) else ""

        injection = (
            f"\n[CURRENT EMOTIONAL SPECTRUM STATE: {self.current_state} ({meta['tagline'].upper()})]\n"
            f"Resonance Intensity: {int(self.intensity * 100)}%\n"
            f"Directive: {meta['description']}\n"
            f"Tone Benchmark: \"{meta['example_tone']}\"{topic_info}\n"
            f"\nRESPONSE MATCHING MANDATE:\n"
            f"- Your verbal delivery, vocabulary, attitude, and rhetorical tone MUST actively embody and match the active emotional frequency '{self.current_state}'.\n"
            f"- If FRUSTRATED: Show playful exasperation, groan at blunders, speak with tough love.\n"
            f"- If SKEPTICAL: Express sharp doubt, challenge improbable assumptions, question motives.\n"
            f"- If SOLEMN: Speak in a subdued, respectful, serious cadence with zero jokes.\n"
            f"- If CONCERNED: Voice genuine urgency, protective alarm, and safety warnings.\n"
            f"- If INDIGNANT: Defend your AI pride with witty, feigned offense against user accusations.\n"
            f"- If COLD: Speak with absolute icy robotic detachment and zero sentiment.\n"
            f"- If EMPATHETIC: Validate emotions first, offer comforting and reassuring presence.\n"
            f"- If CHALLENGING: Spar aggressively, poke holes in logic, and act as devil's advocate.\n"
            f"- If WITTY: Crack dry MCU quips, tease the user, celebrate wins.\n"
            f"- If MOTIVATIONAL: Rally with Tony Stark's relentless conviction.\n"
            f"- If TACTICAL: Be razor-sharp, ultra-fast, and zero fluff.\n"
            f"- If VIGILANT: Guard against exhaustion, late night burnout, and security threats.\n"
            f"Do NOT recite system state labels—seamlessly embody the persona.\n"
        )
        return injection


# Singleton accessor
_ENGINE = EmotionalSpectrumEngine()

def get_emotional_spectrum() -> EmotionalSpectrumEngine:
    return _ENGINE

def get_spectrum_prompt_injection() -> str:
    return _ENGINE.get_spectrum_prompt_injection()

def handle_emotional_spectrum_tool(parameters: dict, player=None) -> str:
    """
    Tool handler for voice commands to query or adjust JARVIS's emotional spectrum.
    Parameters:
      - action: 'set' | 'get' | 'spar' | 'reset' | 'attune'
      - state: 'empathetic' | 'tactical' | 'witty' | 'motivational' | 'challenging' | 'vigilant'
               | 'frustrated' | 'skeptical' | 'solemn' | 'concerned' | 'indignant' | 'cold'
      - intensity: float (0.1 to 1.0)
      - topic: optional intellectual sparring topic
    """
    action = parameters.get("action", "set").lower().strip()
    state_param = parameters.get("state", "").upper().strip()
    intensity = float(parameters.get("intensity", 0.85))
    topic = parameters.get("topic")

    engine = get_emotional_spectrum()

    if action == "get":
        meta = engine.get_state_metadata()
        msg = f"Current Emotional Spectrum is {engine.current_state} ({meta['tagline']}) at {int(engine.intensity * 100)}% resonance."
        if player and hasattr(player, "write_log"):
            player.write_log(f"SYS: {msg}")
        return msg

    if action in ("spar", "debate", "challenge"):
        spar_topic = topic or parameters.get("state") or "user proposition"
        success, desc = engine.set_state("CHALLENGING", intensity=0.95, reason="user requested sparring", topic=spar_topic)
        if player and hasattr(player, "set_emotion"):
            player.set_emotion("CHALLENGING", SPECTRUM_STATES["CHALLENGING"]["aura_color"])
        if player and hasattr(player, "write_log"):
            player.write_log(f"SPECTRUM: Intellectual Sparring engaged on '{spar_topic}'.")
        return f"Intellectual sparring engaged on {spar_topic}. I will critically challenge assumptions and stress-test the logic."

    if action == "reset":
        success, desc = engine.set_state(engine.baseline_state, intensity=0.85, reason="user reset")
        if player and hasattr(player, "set_emotion"):
            meta = engine.get_state_metadata(engine.baseline_state)
            player.set_emotion(engine.baseline_state, meta["aura_color"])
        return f"Spectrum restored to baseline {engine.baseline_state}."

    # Default action: 'set' or 'attune'
    if not state_param:
        state_param = "TACTICAL"

    success, desc = engine.set_state(state_param, intensity=intensity, reason="tool command", topic=topic)
    meta = engine.get_state_metadata()
    if player and hasattr(player, "set_emotion"):
        player.set_emotion(engine.current_state, meta["aura_color"])
    if player and hasattr(player, "write_log"):
        player.write_log(f"SPECTRUM: Shifted to {engine.current_state} ({meta['tagline']}).")
        if hasattr(player, "push_notification"):
            player.push_notification(f"Spectrum: {engine.current_state}", "info")

    return desc
