# This is a sample Python script.
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import ntplib
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from TTS.api import TTS

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.

# Get the current time in the UK
def get_uk_time():
    ntp = retrieve_ntp_time()
    uk_time = ntp.astimezone(ZoneInfo('Europe/London'))
    return uk_time


# Return NTP as UTC
def retrieve_ntp_time():
    ntp_client = ntplib.NTPClient()

    response = ntp_client.request('uk.pool.ntp.org', version=3)
    return datetime.fromtimestamp(response.tx_time, tz=timezone.utc)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print(get_uk_time())
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

# tts --model_name "tts_models/uk/mai/vits" --download
