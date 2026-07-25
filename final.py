import os
import sys
from types import ModuleType

# 1. Force standard fallback transport loops for cross-laptop network configurations
os.environ['EVENTLET_HUB'] = 'selects'

# 2. Break circular import paths before initializing underlying sockets
try:
    import eventlet.patcher
except ImportError:
    pass

# 3. Inject dummy tracking references to ignore non-Windows OS dependencies
for platform_hub in ['eventlet.hubs.epolls', 'eventlet.hubs.kqueue', 'eventlet.hubs.poll']:
    if platform_hub not in sys.modules:
        sys.modules[platform_hub] = ModuleType(platform_hub)

import eventlet
eventlet.hubs.use_hub("selects")
eventlet.monkey_patch()

if sys.platform == "win32":
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Local.LLM.ServerCore.2026")

import socket
import whisper
import ollama
import pyttsx3
import wave
import socketio
import tkinter as tk
from tkinter import scrolledtext

K10_PORT = 6001 
DISCOVERY_PORT = 5005

if not os.path.exists('uploads'): 
    os.makedirs('uploads')

# --- PORTABLE STATIC WEB ASSETS MIDDLEWARE HOSTING ---
# This looks for the 'ui' folder right outside your k10_hub executable folder block
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
UI_DIR = os.path.join(BASE_DIR, '..', 'ui') if os.path.basename(BASE_DIR) == 'k10_hub' else os.path.join(BASE_DIR, 'ui')
UI_DIR = os.path.abspath(UI_DIR)

def standalone_static_router(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    if path == '/' or path == '':
        path = '/index.html'
        
    file_path = os.path.join(UI_DIR, path.lstrip('/'))
    
    # Block local storage path traversal attacks
    if not os.path.commonpath([UI_DIR, os.path.abspath(file_path)]) == UI_DIR:
        start_response('403 Forbidden', [('Content-Type', 'text/plain')])
        return [b'Forbidden']

    if os.path.exists(file_path) and os.path.isfile(file_path):
        mime_type = 'text/html'
        if file_path.endswith('.js'): mime_type = 'application/javascript'
        elif file_path.endswith('.css'): mime_type = 'text/css'
        elif file_path.endswith('.png'): mime_type = 'image/png'
        elif file_path.endswith('.svg'): mime_type = 'image/svg+xml'
        
        start_response('200 OK', [('Content-Type', mime_type)])
        with open(file_path, 'rb') as f:
            return [f.read()]
            
    # Fallback default route map for Vite single page application frameworks
    spa_fallback = os.path.join(UI_DIR, 'index.html')
    if os.path.exists(spa_fallback):
        start_response('200 OK', [('Content-Type', 'text/html')])
        with open(spa_fallback, 'rb') as f:
            return [f.read()]
            
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found']

# --- COMBINED SYSTEM WSGI INSTANCE SETUP ---
sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio, standalone_static_router)

def log_to_gui(message, msg_type="info"):
    formatted_msg = f"[{msg_type.upper()}] {message}\n"
    try:
        log_display.insert(tk.END, formatted_msg)
        log_display.see(tk.END)
    except:
        pass
        
    try:
        sio.emit('terminal_log', {'text': message, 'type': msg_type})
        eventlet.sleep(0)
    except:
        pass

def update_web_status(status_state):
    try:
        sio.emit('status_change', status_state)
        eventlet.sleep(0)  
    except:
        pass

def push_web_chat(user_str, ai_str):
    try:
        sio.emit('new_chat', {'user': user_str, 'ai': ai_str})
        eventlet.sleep(0)  
    except:
        pass

# --- COOPERATIVE UDP BEACON LOOP ---
def ip_discovery_broadcast():
    broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    log_to_gui("Auto-Discovery Broadcast active on network...", "beacon")
    while True:
        try:
            s_temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s_temp.connect(("8.8.8.8", 80))
            local_ip = s_temp.getsockname()[0]
            s_temp.close()
            
            ip_parts = local_ip.split('.')
            ip_parts[3] = '255'
            subnet_broadcast = '.'.join(ip_parts)
            
            broadcast_sock.sendto(b"CHIMERA_SERVER_BEACON", (subnet_broadcast, DISCOVERY_PORT))
        except Exception:
            try:
                broadcast_sock.sendto(b"CHIMERA_SERVER_BEACON", ('<broadcast>', DISCOVERY_PORT))
            except:
                pass
        eventlet.sleep(3.0)

# --- MAIN HARDWARE ENGINE LOOP ---
def hardware_pipeline_loop():
    # Dynamically inject your local ffmpeg path so Whisper can see it without system environment vars
    current_exec_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    root_workspace = os.path.abspath(os.path.join(current_exec_dir, '..'))
    if root_workspace not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + root_workspace

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 6000))
    server.listen(1)
    
    log_to_gui("Awaiting incoming voice frames from K10 on port 6000...", "system")
    SILENCE_HALLUCINATIONS = ["oh my god", "hmm", "maybe not", "thank you", "you", "bye", "hello", "screaming", "whispering"]
    
    while True:
        try:
            update_web_status("IDLE")
            conn, addr = server.accept()
            captured_k10_ip = addr[0]
            
            update_web_status("RECEIVING")
            log_to_gui(f"--- Phase 1: Voice block incoming from K10 node at {captured_k10_ip} ---", "process")
            
            conn.settimeout(1.0)
            file_path = os.path.join('uploads', 'input.wav')
            with open(file_path, 'wb') as f:
                while True:
                    try:
                        data = conn.recv(8192)
                        if not data: break
                        f.write(data)
                    except socket.timeout:
                        break
            conn.close()
            
            log_to_gui("Transcribing audio stream locally using Whisper...", "info")
            user_text = ""
            
            if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
                try:
                    result = stt_model.transcribe(file_path, fp16=False, language="en")
                    user_text = result["text"].strip()
                    log_to_gui(f"Whisper output evaluated: '{user_text}'", "success")
                except Exception as e:
                    log_to_gui(f"⚠️ Whisper processing mistake: {e}", "error")
            
            clean_check = user_text.lower().replace(".", "").replace(",", "").strip()
            if not clean_check or clean_check in SILENCE_HALLUCINATIONS or len(clean_check) <= 2:
                log_to_gui("⚠️ Anomaly filtered out (static noise envelope). Resetting loop.", "error")
                try:
                    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_sock.settimeout(2.0)
                    client_sock.connect((captured_k10_ip, K10_PORT))
                    client_sock.sendall(b"|||") 
                    client_sock.close()
                except:
                    pass
                continue

            update_web_status("THINKING")
            log_to_gui(f"Passing query payload to local Ollama instance (phi3:mini)...", "process")
            ai_text = "வணக்கம்" 
            
            try:
                response = ollama.chat(model='phi3:mini', messages=[
                    {'role': 'system', 'content': 'You are a concise voice assistant. Give an extremely short answer. Maximum 6 words total.'},
                    {'role': 'user', 'content': user_text},
                ])
                raw_ai_text = response['message']['content'].strip()
                words_array = raw_ai_text.split(' ')
                ai_text = " ".join(words_array[:7]) + "." if len(words_array) > 7 else raw_ai_text
                log_to_gui(f"Ollama string output validated: '{ai_text}'", "success")
            except Exception as e:
                log_to_gui(f"Ollama query failure: {e}", "error")

            update_web_status("SPEAKING")
            log_to_gui("Generating audio track container using native system TTS strings...", "info")
            
            final_wav = os.path.join('uploads', 'response.wav') 
            temp_tts_out = os.path.join('uploads', 'temp_out.wav')
            
            try:
                if os.path.exists(final_wav): os.remove(final_wav)
                if os.path.exists(temp_tts_out): os.remove(temp_tts_out)
                
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                if len(voices) >= 3: engine.setProperty('voice', voices[2].id)
                engine.setProperty('rate', 145) 
                engine.save_to_file(ai_text, temp_tts_out)
                engine.runAndWait() 
                del engine
                
                if os.path.exists(temp_tts_out) and os.path.getsize(temp_tts_out) > 0:
                    with wave.open(temp_tts_out, 'rb') as wav_in:
                        audio_frames = wav_in.readframes(wav_in.getnframes())
                    with wave.open(final_wav, 'wb') as wav_out:
                        wav_out.setnchannels(1)      
                        wav_out.setsampwidth(2)      
                        wav_out.setframerate(16000)  
                        wav_out.writeframes(audio_frames)
                    os.remove(temp_tts_out)
                    log_to_gui("Audio container generation processed safely.", "success")
            except Exception as e:
                log_to_gui(f"Audio mapping mismatch: {e}", "error")
            
            push_web_chat(user_text, ai_text)
            
            log_to_gui(f"Phase 2: Connecting back down to Unihiker target node at {captured_k10_ip}...", "process")
            connected = False
            retries = 3
            while retries > 0 and not connected:
                try:
                    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_sock.settimeout(4.0)
                    client_sock.connect((captured_k10_ip, K10_PORT))
                    
                    text_payload = f"{user_text}|||{ai_text}"
                    encoded_payload = text_payload.encode('utf-8')
                    padded_payload = encoded_payload + b' ' * (512 - len(encoded_payload)) if len(encoded_payload) < 512 else encoded_payload[:512]
                    
                    client_sock.sendall(padded_payload)
                    if os.path.exists(final_wav):
                        with open(final_wav, 'rb') as f:
                            client_sock.sendall(f.read())
                    client_sock.close()
                    log_to_gui("Text frames and audio signals safely pushed to K10 hardware layer!", "success")
                    connected = True
                except:
                    retries -= 1
                    eventlet.sleep(0.5)

        except Exception as glitch:
            log_to_gui(f"Core execution recovery warning trigger: {glitch}", "error")
            eventlet.sleep(1)

def start_servers():
    log_to_gui("Loading Whisper model into RAM... please wait.", "system")
    global stt_model
    stt_model = whisper.load_model("base")
    log_to_gui("✅ Whisper Model Loaded Successfully!", "system")
    
    eventlet.spawn(ip_discovery_broadcast)
    eventlet.spawn(hardware_pipeline_loop)
    
    # Starts the unified WSGI Server on Port 5000 hosting both the UI files and sockets natively
    eventlet.spawn(lambda: eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app, log_output=False))

# --- DESIGN SOFTWARE GUI DESKTOP WINDOW ---
window = tk.Tk()
window.title("🤖 Local LLM Server Center")
window.geometry("700x450")
window.configure(bg="#121214")

header = tk.Label(window, text="LOCAL LLM DISPLAY", font=("Helvetica", 14, "bold"), bg="#121214", fg="#00FFFF")
header.pack(pady=10)

log_display = scrolledtext.ScrolledText(window, font=("Consolas", 10), bg="#1E1E24", fg="#A6ADC8", wrap=tk.WORD, width=80, height=18)
log_display.pack(padx=15, pady=10)

def process_gui_tasks():
    eventlet.sleep(0.03)
    window.after(30, process_gui_tasks)

window.after(500, start_servers)
window.after(550, process_gui_tasks)
window.mainloop()