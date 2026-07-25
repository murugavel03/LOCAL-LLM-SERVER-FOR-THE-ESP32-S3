Local LLM Server Hub (K10 Voice Assistant Server)

A desktop server app (Tkinter GUI) that receives voice audio from a "K10" hardware node over TCP, transcribes it with Whisper, generates a reply with a local Ollama model, converts the reply to speech, and sends the audio + text back to the K10 device. It also serves a small web UI and broadcasts itself on the LAN so K10 devices can auto-discover it.

Requirements
System
Python 3.10 or 3.11 recommended (Whisper/eventlet compatibility; avoid 3.12+ unless you've confirmed all packages support it)
Ollama installed and running locally — https://ollama.com
ffmpeg — required by Whisper for audio decoding
Either install it system-wide and have it on PATH, or
Place an ffmpeg executable in the folder one level above this script (the code auto-adds ../ to PATH at runtime)
Windows, macOS, or Linux (one line uses ctypes.windll, but it's guarded by sys.platform == "win32" so it's safe on other OSes)
A working network interface for UDP broadcast / LAN discovery
Python packages

Install with pip:

bash
pip install eventlet python-socketio openai-whisper ollama pyttsx3

Notes on package names:

whisper in the code refers to openai-whisper (pip install openai-whisper)
socketio refers to python-socketio (pip install python-socketio)
ollama refers to the ollama Python client (pip install ollama)
tkinter and wave ship with standard Python — on Linux you may need your distro's python3-tk package (e.g. sudo apt install python3-tk)
Ollama model

Pull the model used by the script before running:

bash
ollama pull phi3:mini

Make sure the Ollama service is running (ollama serve, or it may already run in the background after install).

Directory structure

The script looks for a ui folder to serve as the static web frontend. Depending on where the script lives, place your files like this:

project_root/
├── ui/                  # your web frontend (index.html, css, js, etc.)
└── k10_hub/
    └── final.py         # this script (if folder is named "k10_hub")

or, if the script is not inside a folder called k10_hub:

project_root/
├── ui/
└── final.py

A uploads/ folder is created automatically next to the script at runtime for storing input.wav and response.wav.

Ports used
Port	Protocol	Purpose
5000	TCP (HTTP/WebSocket)	Web UI + Socket.IO events
6000	TCP	Receives incoming voice audio from K10
6001	TCP	Sends text/audio replies back to K10
5005	UDP	LAN broadcast so K10 devices can discover this server

Make sure your firewall allows inbound connections on these ports if the K10 device is on the same network but blocked.

Running

From the project root (or wherever final.py lives, with ui/ in the right relative location):

bash
python final.py

On startup it will:

Open a Tkinter log window ("LOCAL LLM Display")
Load the Whisper base model into memory
Start the UDP discovery beacon
Start listening for K10 voice frames on port 6000
Start the web server (UI + Socket.IO) on port 5000

You can then open http://<this-machine-ip>:5000 in a browser to view the web UI, and K10 devices on the same LAN should auto-discover the server via the UDP beacon on port 5005.

Building a Windows .exe

Use PyInstaller to package this into a standalone executable. Whisper, eventlet, and socketio all pull in dynamic/hidden imports and data files that PyInstaller won't detect automatically, so a plain pyinstaller final.py will fail at runtime. Use the command below instead.

1. Install PyInstaller
bash
pip install pyinstaller
2. Build command

Run this from the folder containing final.py:

bash
pyinstaller final.py ^
  --name k10_hub ^
  --onedir ^
  --windowed ^
  --collect-all whisper ^
  --collect-all eventlet ^
  --collect-data whisper ^
  --hidden-import eventlet.hubs.epolls ^
  --hidden-import eventlet.hubs.kqueue ^
  --hidden-import eventlet.hubs.poll ^
  --hidden-import eventlet.hubs.selects ^
  --hidden-import engineio.async_drivers.eventlet ^
  --hidden-import pyttsx3.drivers ^
  --hidden-import pyttsx3.drivers.sapi5

(^ is the Windows CMD line-continuation character — if you're using PowerShell replace it with a backtick `, or just put the whole command on one line.)

Argument reference
Argument	Why it's needed
--name k10_hub	Names the output exe/folder k10_hub (matches the folder-name check in the script for locating ../ui)
--onedir	Produces a folder with the exe + dependencies (recommended over --onefile — Whisper's model files and ffmpeg are easier to manage this way, and startup is much faster)
--windowed	Suppresses the console window since this app has a Tkinter GUI (use --console instead if you want to see raw errors while testing)
--collect-all whisper	Pulls in Whisper's package data (tokenizer files, assets) that PyInstaller misses by default
--collect-all eventlet	Ensures eventlet's hub modules and internal data are bundled
--collect-data whisper	Explicitly grabs Whisper's non-Python data files
--hidden-import eventlet.hubs.*	The script dynamically injects/selects these hub modules at runtime, so PyInstaller's static analysis won't find them on its own
--hidden-import engineio.async_drivers.eventlet	python-socketio/engineio picks its eventlet driver dynamically
--hidden-import pyttsx3.drivers / pyttsx3.drivers.sapi5	pyttsx3 loads its TTS driver (SAPI5 on Windows) dynamically at runtime
3. Add files PyInstaller can't bundle automatically

After the build, go into dist/k10_hub/ and add, next to the exe:

ui/ folder — copy your entire web frontend folder in (the script looks for ../ui relative to the exe when the exe's own folder is named k10_hub, so keep the exe inside a k10_hub subfolder with ui/ as a sibling — see Directory structure below)
ffmpeg.exe — place it in the folder one level above the exe (the script auto-adds that path to PATH at runtime), unless ffmpeg is already installed system-wide
Whisper model cache — the base model downloads to %USERPROFILE%\.cache\whisper on first run; either let it download on first launch of the exe (needs internet), or pre-copy that cache folder onto the target machine to make it fully offline
Final packaged layout
project_root/
├── ffmpeg.exe
├── ui/
│   └── index.html, css, js, etc.
└── k10_hub/
    ├── k10_hub.exe
    └── (PyInstaller's bundled dependency files)
4. Run it

Just double-click k10_hub.exe (or run it from a terminal to see console output if you built with --console instead of --windowed).

Troubleshooting
Whisper fails to transcribe / "ffmpeg not found" — confirm ffmpeg is either on PATH or placed in the parent folder as described above.
"Ollama query failure" in the log — ensure ollama serve is running and that phi3:mini has been pulled.
No sound output / pyttsx3 errors — pyttsx3 relies on OS-level TTS engines (SAPI5 on Windows, NSSpeech on macOS, espeak on Linux). Install espeak (sudo apt install espeak) on Linux if TTS fails.
UI shows 404 — double check the ui folder location relative to the script, as described in Directory structure above.
