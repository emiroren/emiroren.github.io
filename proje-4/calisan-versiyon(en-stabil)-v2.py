#!/usr/bin/env python3
"""
Twitch Stream Translation Tool MVP - Fixed Version
Captures audio from Twitch streams, performs speech-to-text, and translates to Turkish
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import subprocess
import sys
import json
import queue
import requests
import os
from datetime import datetime

# Vosk import with error handling
try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Warning: Vosk not installed. Run: pip install vosk")

# FFmpeg: use system ffmpeg or imageio-ffmpeg (pip install imageio-ffmpeg)
try:
    import imageio_ffmpeg
    IMAGEIO_FFMPEG_AVAILABLE = True
except ImportError:
    IMAGEIO_FFMPEG_AVAILABLE = False


def get_ffmpeg_path():
    """Return path to ffmpeg: system PATH first, then imageio-ffmpeg if installed."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return 'ffmpeg'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    if IMAGEIO_FFMPEG_AVAILABLE:
        return imageio_ffmpeg.get_ffmpeg_exe()
    return None


class TwitchTranslator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Twitch Stream Translator")
        self.root.geometry("800x600")
        
        # Configuration
        self.deepl_api_key = "9fd9b299-6b39-4f47-8cb2-8e628b5f5748:fx"
        self.vosk_model_path = ""
        
        # Audio processing
        self.audio_queue = queue.Queue()
        self.is_capturing = False
        self.capture_process = None
        
        # Vosk setup
        self.vosk_model = None
        self.vosk_recognizer = None
        
        self.setup_gui()
    
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # URL input
        ttk.Label(main_frame, text="Twitch Stream URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.url_entry.insert(0, "https://www.twitch.tv/")  # Default value
        
        # API Key input
        ttk.Label(main_frame, text="DeepL API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_key_entry = ttk.Entry(main_frame, width=60, show="*")
        self.api_key_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Model path input
        ttk.Label(main_frame, text="Vosk Model Path:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_path_entry = ttk.Entry(main_frame, width=60)
        self.model_path_entry.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Translation", command=self.start_translation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_translation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Make sure streamlink and ffmpeg are installed")
        ttk.Label(main_frame, textvariable=self.status_var, wraplength=600).grid(row=4, column=0, columnspan=3, pady=5)
        
        # Subtitle display
        ttk.Label(main_frame, text="Live Subtitles (Turkish):").grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        
        self.subtitle_text = scrolledtext.ScrolledText(main_frame, height=15, wrap=tk.WORD, font=("Arial", 11))
        self.subtitle_text.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
    
    def setup_vosk(self):
        """Initialize Vosk speech recognition"""
        if not VOSK_AVAILABLE:
            self.log_message("Error: Vosk not installed! Run: pip install vosk")
            return False
            
        try:
            model_path = self.model_path_entry.get().strip()
            
            # Remove quotes if present
            model_path = model_path.strip('"').strip("'")
            
            self.log_message(f"Checking model path: {model_path}")
            print(f"Trying to load model from: {model_path}")
            
            if not model_path:
                self.log_message("Please provide a Vosk model path")
                return False
                
            if not os.path.exists(model_path):
                self.log_message(f"Path does not exist: {model_path}")
                print(f"Path does not exist: {model_path}")
                # List files in parent directory for debugging
                parent_dir = os.path.dirname(model_path)
                if os.path.exists(parent_dir):
                    print(f"Files in {parent_dir}:")
                    for item in os.listdir(parent_dir):
                        print(f"  - {item}")
                return False
            
            # Check if it's a directory
            if not os.path.isdir(model_path):
                self.log_message(f"Path is not a directory: {model_path}")
                return False
            
            # List contents of model directory
            print(f"Contents of model directory {model_path}:")
            for item in os.listdir(model_path):
                item_path = os.path.join(model_path, item)
                if os.path.isdir(item_path):
                    print(f"  [DIR] {item}")
                else:
                    print(f"  [FILE] {item}")
            
            # Check for minimum required directories/files
            # Different models have different structures, so we'll be more flexible
            has_am = os.path.exists(os.path.join(model_path, 'am'))
            has_graph = os.path.exists(os.path.join(model_path, 'graph'))
            has_conf = os.path.exists(os.path.join(model_path, 'conf'))
            
            print(f"Directory check - am: {has_am}, graph: {has_graph}, conf: {has_conf}")
            
            if not (has_am or has_graph):
                self.log_message("Model directory doesn't have required structure (missing 'am' or 'graph' folder)")
                self.log_message("Make sure you extracted the model correctly")
                return False
            
            self.log_message("Loading Vosk model... This may take a moment...")
            self.root.update()  # Update GUI
            
            # Try to load the model with error handling
            try:
                # Set Vosk log level to see more details
                vosk.SetLogLevel(0)  # 0 = most verbose
                
                self.vosk_model = vosk.Model(model_path)
                self.vosk_recognizer = vosk.KaldiRecognizer(self.vosk_model, 16000)
                
                self.log_message("✓ Vosk model loaded successfully!")
                return True
                
            except Exception as model_error:
                self.log_message(f"Failed to load model: {str(model_error)}")
                print(f"Model loading error details: {model_error}")
                return False
            
        except Exception as e:
            error_msg = f"Error in setup_vosk: {str(e)}"
            self.log_message(error_msg)
            print(f"Detailed error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def start_translation(self):
        """Start the translation process"""
        # Check if streamlink is installed (use same Python as this script)
        try:
            subprocess.run([sys.executable, '-m', 'streamlink', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showerror("Error", "Streamlink is not installed. Please install it first (e.g. py -m pip install streamlink).")
            return
        
        # Find ffmpeg (system or imageio-ffmpeg package)
        self.ffmpeg_exe = get_ffmpeg_path()
        if not self.ffmpeg_exe:
            messagebox.showerror("Error", "FFmpeg not found. Install it from https://ffmpeg.org and add to PATH, or run: py -m pip install imageio-ffmpeg")
            return
        
        # Validate inputs
        url = self.url_entry.get().strip()
        api_key = self.api_key_entry.get().strip()
        model_path = self.model_path_entry.get().strip()
        
        if not url or url == "https://www.twitch.tv/":
            messagebox.showerror("Error", "Please enter a valid Twitch stream URL")
            return
        
        if not api_key:
            response = messagebox.askyesno("Warning", "No DeepL API key provided. Continue without translation?")
            if not response:
                return
        
        if not model_path:
            messagebox.showerror("Error", "Please enter the Vosk model path")
            return
        
        self.deepl_api_key = api_key
        
        # Setup Vosk
        if not self.setup_vosk():
            return
        
        # Clear subtitle text area
        self.subtitle_text.delete("1.0", tk.END)
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_capturing = True
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self.capture_audio, args=(url,))
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        # Start processing thread
        self.process_thread = threading.Thread(target=self.process_audio)
        self.process_thread.daemon = True
        self.process_thread.start()
        
        self.log_message("Translation started...")
    
    def stop_translation(self):
        """Stop the translation process"""
        self.is_capturing = False
        
        if self.capture_process:
            try:
                self.capture_process.terminate()
                self.capture_process.wait(timeout=5)
            except:
                self.capture_process.kill()
            self.capture_process = None
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        self.log_message("Translation stopped")
    
    def capture_audio(self, url):
        """Capture audio from Twitch stream using streamlink and ffmpeg"""
        try:
            # Use streamlink to get the actual stream URL
            self.log_message("Getting stream URL...")
            
            # Try different quality options
            qualities = ['audio_only', 'worst', '160p', '360p']
            stream_url = None
            
            for quality in qualities:
                try:
                    streamlink_cmd = [sys.executable, '-m', 'streamlink', url, quality, '--stream-url']
                    result = subprocess.run(streamlink_cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        stream_url = result.stdout.strip()
                        self.log_message(f"Got stream with quality: {quality}")
                        break
                except:
                    continue
            
            if not stream_url:
                self.log_message("Could not get stream URL. Is the stream live?")
                return
            
            self.log_message("Stream URL obtained, starting audio capture...")
            
            # Use ffmpeg to capture and process audio
            ffmpeg_cmd = [
                self.ffmpeg_exe,
                '-i', stream_url,
                '-f', 'wav',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-loglevel', 'quiet',
                '-'
            ]
            
            self.capture_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )
            
            # Read audio data in chunks
            chunk_size = 1024 * 4  # 4KB chunks
            while self.is_capturing:
                audio_data = self.capture_process.stdout.read(chunk_size)
                if not audio_data:
                    break
                
                self.audio_queue.put(audio_data)
            
        except subprocess.TimeoutExpired:
            self.log_message("Stream capture timeout")
        except Exception as e:
            self.log_message(f"Audio capture error: {e}")
    
    def process_audio(self):
        """Process audio data for speech recognition"""
        audio_buffer = b''
        
        while self.is_capturing:
            try:
                # Get audio data from queue
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get(timeout=1)
                    audio_buffer += audio_data
                    
                    # Process when we have enough data
                    if len(audio_buffer) >= 16000 * 2 * 2:  # ~2 seconds of audio at 16kHz
                        self.recognize_speech(audio_buffer)
                        audio_buffer = b''
                
            except queue.Empty:
                continue
            except Exception as e:
                self.log_message(f"Audio processing error: {e}")
    
    def recognize_speech(self, audio_data):
        """Recognize speech using Vosk"""
        try:
            if self.vosk_recognizer and self.vosk_recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.vosk_recognizer.Result())
                text = result.get('text', '').strip()
                
                if text:
                    self.log_message(f"Recognized: {text}")
                    if self.deepl_api_key:
                        self.translate_text(text)
                    else:
                        # Just show the recognized text without translation
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        subtitle = f"[{timestamp}] {text}\n\n"
                        self.root.after(0, self.update_subtitles, subtitle)
            else:
                # Check partial results
                partial = json.loads(self.vosk_recognizer.PartialResult())
                partial_text = partial.get('partial', '').strip()
                if partial_text and len(partial_text) > 20:
                    self.root.after(0, self.status_var.set, f"Detecting: {partial_text[:50]}...")
            
        except Exception as e:
            self.log_message(f"Speech recognition error: {e}")
    
    def translate_text(self, text):
        """Translate text using DeepL API"""
        try:
            url = "https://api-free.deepl.com/v2/translate"
            
            data = {
                'auth_key': self.deepl_api_key,
                'text': text,
                'target_lang': 'TR'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            translated_text = result['translations'][0]['text']
            
            # Display only Turkish translation
            timestamp = datetime.now().strftime("%H:%M:%S")
            subtitle = f"[{timestamp}] {translated_text}\n\n"
            
            # Update GUI in main thread
            self.root.after(0, self.update_subtitles, subtitle)
            
        except Exception as e:
            # If translation fails, show original text with error note
            timestamp = datetime.now().strftime("%H:%M:%S")
            subtitle = f"[{timestamp}] {text} (Çeviri başarısız)\n\n"
            self.root.after(0, self.update_subtitles, subtitle)
            self.log_message(f"Translation error: {e}")
    
    def update_subtitles(self, subtitle):
        """Update subtitle display"""
        self.subtitle_text.insert(tk.END, subtitle)
        self.subtitle_text.see(tk.END)
        
        # Keep only last 100 lines to prevent memory issues
        lines = self.subtitle_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            # Remove first 20 lines when limit is reached
            for _ in range(20):
                self.subtitle_text.delete("1.0", "2.0")
    
    def log_message(self, message):
        """Log status message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        
        # Update status in main thread
        self.root.after(0, self.status_var.set, message)
        print(log_msg)
    
    def run(self):
        """Start the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_capturing:
            self.stop_translation()
        
        self.root.destroy()

if __name__ == "__main__":
    app = TwitchTranslator()
    app.run()