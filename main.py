import io
import os
import time

from datetime import datetime
from TTS.api import TTS
from pydub import AudioSegment
from pydub.generators import Sine
from ntp_utils import get_uk_time
from constants import number_words, sentences

# Every 10 seconds, the voice announces the time in the UK
SPEAKING_INTERVAL = 10
BEEPS = 3
SPEAKER = "p312"
OUTPUT = "/tmp/audio.pcm"

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
    intro = AudioSegment.from_wav("sentences/sequence_start.wav")
    beeps = AudioSegment.from_wav("beep_leap.wav" if leap else "beep.wav")
    hour = AudioSegment.from_wav(f"numbers/{uk_time.hour}.wav")
    minute = AudioSegment.from_wav(f"numbers/{uk_time.minute}.wav")
    second = AudioSegment.from_wav(f"numbers/{uk_time.second}.wav")

    parts = [beeps, intro, hour]

    if uk_time.minute == 0:
        parts += [
            AudioSegment.from_wav("sentences/oclock.wav"),
            AudioSegment.from_wav("sentences/precisely.wav")]
    else:
        parts += [
            minute,
            AudioSegment.from_wav("sentences/and.wav"),
            second,
            AudioSegment.from_wav("sentences/seconds.wav"),
        ]

    clip = sum(parts)

    return clip.set_frame_rate(22050).set_channels(1)


if __name__ == '__main__':
    # Generate beeps on application start
    make_beep_sequence("beep.wav")
    make_beep_sequence("beep_leap.wav", leap=True)

    # Initialise TTS
    tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False, gpu=False)

    # Create numbers
    os.makedirs("numbers", exist_ok=True)
    numbers = [str(i) for i in range(0, 61)]
    for i in range(0, 61):
        numbers[i] = tts.tts_to_file(text=number_words[i], speaker=SPEAKER, file_path=f"numbers/{i}.wav")

    # Create sentences
    os.makedirs("sentences", exist_ok=True)
    for key, value in sentences.items():
        sentences[key] = tts.tts_to_file(text=value, speaker=SPEAKER, file_path=f"sentences/{key}.wav")

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
