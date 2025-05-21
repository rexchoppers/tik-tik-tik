import importlib
import io
import os
import queue
import threading
import time
import subprocess

from TTS.api import TTS
from pydub import AudioSegment
from pydub.generators import Sine
from ntp_utils import get_uk_time

# Every 10 seconds, the voice announces the time in the UK
SPEAKING_INTERVAL = 10
BEEPS = 3
LANGUAGE = os.getenv("LANGUAGE", "en")
# LANGUAGE = os.getenv("LANGUAGE", "el")

CONFIG = importlib.import_module(f"config.{LANGUAGE}")

audio_queue = queue.Queue()

tts = TTS(
    model_name=CONFIG.MODEL
)

print(CONFIG)

def make_beep_sequence(filename: str, leap: bool = False):
    beep = Sine(1000).to_audio_segment(duration=250).apply_gain(-3)
    silence = AudioSegment.silent(duration=750)

    sequence = AudioSegment.silent(duration=0)
    for i in range(BEEPS):
        sequence += beep

        beep_count = i + 1

        if i < BEEPS - 1:
            if leap and (beep_count == 2 or beep_count == 3):
                sequence += AudioSegment.silent(duration=1000)
            else:
                sequence += silence

    sequence.export(filename, format="wav")

def create_time(uk_time, leap):
    beeps = AudioSegment.from_wav("beep_leap.wav" if leap else "beep.wav")

    if uk_time.minute == 0:
        sentence = CONFIG.SENTENCES["sequence_start"] + " " + CONFIG.NUMBER_WORDS[uk_time.hour] + " " + CONFIG.SENTENCES["oclock"] + " " + CONFIG.SENTENCES["precisely"]
    else:
        sentence = CONFIG.SENTENCES["sequence_start"] + " " + CONFIG.NUMBER_WORDS[uk_time.hour] + ", " + CONFIG.NUMBER_WORDS[uk_time.minute] +  ", " + CONFIG.SENTENCES["and"] + " " + CONFIG.NUMBER_WORDS[uk_time.second] + " " + CONFIG.SENTENCES["seconds"]

    model_args = {}
    if CONFIG.SPEAKER:
        model_args["speaker"] = CONFIG.SPEAKER

    tts.tts_to_file(
        text=sentence,
        file_path="temp.wav",
        **model_args
    )

    sentence = AudioSegment.from_wav("temp.wav")
    parts = [beeps, sentence]
    clip = sum(parts)

    return clip.set_frame_rate(22050).set_channels(1)

def generator_loop():
    while True:
        # Work out the next interval time (e.g. 10s ahead from last multiple)
        now = time.time()
        next_time = ((now // SPEAKING_INTERVAL) + 1) * SPEAKING_INTERVAL
        delay = next_time - now

        # Wait just until the next boundary
        time.sleep(delay)

        # Once it's exact, get the time
        uk_time, leap = get_uk_time()

        print(f"[{uk_time.strftime('%H:%M:%S')}] Generating audio for {SPEAKING_INTERVAL}s mark...")

        audio = create_time(uk_time, leap)
        audio_queue.put((audio, next_time))  # Push both audio and when it should start


def streaming_loop():
    SAMPLE_RATE = 22050
    CHANNELS = 1
    SILENCE_CHUNK_MS = 200
    SILENCE_CHUNK = AudioSegment.silent(duration=SILENCE_CHUNK_MS).set_frame_rate(SAMPLE_RATE).set_channels(CHANNELS)

    # Launch ffmpeg to stream to Icecast
    ffmpeg = subprocess.Popen([
        "ffmpeg",
        "-f", "s16le",
        "-ar", str(SAMPLE_RATE),
        "-ac", str(CHANNELS),
        "-i", "pipe:0",
        "-acodec", "libmp3lame",
        "-b:a", "128k",
        "-content_type", "audio/mpeg",
        "-legacy_icecast", "1",
        "-f", "mp3",
        "icecast://source:password@localhost:8000/clock"
    ], stdin=subprocess.PIPE)

    current_audio = None
    position = 0

    while True:
        if current_audio is None or position >= len(current_audio):
            try:
                # Get audio and its scheduled play time
                audio_data, scheduled_time = audio_queue.get(timeout=0.1)

                # Check if we need to skip this audio because it's too old
                now = time.time()
                if now > scheduled_time + SPEAKING_INTERVAL:
                    print(f"Skipping outdated audio scheduled for {scheduled_time:.1f}, current time is {now:.1f}")
                    continue

                # Wait until it's time to play this audio
                wait_time = scheduled_time - now

                print("Wait time " + str(wait_time))

                if wait_time > 0:
                    time.sleep(wait_time)

                current_audio = audio_data
                position = 0
                print(f"Playing audio scheduled for {scheduled_time:.1f}")
            except queue.Empty:
                current_audio = SILENCE_CHUNK
                position = 0

        chunk = current_audio[position:position + SILENCE_CHUNK_MS]
        buf = io.BytesIO()
        chunk.export(buf, format="raw")
        ffmpeg.stdin.write(buf.getvalue())
        ffmpeg.stdin.flush()

        position += SILENCE_CHUNK_MS
        time.sleep(SILENCE_CHUNK_MS / 1000.0)

if __name__ == '__main__':
    make_beep_sequence("beep.wav")
    make_beep_sequence("beep_leap.wav", leap=True)

    threading.Thread(target=generator_loop, daemon=True).start()
    streaming_loop()