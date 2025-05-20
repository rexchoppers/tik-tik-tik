import io
import os
import time
import ntplib

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from TTS.api import TTS
from pydub import AudioSegment
from pydub.generators import Sine

number_words = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
    10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen",
    17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty", 21: "twenty one", 22: "twenty two",
    23: "twenty three", 24: "twenty four", 25: "twenty five", 26: "twenty six", 27: "twenty seven",
    28: "twenty eight", 29: "twenty nine", 30: "thirty", 31: "thirty one", 32: "thirty two", 33: "thirty three",
    34: "thirty four", 35: "thirty five", 36: "thirty six", 37: "thirty seven", 38: "thirty eight",
    39: "thirty nine", 40: "forty", 41: "forty one", 42: "forty two", 43: "forty three", 44: "forty four",
    45: "forty five", 46: "forty six", 47: "forty seven", 48: "forty eight", 49: "forty nine",
    50: "fifty", 51: "fifty one", 52: "fifty two", 53: "fifty three", 54: "fifty four", 55: "fifty five",
    56: "fifty six", 57: "fifty seven", 58: "fifty eight", 59: "fifty nine", 60: "sixty"
}

# Every 10 seconds, the voice announces the time in the UK
SPEAKING_INTERVAL = 10
BEEPS = 3
SPEAKER = "p312"
OUTPUT = "/tmp/audio.pcm"

ntp_sync_interval = 300
last_ntp_sync = 0
ntp_offset = 0
leap_second_flag = False


# Get the current time in the UK
def get_uk_time():
    global last_ntp_sync, ntp_offset, leap_second_flag

    now = time.time()
    if now - last_ntp_sync > ntp_sync_interval:
        try:
            ntp = retrieve_ntp_time()
            ntp_offset = ntp.tx_time - now
            leap_second_flag = ntp.leap > 1
            last_ntp_sync = now
            print(f"NTP synced. Offset: {ntp_offset:.6f}s, Leap: {leap_second_flag}")
        except Exception as e:
            print(f"[WARN] NTP sync failed: {e}")

    corrected_time = datetime.fromtimestamp(now + ntp_offset, tz=timezone.utc)
    uk_time = corrected_time.astimezone(ZoneInfo('Europe/London'))
    return uk_time, leap_second_flag


# Return NTP as UTC
def retrieve_ntp_time():
    ntp_client = ntplib.NTPClient()

    response = ntp_client.request('uk.pool.ntp.org', version=3)
    return response


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
    sentences = {
        "sequence_start": "At the third stroke, the time will be",
        "seconds": "seconds",
        "precisely": "precisely",
        "oclock": "o'clock",
        "and": "and"
    }
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
