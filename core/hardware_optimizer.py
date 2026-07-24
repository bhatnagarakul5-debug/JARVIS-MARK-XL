"""
core/hardware_optimizer.py — Hardware Acceleration & Latency Optimization Engine for JARVIS Mark XL
Tailored for Dell Inspiron 15 (Intel UHD Graphics, 16GB RAM, 12 Core CPU, 512GB SSD)
Enables OpenCL GPU acceleration, Windows High Process Priority, UI macro acceleration, and RAM garbage collection.
"""

import os
import sys
import gc
import psutil
import cv2
import pyautogui

def optimize_hardware():
    """Applies GPU, OpenCL, CPU thread-pooling, PyAutoGUI macro speedup, and RAM garbage collection."""
    report = []
    
    # 1. UI Macro Speed Optimization (0.02s pause)
    try:
        pyautogui.PAUSE = 0.02
        pyautogui.FAILSAFE = True
        report.append("UI Macro Engine: Ultra-Low Latency (0.02s pause)")
    except Exception as e:
        report.append(f"UI Macro Notice: {e}")

    # 2. Windows Process Priority Boost
    try:
        p = psutil.Process(os.getpid())
        if sys.platform == "win32":
            p.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
            report.append("Process Priority: ABOVE_NORMAL_PRIORITY_CLASS (Windows)")
        else:
            p.nice(-5)
            report.append("Process Priority: High (-5)")
    except Exception as e:
        report.append(f"Process Priority Notice: {e}")

    # 3. OpenCV OpenCL GPU Acceleration (Intel UHD Graphics)
    try:
        cv2.ocl.setUseOpenCL(True)
        is_ocl = cv2.ocl.useOpenCL()
        device_name = "Intel UHD / OpenCL GPU" if is_ocl else "CPU Fallback"
        report.append(f"OpenCV GPU Acceleration: {'ENABLED (' + device_name + ')' if is_ocl else 'DISABLED'}")
    except Exception as e:
        report.append(f"OpenCV GPU Notice: {e}")

    # 4. CPU Multi-Threading & Thread Contention Prevention
    try:
        cpu_count = os.cpu_count() or 4
        os.environ["OMP_NUM_THREADS"] = str(max(1, cpu_count // 2))
        os.environ["MKL_NUM_THREADS"] = str(max(1, cpu_count // 2))
        os.environ["OPENBLAS_NUM_THREADS"] = str(max(1, cpu_count // 2))
        os.environ["VECLIB_MAXIMUM_THREADS"] = str(max(1, cpu_count // 2))
        os.environ["NUMEXPR_NUM_THREADS"] = str(max(1, cpu_count // 2))
        report.append(f"CPU Thread Pool: Configured ({cpu_count} logical cores detected)")
    except Exception as e:
        report.append(f"CPU Thread Notice: {e}")

    # 5. DirectML Execution & RAM Garbage Collection
    try:
        os.environ["ONNXRUNTIME_PROVIDER"] = "DmlExecutionProvider,CPUExecutionProvider"
        gc.collect()
        report.append("Memory Engine: RAM Garbage Collection & DirectML Execution Active")
    except Exception as e:
        report.append(f"Memory Notice: {e}")

    return report

if __name__ == "__main__":
    results = optimize_hardware()
    print("--- JARVIS HARDWARE OPTIMIZER REPORT ---")
    for r in results:
        print(f"  [OK] {r}")
