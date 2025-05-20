# Tik-Tik-Tik

A speaking clock application that announces the current UK time with precise NTP synchronization, inspired by the traditional telephone speaking clock service.

## Description

Tik-Tik-Tik is a Python application that:
- Synchronizes with NTP servers to get accurate time
- Announces the current UK time using text-to-speech
- Plays a sequence of beeps before each announcement (similar to the traditional speaking clock)
- Handles leap seconds
- Outputs audio to a PCM file that can be streamed via Icecast

The application is designed to mimic the traditional speaking clock service with phrases like "At the third stroke, the time will be..." followed by the current time.

## Features

- Accurate time synchronization using NTP
- Text-to-speech time announcements using the VCTK model
- Special handling for leap seconds
- Configurable announcement intervals
- Audio streaming capability via Icecast
- Runs as a continuous service

## Installation

### Prerequisites

- Python 3.11 or higher
- Docker

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/rexchoppers/tik-tik-tik.git
   cd tik-tik-tik
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Start the Icecast server (optional, for streaming):
   ```
   docker-compose up -d
   ```

## Usage

Run the main script to start the speaking clock:

```
python main.py
```

The application will:
1. Generate necessary audio files on first run
2. Sync with NTP servers to get accurate time
3. Announce the time at regular intervals (default: every 10 seconds)
4. Output audio to `/tmp/audio.pcm`

### Configuration

You can modify the following variables in `main.py` to customize the behavior:

- `SPEAKING_INTERVAL`: Time between announcements in seconds (default: 10)
- `BEEPS`: Number of beeps before each announcement (default: 3)
- `SPEAKER`: Voice model to use (default: "p312" from VCTK)
- `OUTPUT`: Output file path (default: "/tmp/audio.pcm")

### Streaming

The application outputs raw PCM audio to `/tmp/audio.pcm`. To stream this audio:

1. Ensure the Icecast server is running:
   ```
   docker-compose up -d
   ```

2. Use a tool like FFmpeg to stream the PCM file to Icecast:
   ```
   ffmpeg -f s16le -ar 22050 -ac 1 -i /tmp/audio.pcm -acodec libmp3lame -ab 128k -f mp3 icecast://source:password@localhost:8000/speaking-clock.mp3
   ```

3. Listen to the stream at `http://localhost:8000/speaking-clock.mp3`

## License

This project is licensed under the WTFPL (Do What The F*** You Want To Public License) - see the [LICENSE.md](LICENSE.md) file for details.

## Project Status

This project is a work in progress.