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




AI Vision Assistant - Max Level Upgrade Walkthrough
The AI Vision Assistant in Project24 has been thoroughly upgraded to provide a sophisticated, safe, and feature-rich experience for visually impaired users.

Changes Made
1. Imminent Collision Warning System 🚨
Implementation: We upgraded main.py with an announce_urgent priority queuing system.
Safety: When an object is detected as very close AND in front, the system immediately interrupts any current speech, clears lower-priority queued objects, and loudly announces WARNING: [Object] directly ahead!. This is coupled with a flashing red border on the screen.
2. Intelligent Movement Tracking & Trajectory
Implementation: The script now leverages YOLOv8's model.track(persist=True) instead of static inference.
Why it matters: By assigning unique IDs to objects and tracking their pixel area over the last 10 frames, the assistant can mathematically determine if an object is approaching or moving away. This adjective is now appended dynamically to the voice announcements.
3. Automatic Night Vision (CLAHE Enhancement) 🌙
Implementation: The enhance_low_light function was added to compute the mean brightness of every frame.
Result: If the environment is dark (brightness < 70), the frame is temporarily converted to the LAB color space where a CLAHE (Contrast Limited Adaptive Histogram Equalization) filter is rapidly applied to boost details without causing light washout, allowing the AI to effectively "see in the dark".
4. Interactive Reading Mode (OCR) 📖
Implementation: Integrated EasyOCR.
Usage: Press the 'R' key on your keyboard while the window is focused to toggle Reading Mode. The assistant will notify you. It will then scan the yellow guide box on your screen for text every few seconds and read it out loud to you!
5. Premium HUD Overlay
Implementation: The OpenCV rendering loop was upgraded to include sleek, semi-transparent overlays at the top and bottom of the video feed.
Features: It lists the current MODE, Real-time FPS, Night Vision Status, and a transcript of the last spoken AI phrase at the bottom of the screen.
Validation Results
Code syntax passes fully (python -m py_compile main.py).
No conflicting package dependencies in requirements.txt.
How to test:
Open a terminal in the Project24 directory and run:

bash
pip install -r requirements.txt
python main.py
Try covering the camera slightly to test Night Vision, moving your hand towards it to test tracking, and putting your hand directly in front to trigger the Collision Alarm!

