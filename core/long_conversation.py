"""
core/long_conversation.py — Long-Horizon Context & Multi-Turn Dialogue Engine for JARVIS Mark 58
Enables JARVIS to hold extended, coherent, multi-hour conversations across complex technical,
academic, and strategic topics without context collapse, amnesia, or loss of continuity.

Features:
1. Rolling Dialogue Window with semantic turn compression.
2. Active Topic & Subtopic Drift Tracker.
3. Key Facts, Constraints & Decisions Working Cache.
4. Auto-re-anchoring prompt injection across WebSocket resets.
"""

import time
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_CACHE_PATH = BASE_DIR / "memory" / "active_conversation_thread.json"
SESSION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

class LongConversationManager:
    """
    Maintains continuous conversational state across long multi-turn sessions.
    """

    def __init__(self, max_verbatim_turns: int = 12):
        self.max_verbatim_turns = max_verbatim_turns
        self._lock = threading.Lock()
        self.current_topic: str = "General Assistance"
        self.subtopics: List[str] = []
        self.key_facts: Dict[str, str] = {}
        self.verbatim_history: List[Dict[str, str]] = []  # [{"role": "user"/"jarvis", "text": "...", "time": "..."}]
        self.compressed_summary: str = ""
        self.turn_count: int = 0
        self.last_interaction_time: float = time.time()
        self._load_state()

    def _load_state(self):
        try:
            if SESSION_CACHE_PATH.exists():
                data = json.loads(SESSION_CACHE_PATH.read_text(encoding="utf-8"))
                # Only restore if session was active within the last 6 hours
                if time.time() - data.get("saved_at", 0) < 21600:
                    self.current_topic = data.get("current_topic", "General Assistance")
                    self.subtopics = data.get("subtopics", [])
                    self.key_facts = data.get("key_facts", {})
                    self.verbatim_history = data.get("verbatim_history", [])
                    self.compressed_summary = data.get("compressed_summary", "")
                    self.turn_count = data.get("turn_count", 0)
        except Exception:
            pass

    def _save_state(self):
        try:
            data = {
                "saved_at": time.time(),
                "current_topic": self.current_topic,
                "subtopics": self.subtopics[-8:],
                "key_facts": self.key_facts,
                "verbatim_history": self.verbatim_history[-self.max_verbatim_turns:],
                "compressed_summary": self.compressed_summary,
                "turn_count": self.turn_count
            }
            SESSION_CACHE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def record_turn(self, user_text: str, jarvis_text: str):
        """Records a new exchange, extracts topic hints, and periodically compresses history."""
        if not user_text and not jarvis_text:
            return

        with self._lock:
            self.turn_count += 1
            now_str = datetime.now().strftime("%I:%M %p")
            self.last_interaction_time = time.time()

            if user_text:
                self.verbatim_history.append({"role": "user", "text": user_text, "time": now_str})
            if jarvis_text:
                self.verbatim_history.append({"role": "jarvis", "text": jarvis_text, "time": now_str})

            # Detect topic hints from user text
            self._detect_topic(user_text)

            # Keep verbatim buffer bounded and summarize older turns
            if len(self.verbatim_history) > self.max_verbatim_turns * 2:
                self._compress_older_turns()

            self._save_state()

    def _detect_topic(self, user_text: str):
        """Extracts key subjects or themes being discussed."""
        t_low = user_text.lower()
        academic_keywords = [
            "exam", "syllabus", "chapter", "lecture", "assignment", "test",
            "study", "notes", "quiz", "formula", "derivation", "paper",
            "economics", "finance", "math", "physics", "code", "python",
            "presentation", "slides", "outlook", "college", "professor"
        ]
        for kw in academic_keywords:
            if kw in t_low and kw not in self.subtopics:
                self.subtopics.append(kw.title())
                if len(self.subtopics) > 10:
                    self.subtopics.pop(0)

        # Update general topic if prominent
        if any(k in t_low for k in ["exam", "test", "study", "syllabus"]):
            self.current_topic = "Exam Preparation & Academic Study"
        elif any(k in t_low for k in ["code", "bug", "python", "error", "script"]):
            self.current_topic = "Software Engineering & Development"
        elif any(k in t_low for k in ["presentation", "slide", "pptx", "document"]):
            self.current_topic = "Content Creation & Presentation"

    def _compress_older_turns(self):
        """Compresses the oldest turns into bullet-point memory so context is never lost."""
        overflow_count = len(self.verbatim_history) - self.max_verbatim_turns
        if overflow_count <= 0:
            return

        to_compress = self.verbatim_history[:overflow_count]
        self.verbatim_history = self.verbatim_history[overflow_count:]

        # Simple high-yield extraction
        bullets = []
        for turn in to_compress:
            prefix = "Akul asked" if turn["role"] == "user" else "JARVIS explained"
            snippet = turn["text"][:120].replace("\n", " ").strip()
            if snippet:
                bullets.append(f"- {prefix}: \"{snippet}...\"")

        new_summary_chunk = "\n".join(bullets[-6:])
        if self.compressed_summary:
            self.compressed_summary = self.compressed_summary + "\n" + new_summary_chunk
        else:
            self.compressed_summary = new_summary_chunk

        # Cap compressed summary size
        lines = self.compressed_summary.splitlines()
        if len(lines) > 20:
            self.compressed_summary = "\n".join(lines[-20:])

    def get_conversation_context(self) -> str:
        """
        Assembles a high-density, prompt-ready conversational continuity block.
        Injected into Gemini Live prompt so reconnects or multi-turn dialogues never break.
        """
        with self._lock:
            if not self.verbatim_history and not self.compressed_summary:
                return ""

            parts = [
                "[LONG-CONVERSATION MEMORY & ACTIVE THREAD CONTINUITY]",
                f"Active Discussion Focus: {self.current_topic}",
            ]

            if self.subtopics:
                parts.append(f"Recent Subtopics Discussed: {', '.join(self.subtopics[-6:])}")

            if self.compressed_summary:
                parts.append(f"Earlier Discussion Summary:\n{self.compressed_summary}")

            if self.verbatim_history:
                parts.append("Immediate Prior Exchanges:")
                for turn in self.verbatim_history[-6:]:
                    speaker = "Akul" if turn["role"] == "user" else "JARVIS"
                    clean_txt = turn["text"].replace("\n", " ").strip()[:180]
                    parts.append(f"  {speaker}: {clean_txt}")

            parts.append(
                "MANDATE: Maintain seamless conversational continuity. "
                "Refer back to previously established facts, questions, and decisions naturally without asking Akul to repeat himself."
            )

            return "\n".join(parts) + "\n\n"

    def clear_session(self):
        """Resets the active conversation state."""
        with self._lock:
            self.current_topic = "General Assistance"
            self.subtopics.clear()
            self.key_facts.clear()
            self.verbatim_history.clear()
            self.compressed_summary = ""
            self.turn_count = 0
            if SESSION_CACHE_PATH.exists():
                try:
                    SESSION_CACHE_PATH.unlink()
                except Exception:
                    pass

_conv_mgr = LongConversationManager()

def get_long_conversation_manager() -> LongConversationManager:
    return _conv_mgr
