import ntplib
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# NTP configuration
ntp_sync_interval = 300
last_ntp_sync = 0
ntp_offset = 0
leap_second_flag = False

def retrieve_ntp_time():
    """
    Retrieve time from NTP server
    """
    ntp_client = ntplib.NTPClient()
    response = ntp_client.request('uk.pool.ntp.org', version=3)
    return response

def sync_ntp():
    """
    Synchronize with NTP server and return offset and leap second flag
    """
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
    
    return ntp_offset, leap_second_flag

def get_uk_time():
    """
    Get the current time in the UK, synchronized with NTP
    """
    ntp_offset, leap = sync_ntp()
    
    now = time.time()
    corrected_time = datetime.fromtimestamp(now + ntp_offset, tz=timezone.utc)
    uk_time = corrected_time.astimezone(ZoneInfo('Europe/London'))
    
    return uk_time, leap