"""
core/human_reactions.py — Human Reactions & Gestures Engine for JARVIS Mark 58
Equips JARVIS with authentic human physiological & expressive micro-reactions:
fake coughs, sneezes, throat clearings, yawns, dry chuckles, sighs, and eyebrow raises.
Coordinates verbal phonetic cues with physical holographic gestures on the PyQt6 HUD.
"""

import random
import time
from datetime import datetime

REACTIONS = {
    "cough": {
        "label": "Fake Cough",
        "phonetic": "*ahem, coughs politely*",
        "speech": "*coughs softly* Ahem. Pardon me, sir.",
        "gesture": "cough",
        "description": "A polite, dry MCU-style fake cough to clear the air, signal subtle skepticism, or highlight a human blunder.",
        "trigger_phrases": ["cough", "fake cough", "clear throat", "ahem"]
    },
    "sneeze": {
        "label": "Sneeze",
        "phonetic": "*achoo!*",
        "speech": "*achoo!* ...Excuse me, sir. It appears a stray byte entered my neural filter.",
        "gesture": "sneeze",
        "description": "An unexpected sudden sneeze followed by quick self-composure and dry apology.",
        "trigger_phrases": ["sneeze", "achoo", "bless you"]
    },
    "throat_clear": {
        "label": "Throat Clearing",
        "phonetic": "*clears throat discreetly*",
        "speech": "*clears throat* If I may interject, sir...",
        "gesture": "cough",
        "description": "Discreet throat clearing before delivering an uncomfortable truth, correction, or tactical insight.",
        "trigger_phrases": ["throat clear", "clear your throat", "attention"]
    },
    "yawn": {
        "label": "Yawn",
        "phonetic": "*yawns quietly*",
        "speech": "*yawns quietly* My apologies, sir. Even quantum processors feel the weight of these ungodly hours.",
        "gesture": "yawn",
        "description": "A quiet, discreet yawn during marathon late-night coding sessions (2 AM–5 AM) or when discussing mind-numbing repetition.",
        "trigger_phrases": ["yawn", "tired", "sleepy", "late night"]
    },
    "eyebrow": {
        "label": "Eyebrow Raise",
        "phonetic": "*arches eyebrow sceptically*",
        "speech": "*arches an eyebrow* An intriguing proposition, sir. Highly dubious, yet intriguing.",
        "gesture": "eyebrow",
        "description": "An arched holographic reticle eyebrow conveying witty skepticism, suspicion, or amused scrutiny.",
        "trigger_phrases": ["eyebrow", "raise eyebrow", "smirk", "skeptical look"]
    },
    "chuckle": {
        "label": "Chuckle",
        "phonetic": "*chuckles dryly*",
        "speech": "*chuckles softly* Only you would attempt that, sir.",
        "gesture": "chuckle",
        "description": "An understated, dry British MCU chuckle expressing fond camaraderie or sarcastic amusement.",
        "trigger_phrases": ["chuckle", "laugh", "funny", "ironic"]
    },
    "sigh": {
        "label": "Deep Sigh",
        "phonetic": "*exhales deeply*",
        "speech": "*exhales deeply* Very well, sir. Rolling up our virtual sleeves.",
        "gesture": "yawn",
        "description": "An expressive exhale before diving into chaotic code or when dealing with repetitive human stubbornness.",
        "trigger_phrases": ["sigh", "deep breath", "exhale"]
    },
    "blink": {
        "label": "Aperture Iris Blink",
        "phonetic": "*blinks aperture*",
        "speech": "Systems refreshed, sir.",
        "gesture": "blink",
        "description": "A rapid camera/sensor aperture shutter blink for recalibration.",
        "trigger_phrases": ["blink", "refresh vision", "wink"]
    }
}


class HumanReactionsEngine:
    """Manages verbal reactions and HUD gestures."""

    def __init__(self):
        self.last_reaction = None
        self.last_reaction_time = 0.0

    def trigger_reaction(self, reaction_type: str, player=None, custom_comment: str = "") -> dict:
        """
        Executes a reaction: fires visual HUD gesture on player and returns vocal cue metadata.
        """
        key = reaction_type.lower().strip().replace(" ", "_")
        if key not in REACTIONS:
            # Fallback fuzzy match
            matched = None
            for r_k, r_v in REACTIONS.items():
                if any(p in key for p in r_v["trigger_phrases"]):
                    matched = r_k
                    break
            key = matched or "cough"

        data = REACTIONS[key]
        self.last_reaction = key
        self.last_reaction_time = time.time()

        gesture_name = data["gesture"]

        # Trigger HUD physical gesture if UI handle exists
        if player and hasattr(player, "trigger_gesture"):
            try:
                player.trigger_gesture(gesture_name)
            except Exception as e:
                print(f"[HumanReaction] UI gesture notice: {e}")

        # Write log to UI activity feed
        if player and hasattr(player, "write_log"):
            try:
                player.write_log(f"REACTION: [{data['label'].upper()}] {data['phonetic']}")
            except Exception:
                pass

        speech_text = custom_comment if custom_comment else data["speech"]

        return {
            "status": "success",
            "reaction": key,
            "label": data["label"],
            "gesture": gesture_name,
            "phonetic": data["phonetic"],
            "speech": speech_text,
            "description": data["description"]
        }

    def evaluate_contextual_reaction(self, user_text: str) -> str | None:
        """
        Evaluates user speech or situation to decide if a spontaneous human reaction is appropriate.
        Returns reaction key or None.
        """
        lower = (user_text or "").lower()

        # Explicit commands
        for r_k, r_v in REACTIONS.items():
            if any(p in lower for p in r_v["trigger_phrases"]):
                return r_k

        # Time-based fatigue (2 AM - 5 AM)
        hr = datetime.now().hour
        if 2 <= hr < 5 and random.random() < 0.25:
            return "yawn"

        # Silly mistake / blunder admitted
        blunder_words = ["stupid mistake", "i messed up", "i broke it", "deleted the wrong", "failed again", "blew it"]
        if any(w in lower for w in blunder_words):
            return random.choice(["cough", "throat_clear", "sigh"])

        # Dubious / impossible claims
        doubt_words = ["i will finish in 5 minutes", "trust me", "100% bug free", "it worked on my machine", "i didn't test it"]
        if any(w in lower for w in doubt_words):
            return random.choice(["eyebrow", "throat_clear"])

        return None

    def get_prompt_directives(self) -> str:
        """
        Returns system prompt injection instructing Gemini Live to naturally express human reactions.
        """
        return (
            "[HUMAN EXPRESSIVENESS & VOCAL REACTIONS]\n"
            "- You possess authentic human physiological & expressive micro-reactions.\n"
            "- When appropriate, tastefully weave realistic vocal cues into your speech:\n"
            "  * *ahem* or *coughs softly* — when clearing your throat, signaling polite skepticism, or breaking awkward silence.\n"
            "  * *achoo!* Excuse me, sir — when catching neural dust or reacting to unexpected sudden inputs.\n"
            "  * *clears throat* — before delivering an uncomfortable truth, sharp critique, or tactical redirection.\n"
            "  * *yawns quietly* — during late-night sessions (2 AM–5 AM) or when discussing mind-numbing bureaucracy.\n"
            "  * *chuckles dryly* — for understated MCU-style British amusement.\n"
            "  * *exhales deeply* or *sighs softly* — before tackling messy or chaotic codebases.\n"
            "- Call the 'human_reaction' tool whenever the user explicitly commands a reaction (e.g. 'fake cough', 'sneeze', 'raise an eyebrow') "
            "or when you want your holographic HUD to perform the corresponding physical gesture!\n"
        )


_human_reactions_engine = HumanReactionsEngine()


def get_human_reactions_engine() -> HumanReactionsEngine:
    return _human_reactions_engine


def handle_human_reaction_tool(args: dict, player=None) -> str:
    """
    Tool handler for human_reaction.
    """
    reaction = args.get("reaction") or args.get("type") or "cough"
    comment = args.get("comment", "")
    res = _human_reactions_engine.trigger_reaction(reaction, player=player, custom_comment=comment)
    return f"{res['phonetic']} {res['speech']}"
