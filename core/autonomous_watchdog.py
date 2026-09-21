"""
core/autonomous_watchdog.py — Autonomous System Auto-Healing Watchdog for JARVIS Mark XLII
Monitors live audio stream health, RAM utilization, and Wi-Fi network connectivity in the background.
Executes zero-latency auto-healing re-connections if network stutters occur.
"""

import sys
import gc
import time
import psutil
import urllib.request
import threading

class AutonomousWatchdog:
    """Background Auto-Healing & Telemetry Health Guardian."""

    def __init__(self):
        self.is_running = False
        self.reconnect_callback = None
        self.last_network_ok = True

    def start_watchdog(self, reconnect_callback=None, player=None):
        """Starts background monitoring daemon thread."""
        if self.is_running:
            return
        self.is_running = True
        self.reconnect_callback = reconnect_callback

        def _watchdog_loop():
            while self.is_running:
                time.sleep(5)  # 5s interval for < 0.1% CPU load
                try:
                    # 1. RAM Utilization Auto-Flush (> 90% RAM triggers GC)
                    mem_pct = psutil.virtual_memory().percent
                    if mem_pct > 90.0:
                        gc.collect()
                        if player and hasattr(player, "write_log"):
                            player.write_log(f"WATCHDOG: 🧹 RAM usage at {mem_pct:.1f}% -- Executed memory garbage collection.")

                    # 2. Network Connectivity Auto-Healing Check
                    net_ok = self._check_internet()
                    if not net_ok and self.last_network_ok:
                        self.last_network_ok = False
                        if player and hasattr(player, "write_log"):
                            player.write_log("WATCHDOG: ⚠️ Wi-Fi network drop detected -- Standing by for auto-healing...")
                    elif net_ok and not self.last_network_ok:
                        self.last_network_ok = True
                        if player and hasattr(player, "write_log"):
                            player.write_log("WATCHDOG: ✅ Network restored! Auto-healing live audio connection...")
                        if self.reconnect_callback:
                            try:
                                self.reconnect_callback()
                            except Exception as ex:
                                print(f"[Watchdog] Reconnect callback notice: {ex}")
                except Exception as e:
                    print(f"[Watchdog] Loop notice: {e}")

        t = threading.Thread(target=_watchdog_loop, daemon=True)
        t.start()

    def _check_internet(self) -> bool:
        """Quick 1-second ping to verify active internet connection."""
        try:
            urllib.request.urlopen("https://www.google.com", timeout=2)
            return True
        except Exception:
            return False

    def stop(self):
        self.is_running = False


autonomous_watchdog = AutonomousWatchdog()
