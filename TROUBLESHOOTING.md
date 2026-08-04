# 🛠️ J.A.R.V.I.S. Mark XLI — Troubleshooting & FAQ Guide

Welcome! If you encounter any issues downloading, installing, or running J.A.R.V.I.S., follow the quick solutions below.

---

## ❓ Common Issues & Solutions

### 1. `python` command is not recognized or opens Microsoft Store
- **Cause**: Windows dummy App Execution Aliases are redirecting `python.exe` to the Microsoft Store.
- **Solution**:
  1. Open Windows **Settings** ➔ **Apps** ➔ **Advanced app settings** ➔ **App execution aliases**.
  2. Turn **OFF** `App Installer python.exe` and `App Installer python3.exe`.
  3. Re-run `setup.bat` (or install standard Python 3.10+ from [python.org](https://www.python.org/downloads/) and check *"Add Python to PATH"* during setup).

---

### 2. MAX_PATH / Long File Path Error (`OSError: [Errno 2] No such file or directory`)
- **Cause**: Windows has a 260-character path limit by default.
- **Solution**:
  - Running `setup.bat` automatically enables Windows Long Paths in the registry.
  - Make sure you run `setup.bat`, which creates a local virtual environment (`venv`) inside the project folder so path lengths remain short.

---

### 3. `pyaudio` compilation error (`Microsoft Visual C++ 14.0 or greater is required`)
- **Cause**: You are using Python 3.13+ or pre-release Python where pre-compiled PyAudio wheel binaries are not yet available on PyPI.
- **Solution**:
  - Simply run `setup.bat`. `setup.bat` automatically attempts to install pre-compiled wheel binaries via `pipwin`.
  - Even if PyAudio compilation fails, **JARVIS continues cleanly** using `sounddevice` as the primary audio recording engine!

---

### 4. `git` command not recognized in Command Prompt
- **Cause**: Git for Windows is either not installed or not added to system PATH.
- **Solution**:
  - Download Git for Windows from [git-scm.com](https://git-scm.com/) and check *"Add Git to Windows PATH"*, or run commands inside **Git Bash**.

---

### 5. `api_keys.json` Missing or Invalid API Key Error
- **Cause**: Gemini API key has not been configured yet.
- **Solution**:
  1. Get a **Free Gemini API Key** from [Google AI Studio](https://aistudio.google.com/app/apikey).
  2. Open `config/api_keys.json` in Notepad.
  3. Paste your key:
     ```json
     {
         "gemini_api_key": "AIzaSy..."
     }
     ```
  4. Save the file and double-click `main.bat`!

---

## 🌐 Platform Compatibility Matrix
- **Windows 10 / 11**: Fully Supported (100% Native).
- **macOS / Linux**: Supported via `setup.sh` and `main.sh`.
