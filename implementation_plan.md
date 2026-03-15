# AI Vision Assistant Implementation

The goal is to create a Python application that uses a webcam to monitor the surroundings, runs real-time object detection via YOLOv8, and synthesizes localized speech logic to inform visually impaired individuals of what lies ahead.

## Proposed Changes

### Core Project Files

#### [NEW] main.py
The primary application script containing:
- `TTSThread`: A dedicated thread for Text-To-Speech (pyttsx3) to ensure video capturing doesn't lag while the engine is speaking.
- Real-time video processing using OpenCV (`cv2.VideoCapture`).
- Model inferences using Ultralytics `YOLO("yolov8n.pt")` for recognizing objects.
- Logic to avoid text-to-speech spam (e.g., waiting 4 seconds between assertions).

#### [NEW] requirements.txt
Will outline Python dependencies so the user can quickly get started using `pip install -r requirements.txt`. Includes `ultralytics`, `opencv-python`, and `pyttsx3`.

#### [NEW] README.md
A quick-start guide providing a summary of requirements and instructions to run the application.

## Verification Plan

### Automated / Manual Fast Testing
I will create the scripts locally to the workspace. The user will be instructed to install the requirements and run `python main.py`. No system dependencies except standard Python environment and webcam hardware exist.
