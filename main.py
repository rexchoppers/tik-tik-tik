# This is a sample Python script.
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import time
import ntplib
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from TTS.api import TTS

# Every 10 seconds, the voice announces the time in the UK
SPEAKING_INTERVAL = 10

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


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    while True:
        now = datetime.now()

        # Generate beeps

        sleep_secs = SPEAKING_INTERVAL - (time.time() % SPEAKING_INTERVAL)
        time.sleep(sleep_secs)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/

# tts --model_name "tts_models/uk/mai/vits" --download
