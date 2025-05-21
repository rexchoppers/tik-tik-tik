import importlib
import io
import os
import queue
import threading
import time

from TTS.api import TTS
from pydub import AudioSegment
from pydub.generators import Sine
from ntp_utils import get_uk_time

# Every 10 seconds, the voice announces the time in the UK
SPEAKING_INTERVAL = 10
BEEPS = 3
OUTPUT = "/tmp/audio.pcm"
LANGUAGE = os.getenv("LANGUAGE", "en")
# LANGUAGE = os.getenv("LANGUAGE", "el")

CONFIG = importlib.import_module(f"config.{LANGUAGE}")

audio_queue = queue.Queue()

print(CONFIG)

def make_beep_sequence(filename: str, leap: bool = False):
    beep = Sine(1000).to_audio_segment(duration=250).apply_gain(-3)
    silence = AudioSegment.silent(duration=750)

    sequence = AudioSegment.silent(duration=0)
    for i in range(BEEPS):
        sequence += beep

        beep_count = i + 1

        if i < BEEPS - 1:
            # Check if leap and if it's between beep 2 and 3
            if leap and (beep_count == 2 or beep_count == 3):
                # Add a longer silence
                sequence += AudioSegment.silent(duration=1000)
            else:
                # Add a normal silence
                sequence += silence

    sequence.export(filename, format="wav")

def create_time(uk_time, leap):
    beeps = AudioSegment.from_wav("beep_leap.wav" if leap else "beep.wav")

    if uk_time.minute == 0:
        sentence = CONFIG.SENTENCES["sequence_start"] + " " + CONFIG.NUMBER_WORDS[uk_time.hour] + " " + CONFIG.SENTENCES["oclock"] + " " + CONFIG.SENTENCES["precisely"]
    else:
        sentence = CONFIG.SENTENCES["sequence_start"] + " " + CONFIG.NUMBER_WORDS[uk_time.hour] + ", " + CONFIG.NUMBER_WORDS[uk_time.minute] +  ", " + CONFIG.SENTENCES["and"] + " " + CONFIG.NUMBER_WORDS[uk_time.second] + " " + CONFIG.SENTENCES["seconds"]

    # Generate the sentence using TTS
    model_args = {}

    # Check if the model has a speaker argument
    if CONFIG.SPEAKER:
        model_args["speaker"] = CONFIG.SPEAKER

    tts = TTS(
        model_name=CONFIG.MODEL
    )

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
        uk_time, leap = get_uk_time()
        print(f"[{uk_time.strftime('%H:%M:%S')}] Generating audio...")

        audio = create_time(uk_time, leap)
        audio_queue.put(audio)

        time.sleep(SPEAKING_INTERVAL)

def streaming_loop():
    if not os.path.exists(OUTPUT):
        os.mkfifo(OUTPUT)

    fifo = open(OUTPUT, "wb")

    current_audio = None
    position = 0

    SILENCE_CHUNK_MS = 200  # How big each silent chunk is
    SAMPLE_RATE = 22050
    CHANNELS = 1
    SAMPLE_WIDTH = 2  # 16-bit audio => 2 bytes

    SILENCE_CHUNK = AudioSegment.silent(duration=SILENCE_CHUNK_MS).set_frame_rate(SAMPLE_RATE).set_channels(CHANNELS)

    while True:
        if current_audio is None or position >= len(current_audio):
            # Try to get next clip
            try:
                current_audio = audio_queue.get(timeout=0.1)
                position = 0
            except queue.Empty:
                current_audio = SILENCE_CHUNK
                position = 0

        # Slice the audio into small chunk
        chunk = current_audio[position:position + SILENCE_CHUNK_MS]
        buf = io.BytesIO()
        chunk.export(buf, format="raw")
        fifo.write(buf.getvalue())
        fifo.flush()

        position += SILENCE_CHUNK_MS
        time.sleep(SILENCE_CHUNK_MS / 1000.0)

if __name__ == '__main__':
    # Generate beeps on application start
    make_beep_sequence("beep.wav")
    make_beep_sequence("beep_leap.wav", leap=True)

    threading.Thread(target=generator_loop, daemon=True).start()
    streaming_loop()