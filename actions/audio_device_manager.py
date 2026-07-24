"""
actions/audio_device_manager.py — Dynamic Audio Device & Bluetooth/Jack Switcher for JARVIS Mark XL
Allows switching audio output/input devices dynamically between Speakers, Bluetooth Headphones, and 3.5mm Audio Jack.
"""

import json
import threading
import time
import sounddevice as sd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "jarvis_settings.json"


class AudioDeviceManager:
    """Singleton Audio Device Manager for tracking and switching audio input/output devices."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self):
        self.output_device = None  # None = system default
        self.input_device = None   # None = system default
        self.last_devices_hash = ""
        self.player = None
        self._load_saved_preferences()
        
        # Start background monitor for Bluetooth / Audio Jack hot-plugging
        self.monitor_thread = threading.Thread(target=self._hotplug_monitor, daemon=True)
        self.monitor_thread.start()

    def _load_saved_preferences(self):
        try:
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.output_device = cfg.get("audio_output_device", None)
                self.input_device = cfg.get("audio_input_device", None)
        except Exception:
            pass

    def _save_preferences(self):
        try:
            cfg = {}
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            cfg["audio_output_device"] = self.output_device
            cfg["audio_input_device"] = self.input_device
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4)
        except Exception:
            pass

    def get_output_devices(self) -> list[dict]:
        """Returns all available audio output devices."""
        outputs = []
        try:
            devices = sd.query_devices()
            for idx, dev in enumerate(devices):
                if dev.get("max_output_channels", 0) > 0:
                    name = dev.get("name", f"Device {idx}")
                    hostapi_name = ""
                    try:
                        hostapi_info = sd.query_hostapis(dev.get("hostapi", 0))
                        hostapi_name = hostapi_info.get("name", "")
                    except Exception:
                        pass
                    
                    # Ignore WDM-KS kernel streaming endpoints (blocking API not supported)
                    if "wdm" in hostapi_name.lower() or "ks" in hostapi_name.lower():
                        continue
                    
                    is_bt = any(k in name.lower() for k in ["bluetooth", "hands-free", "bth", "wireless", "xm5", "pods", "buds"])
                    is_jack = any(k in name.lower() for k in ["headphone", "headset", "realtek", "high definition audio"])
                    
                    outputs.append({
                        "index": idx,
                        "name": name,
                        "hostapi": hostapi_name,
                        "channels": dev.get("max_output_channels"),
                        "default_samplerate": dev.get("default_samplerate"),
                        "is_bluetooth": is_bt,
                        "is_jack": is_jack,
                    })
        except Exception as e:
            print(f"[AudioDeviceMgr] Error querying output devices: {e}")
        return outputs

    def get_input_devices(self) -> list[dict]:
        """Returns all available audio input devices."""
        inputs = []
        try:
            devices = sd.query_devices()
            for idx, dev in enumerate(devices):
                if dev.get("max_input_channels", 0) > 0:
                    name = dev.get("name", f"Device {idx}")
                    inputs.append({
                        "index": idx,
                        "name": name,
                        "channels": dev.get("max_input_channels"),
                    })
        except Exception as e:
            print(f"[AudioDeviceMgr] Error querying input devices: {e}")
        return inputs

    def find_best_matching_output(self, query: str) -> int | None:
        """Finds device index matching query string (e.g. 'bluetooth', 'headphones', 'speakers', 'realtek', 'xm5')."""
        query_lower = query.lower().strip()
        devices = self.get_output_devices()

        if not devices:
            return None

        # 1. Exact or keyword match
        for dev in devices:
            name_lower = dev["name"].lower()
            if query_lower in name_lower or name_lower in query_lower:
                return dev["index"]

        # 2. Category match: bluetooth
        if "bluetooth" in query_lower or "bt" in query_lower or "wireless" in query_lower:
            for dev in devices:
                if dev["is_bluetooth"]:
                    return dev["index"]

        # 3. Category match: jack / headphones
        if "jack" in query_lower or "headphone" in query_lower or "aux" in query_lower:
            for dev in devices:
                if dev["is_jack"]:
                    return dev["index"]

        # 4. Category match: speakers
        if "speaker" in query_lower:
            for dev in devices:
                if "speaker" in dev["name"].lower():
                    return dev["index"]

        return None

    def set_output_device(self, device_identifier) -> str:
        """Sets the active output device for JARVIS playback."""
        if isinstance(device_identifier, str):
            idx = self.find_best_matching_output(device_identifier)
            if idx is None:
                return f"Could not find audio device matching '{device_identifier}'."
        else:
            idx = int(device_identifier)

        try:
            dev_info = sd.query_devices(idx)
            if dev_info.get("max_output_channels", 0) == 0:
                return f"Device index {idx} does not support audio output."

            self.output_device = idx
            dev_name = dev_info.get("name", f"Device #{idx}")
            self._save_preferences()

            if self.player:
                if hasattr(self.player, "write_log"):
                    self.player.write_log(f"AUDIO: Switched playback output to '{dev_name}'.")
                if hasattr(self.player, "push_notification"):
                    self.player.push_notification(f"Audio output: {dev_name}", "success")

            return f"Audio output switched to '{dev_name}'."
        except Exception as e:
            return f"Failed to set audio output device: {e}"

    def reset_to_default(self) -> str:
        """Resets audio routing to system default."""
        self.output_device = None
        self.input_device = None
        self._save_preferences()
        return "Audio output and input reset to system default endpoint."

    def _hotplug_monitor(self):
        """Background thread monitoring for Bluetooth / Audio Jack connection changes."""
        while True:
            try:
                time.sleep(3.0)
                current_devices = sd.query_devices()
                device_names = [d.get("name", "") for d in current_devices]
                current_hash = hashlib_md5("".join(device_names))
                
                if self.last_devices_hash and current_hash != self.last_devices_hash:
                    # Device configuration changed! (e.g. Bluetooth connected or jack plugged in)
                    self.last_devices_hash = current_hash
                    
                    # Auto-check if a Bluetooth or headphone device just connected
                    bt_devices = [d for d in current_devices if d.get("max_output_channels", 0) > 0 and any(k in d.get("name", "").lower() for k in ["bluetooth", "wh-1000", "xm5", "hands-free", "headphone"])]
                    if bt_devices and self.output_device is None:
                        best = bt_devices[0]
                        print(f"[AudioDeviceMgr] 🎧 Hot-plug detected: {best['name']}")
                        if self.player:
                            if hasattr(self.player, "write_log"):
                                self.player.write_log(f"AUDIO: External audio device detected — '{best['name']}'.")
                            if hasattr(self.player, "push_notification"):
                                self.player.push_notification(f"External Audio Connected: {best['name']}", "info")
                else:
                    self.last_devices_hash = current_hash
            except Exception:
                pass


def hashlib_md5(text: str) -> str:
    import hashlib
    return hashlib.md5(text.encode("utf-8")).hexdigest()


audio_device_mgr = AudioDeviceManager()


def audio_device_control(parameters: dict, player=None) -> str:
    """
    Action handler for audio device management.

    parameters:
        action : list | set_output | set_input | auto_detect | reset
        device : Device name, index, or keyword (e.g. "bluetooth", "headphones", "speakers", "jack")
    """
    audio_device_mgr.player = player
    params = parameters or {}
    action = (params.get("action") or "list").lower().strip()
    device = params.get("device", "").strip()

    if action in ("list", "show", "devices"):
        outputs = audio_device_mgr.get_output_devices()
        if not outputs:
            return "No audio output devices found."

        summary_lines = ["Available Audio Output Devices:"]
        for dev in outputs[:10]: # Top 10 devices
            tag = " [Bluetooth 🎧]" if dev["is_bluetooth"] else (" [Audio Jack 🔌]" if dev["is_jack"] else "")
            curr = " (ACTIVE)" if audio_device_mgr.output_device == dev["index"] else ""
            summary_lines.append(f"• #{dev['index']} {dev['name']}{tag}{curr}")

        return "\n".join(summary_lines)

    if action in ("set_output", "switch", "change_output", "connect"):
        if not device:
            return "Please specify which audio device or keyword to switch to (e.g., 'bluetooth', 'headphones', 'speakers')."
        return audio_device_mgr.set_output_device(device)

    if action in ("reset", "default"):
        audio_device_mgr.output_device = None
        return "Reset audio output to system default playback device."

    # Default fallback switch if device provided
    if device:
        return audio_device_mgr.set_output_device(device)

    return audio_device_control({"action": "list"}, player=player)
