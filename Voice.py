import os
import sys
import threading
import asyncio
import pygame
import speech_recognition as sr
import edge_tts
import re
from faster_whisper import WhisperModel


def add_nvidia_paths():
    try:
        site_packages = next(p for p in sys.path if 'site-packages' in p)
        paths_to_add = [
            os.path.join(site_packages, 'nvidia', 'cublas', 'bin'),
            os.path.join(site_packages, 'nvidia', 'cudnn', 'bin')
        ]
        for p in paths_to_add:
            if os.path.exists(p):
                try:
                    os.add_dll_directory(p)
                except:
                    pass
                os.environ['PATH'] = p + os.pathsep + os.environ['PATH']
    except Exception:
        pass

if os.name == 'nt':
    add_nvidia_paths()

# fast modell
# medium is kinda 2-3x faster than large-v3 but understands swedish almost as good.
WHISPER_SIZE = "medium" 
DEVICE = "cuda"

print(f"Laddar Whisper ({WHISPER_SIZE}) på {DEVICE}...", flush=True)

try:
    # float16 is standard for rtx cards
    whisper_model = WhisperModel(WHISPER_SIZE, device=DEVICE, compute_type="float16")
    print("Whisper är redo (High Performance Mode)!", flush=True)
except Exception:
    whisper_model = WhisperModel(WHISPER_SIZE, device="cpu", compute_type="int8")

# sound initialization
try:
    pygame.mixer.init()
except Exception:
    pass

def play_audio(filename):
    try:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
    except Exception as e:
        print(f"Ljudfel: {e}")

async def generate_speech_sentence(text, index):
    if not text.strip(): return
    output_file = f"temp_sent_{index}.mp3"
    # 
    communicate = edge_tts.Communicate(text, "sv-SE-SofieNeural", rate="+10%")
    try:
        await communicate.save(output_file)
        if os.path.exists(output_file):
            play_audio(output_file)
            try: os.remove(output_file)
            except: pass
    except: pass

async def generate_speech(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            await generate_speech_sentence(sentence, i)

def speak(text):
    def _run():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate_speech(text))
            loop.close()
        except: pass
    threading.Thread(target=_run).start()

def listen(recognizer=None, source=None, timeout=None):
    if recognizer: r = recognizer
    else: r = sr.Recognizer()

    
    # optimize clip of silence
    r.energy_threshold = 300
    r.pause_threshold = 0.6  
    r.dynamic_energy_threshold = False 

    def _listen_loop(src):
        print("Lyssnar...", flush=True)
        try:
            audio = r.listen(src, timeout=timeout, phrase_time_limit=None)
            
            temp_wav = "temp_listen.wav"
            with open(temp_wav, "wb") as f:
                f.write(audio.get_wav_data())

            
            # optimize beam size = 1 for faster results
            # this makes it not "think" as much about the translation, which saves a lot of time.
            segments, info = whisper_model.transcribe(temp_wav, language="sv", beam_size=1)
            text = "".join([segment.text for segment in segments]).strip()
            
            try: os.remove(temp_wav)
            except: pass

            if text:
                print(f"Hörde: '{text}'", flush=True)
            return text

        except Exception:
            return None

    if source: return _listen_loop(source)
    else:
        with sr.Microphone() as source:
            if not recognizer: r.adjust_for_ambient_noise(source, duration=0.5)
            return _listen_loop(source)