# This is a sample Python script.
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import time
import ntplib
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from TTS.api import TTS
from pydub import AudioSegment
from pydub.generators import Sine

# Every 10 seconds, the voice announces the time in the UK
SPEAKING_INTERVAL = 10
BEEPS = 3

# Get the current time in the UK
def get_uk_time():
    ntp = retrieve_ntp_time()
    ntp_utc = datetime.fromtimestamp(ntp.tx_time, tz=timezone.utc)

    uk_time = ntp_utc.astimezone(ZoneInfo('Europe/London'))
    return uk_time


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

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Generate beeps on application start
    make_beep_sequence("beep.wav")
    make_beep_sequence("beep_leap.wav", leap=True)

    while True:
        now = datetime.now()

        # Generate beeps

        sleep_secs = SPEAKING_INTERVAL - (time.time() % SPEAKING_INTERVAL)
        time.sleep(sleep_secs)


