import pyaudio
import wave
import pyttsx3
import whisper
import ollama
import threading
import time
import keyboard

engine = pyttsx3.init()

# Initialize Whisper model (force CPU usage and FP32)
whisper_model = whisper.load_model("base", device="cpu")

# Initialize PyAudio
p = pyaudio.PyAudio()

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Global variables
is_recording = False
audio_frames = []

# System prompt
system_prompt = """You are administering a trivia night for a User. Make the questions difficult and unique and scale the difficulty of the questions to the correctness of the answers.

Conversation history:
Assistant: Hi.
"""

def record_audio():
    global is_recording, audio_frames
    
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("Press 'r' to start/stop recording")
    
    while True:
        if is_recording:
            data = stream.read(CHUNK)
            audio_frames.append(data)
        
        if keyboard.is_pressed('r'):
            if not is_recording:
                is_recording = True
                audio_frames = []
                print("Recording started")
            else:
                is_recording = False
                print("Recording stopped")
                process_audio()
            time.sleep(0.2)  # Debounce

def process_audio():
    global audio_frames
    global system_prompt
    
    if not audio_frames:
        print("No audio recorded")
        return

    # Save the recorded audio to a temporary file
    wf = wave.open("temp.wav", "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(audio_frames))
    wf.close()
    
    # Transcribe the audio using Whisper
    result = whisper_model.transcribe("temp.wav")
    transcription = result["text"]
    print(f"You said: {transcription}")
    
    # Generate a response using Llama 3
    prompt = f"{system_prompt}\nUser: {transcription}\nAssistant:"
    response = ollama.generate(model='llama3', prompt=prompt)
    engine.say(response['response'], 'test')
    print(f"Agent: {response['response']}\n\n")

    system_prompt = system_prompt + prompt + response['response']
    print(f"System: {system_prompt}")
    engine.runAndWait()


def on_end(name, completed):
    global count
    if name == 'done':
       engine.endLoop()
    else:
        record_audio()
        process_audio()

# voices = engine.getProperty('voices')
# print(voices)
# for voice in voices:
#    engine.setProperty('voice', voice.id)
#    print("id",voice.id)
#    engine.say('The quick brown fox jumped over the lazy dog.')
# engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0')

engine.connect('finished-utterance', on_end)
engine.say('Hi there.')
engine.startLoop()