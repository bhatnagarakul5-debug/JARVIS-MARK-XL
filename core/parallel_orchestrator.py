"""
core/parallel_orchestrator.py — J.A.R.V.I.S. Mark XLI "Bones" Asynchronous Task Orchestrator
Executes long-running worker tasks (research, media processing, code generation) in background threads without voice lag.
"""

import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any

class ParallelOrchestrator:
    """Asynchronous worker pool manager for parallel background sub-brain tasks."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.executor = ThreadPoolExecutor(max_workers=6, thread_name_prefix="Mark41_SubBrain")
            cls._instance.active_tasks = {}
            cls._instance.completed_tasks = {}
            cls._instance._lock = threading.Lock()
        return cls._instance

    def submit_task(self, name: str, fn: Callable, args=(), kwargs=None, callback: Callable = None) -> str:
        """Submits a background task to the parallel worker thread pool."""
        task_id = str(uuid.uuid4())[:8]
        kwargs = kwargs or {}
        
        with self._lock:
            self.active_tasks[task_id] = {
                "name": name,
                "start_time": time.time(),
                "status": "RUNNING"
            }

        def _wrapper():
            try:
                res = fn(*args, **kwargs)
                with self._lock:
                    self.active_tasks.pop(task_id, None)
                    self.completed_tasks[task_id] = {
                        "name": name,
                        "result": str(res),
                        "status": "COMPLETED",
                        "end_time": time.strftime("%I:%M:%S %p")
                    }
                if callback:
                    try:
                        callback(res)
                    except Exception:
                        pass
                return res
            except Exception as e:
                with self._lock:
                    self.active_tasks.pop(task_id, None)
                    self.completed_tasks[task_id] = {
                        "name": name,
                        "result": f"Task error: {e}",
                        "status": "FAILED",
                        "end_time": time.strftime("%I:%M:%S %p")
                    }

        self.executor.submit(_wrapper)
        return f"Sub-Brain Task '{name}' [ID: #{task_id}] dispatched to parallel thread."

    def list_active_tasks(self) -> str:
        """Returns summary of all running and recently completed background sub-brain tasks."""
        with self._lock:
            running = list(self.active_tasks.values())
            done = list(self.completed_tasks.values())

        if not running and not done:
            return "Mark XLI Parallel Orchestrator: All background sub-brain workers idle."

        lines = ["=== Mark XLI Parallel Sub-Brain Tasks ==="]
        if running:
            lines.append(f"Running Tasks ({len(running)}):")
            for t in running:
                elapsed = int(time.time() - t['start_time'])
                lines.append(f"  • {t['name']} (running {elapsed}s)")
        
        if done:
            lines.append(f"\nRecently Completed ({len(done[-5:])}):")
            for t in done[-5:]:
                lines.append(f"  • {t['name']} -> {t['status']} at {t['end_time']}")

        return "\n".join(lines)


parallel_orchestrator = ParallelOrchestrator()
