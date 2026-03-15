# AI Vision Assistant

A computer vision project designed for visually impaired individuals. It uses the system's camera to monitor its surroundings, identify objects via AI, and inform the user of what's ahead using voice (Text-to-Speech).

## Features
- Real-time Object Detection with YOLOv8.
- Non-blocking Text-to-Speech (TTS) using threaded voice announcements.
- Smart cooldowns to prevent repetitive speech alerts for the same objects.

## Requirements

Ensure you have Python 3.8 or later installed.

Install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

Note: If your system has issues with `pyttsx3`, ensure you have the appropriate voice engines installed locally (e.g. `espeak` on Linux, Microsoft Speech Platform on Windows, or `NSSpeechSynthesizer` on macOS).

## Usage

Run the program via Python. The application will initialize the webcam and begin speaking the objects detected to you:

```bash
python main.py
```

Press `q` within the OpenCV window or use `Ctrl+C` in the terminal to exit the application.
