import importlib
import io
import os
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


if __name__ == '__main__':
    # Generate beeps on application start
    make_beep_sequence("beep.wav")
    make_beep_sequence("beep_leap.wav", leap=True)

    # Create path for stream
    if not os.path.exists(OUTPUT):
        os.mkfifo(OUTPUT)

    # Create pipe
    fifo = open(OUTPUT, "wb")

    while True:
        start = time.time()

        uk_time, leap = get_uk_time()
        audio = create_time(uk_time, leap)

        print(f"[{uk_time.strftime('%H:%M:%S')}] Streaming...")

        # Export the spoken time as raw PCM
        buf = io.BytesIO()
        audio.export(buf, format="raw")
        fifo.write(buf.getvalue())
        fifo.flush()

        elapsed = time.time() - start
        delay = SPEAKING_INTERVAL - (elapsed % SPEAKING_INTERVAL)
        if delay < 0:
            delay = 0
        time.sleep(delay)
