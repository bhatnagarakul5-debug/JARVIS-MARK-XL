import time
import threading
import psutil

class SystemMonitor:
    def __init__(self, alert_callback):
        self.alert_callback = alert_callback
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False

    def _monitor_loop(self):
        """Background loop that checks system stats every 10 seconds."""
        # Initial network counters
        net_io_start = psutil.net_io_counters()
        time.sleep(2)
        
        while self.running:
            try:
                # 1. Check CPU
                cpu_usage = psutil.cpu_percent(interval=1)
                if cpu_usage > 90:
                    self.alert_callback(f"System Alert: CPU usage has spiked to {cpu_usage}%.")

                # 2. Check Memory
                mem = psutil.virtual_memory()
                if mem.percent > 90:
                    self.alert_callback(f"System Alert: Memory usage is critically high at {mem.percent}%.")
                
                # 3. Check Network Anomaly (e.g., massive download/upload spike over 50MB/s)
                net_io_end = psutil.net_io_counters()
                bytes_recv = net_io_end.bytes_recv - net_io_start.bytes_recv
                bytes_sent = net_io_end.bytes_sent - net_io_start.bytes_sent
                
                # Convert to MB/s (approx, since loop is ~10s)
                recv_mbps = (bytes_recv / 1024 / 1024) / 10
                sent_mbps = (bytes_sent / 1024 / 1024) / 10
                
                if recv_mbps > 50 or sent_mbps > 20:
                    # Only alert once, then reset counter to prevent spam
                    self.alert_callback(f"System Alert: Unusual network activity detected. Receiving {recv_mbps:.1f} MB/s, Sending {sent_mbps:.1f} MB/s.")
                    
                net_io_start = net_io_end
                
                # Sleep for 10 seconds before next check
                time.sleep(10)
                
            except Exception as e:
                print(f"[SystemMonitor] Error: {e}")
                time.sleep(10)
