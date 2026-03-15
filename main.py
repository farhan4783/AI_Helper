import cv2
import pyttsx3
import threading
import time
import queue
from collections import defaultdict
from ultralytics import YOLO

class VoiceAssistant:
    def __init__(self, cooldown=5.0):
        self.cooldown = cooldown
        self.last_spoken = defaultdict(float)
        self.message_queue = queue.Queue()
        
        # Start a dedicated background thread for TTS
        self.speech_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.speech_thread.start()
        
    def _tts_worker(self):
        """Dedicated background thread for text-to-speech to prevent blocking and COM thread errors."""
        # Initialize engine within the thread that will use it.
        # This is CRITICAL for Windows/macOS stability.
        try:
            # For Windows pythoncom initialization is sometimes needed in new threads
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass  # pythoncom is Windows only, ignore on other OSes
            
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)  # Adjust speech rate slightly faster than default
        
        while True:
            text = self.message_queue.get()
            if text is None:
                break # Exit signal
            
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
            finally:
                self.message_queue.task_done()

    def announce_objects(self, detected_classes):
        """Queues objects for announcement if they haven't been spoken recently."""
        
        current_time = time.time()
        
        # Filter classes based on cooldown
        to_speak = []
        for obj in set(detected_classes):
            if current_time - self.last_spoken[obj] > self.cooldown:
                to_speak.append(obj)
                self.last_spoken[obj] = current_time
                
        if to_speak:
            # Format text naturally
            if len(to_speak) == 1:
                text = f"{to_speak[0]} ahead."
            elif len(to_speak) == 2:
                text = f"{to_speak[0]} and {to_speak[1]} ahead."
            else:
                text = ", ".join(to_speak[:-1]) + f", and {to_speak[-1]} ahead."
                
            print(f"Speaking: {text}")
            
            # Put text in queue. If the queue already has items, it means the assistant
            # is busy speaking, so we can optionally skip or just let it queue up.
            # To avoid spamming, we can ensure the queue isn't too large:
            if self.message_queue.qsize() < 2:
                self.message_queue.put(text)
                
    def shutdown(self):
        self.message_queue.put(None)


def main():
    print("Loading AI Vision Assistant...")
    print("Please wait while the YOLOv8 model is downloaded and loaded.")
    
    # Load YOLOv8 Nano model for fastest real-time performance on average hardware
    try:
        model = YOLO("yolov8n.pt")
    except Exception as e:
        print(f"Error loading YOLO model: {e}")
        return

    # Initialize Voice Assistant
    assistant = VoiceAssistant(cooldown=6.0)  # 6 seconds cooldown per object
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
        
    # Lower resolution for faster processing if needed
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    assistant.message_queue.put("AI Vision Assistant starting up. Camera is active.")
    print("Camera loaded. Press 'Q' to exit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame. Exiting...")
                break

            # Run YOLOv8 inference on the frame
            # stream=True returns a generator (good for continuous feed)
            # verbose=False reduces console spam
            results = model(frame, stream=True, verbose=False)

            detected_objects = []
            
            # Parse results
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Bounding box
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # Confidence and Class ID
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    # Only consider objects with decent confidence (e.g., above 60%)
                    if conf > 0.6:
                        class_name = model.names[cls_id]
                        detected_objects.append(class_name)
                        
                        # Draw bounding box on frame
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        # Note confidence and class name above bounding box
                        label = f"{class_name} {conf:.2f}"
                        cv2.putText(frame, label, (x1, max(y1-10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Trigger voice announcement
            if detected_objects:
                assistant.announce_objects(detected_objects)

            # Display the frame
            cv2.imshow("AI Vision Assistant", frame)

            # Check for quit key (Q)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        print("Shutting down...")
        assistant.shutdown()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
