import cv2
import pyttsx3
import threading
import time
import queue
from collections import defaultdict, deque
import numpy as np
import easyocr
from ultralytics import YOLO

class VoiceAssistant:
    def __init__(self, cooldown=6.0):
        self.cooldown = cooldown
        self.last_spoken = defaultdict(float)
        self.message_queue = queue.Queue()
        self.urgent_message = None
        self.last_spoken_text = ""
        
        # Start a dedicated background thread for TTS
        self.speech_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.speech_thread.start()
        
    def _tts_worker(self):
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass
            
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        
        while True:
            # Check for urgent message first
            if self.urgent_message:
                text = self.urgent_message
                self.urgent_message = None
                # Clear normal queue safely
                with self.message_queue.mutex:
                    self.message_queue.queue.clear()
            else:
                try:
                    text = self.message_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
            if text is None:
                break
                
            try:
                self.last_spoken_text = text
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")

    def announce_urgent(self, text):
        print(f"URGENT: {text}")
        self.urgent_message = text

    def announce(self, text):
        # We limit the queue size so we don't fall behind real-time
        if self.message_queue.qsize() < 2:
            print(f"Speaking: {text}")
            self.message_queue.put(text)

    def announce_objects(self, detected_objects):
        current_time = time.time()
        to_speak = []
        spoken_this_frame = set()
        
        sorted_objs = sorted(detected_objects, key=lambda x: x['area'], reverse=True)
        
        for obj in sorted_objs:
            # Create a unique key for cooldowns
            cooldown_key = f"{obj['class']}_{obj['trajectory']}"
            
            if current_time - self.last_spoken[cooldown_key] > self.cooldown:
                if obj['class'] not in spoken_this_frame:
                    to_speak.append(obj)
                    self.last_spoken[cooldown_key] = current_time
                    spoken_this_frame.add(obj['class'])
                
        if to_speak:
            sentences = []
            for obj in to_speak:
                trajectory = obj['trajectory']
                traj_str = f"{trajectory} " if trajectory else ""
                sentences.append(f"{traj_str}{obj['class']} {obj['position']}")
                
            if len(sentences) == 1:
                text = sentences[0] + "."
            elif len(sentences) == 2:
                text = sentences[0] + " and " + sentences[1] + "."
            else:
                text = ", ".join(sentences[:-1]) + ", and " + sentences[-1] + "."
                
            self.announce(text)
                
    def shutdown(self):
        self.message_queue.put(None)

def enhance_low_light(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    is_night_vision_on = False
    
    # Threshold for dark frame
    if mean_brightness < 70:
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        lab[:,:,0] = clahe.apply(lab[:,:,0])
        frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        is_night_vision_on = True
        
    return frame, is_night_vision_on

def draw_hud(frame, fps, mode, night_vision, last_spoken):
    frame_height, frame_width = frame.shape[:2]
    
    # Create copies for blended overlays
    overlay = frame.copy()
    
    # Top overlay
    cv2.rectangle(overlay, (0, 0), (frame_width, 60), (30, 30, 30), -1)
    # Bottom overlay
    cv2.rectangle(overlay, (0, frame_height - 40), (frame_width, frame_height), (30, 30, 30), -1)
    
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    # Determine mode color
    mode_color = (0, 255, 255) if mode == "READING" else (0, 255, 0)
    
    # Draw text elements
    cv2.putText(frame, f"MODE: {mode}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
    cv2.putText(frame, f"FPS: {fps}", (frame_width - 100, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    if night_vision:
        cv2.putText(frame, "NIGHT VISION: ON", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 100), 2)
        
    last_spoken = last_spoken if last_spoken else "Initializing..."
    cv2.putText(frame, f"Speech: {last_spoken}", (10, frame_height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

def main():
    print("Loading AI Vision Assistant - Max Level...")
    assistant = VoiceAssistant(cooldown=7.0)
    
    try:
        print("Loading YOLOv8 Model. This might take a moment...")
        model = YOLO("yolov8n.pt")
        print("YOLOv8 Loaded.")
        
        print("Loading EasyOCR Model. This might also take a moment...")
        reader = easyocr.Reader(['en'])
        print("EasyOCR Loaded.")
    except Exception as e:
        print(f"Error loading AI models: {e}")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    assistant.announce("AI Vision Assistant starting up. Press R to toggle reading mode.")
    
    mode = "NAVIGATION"
    last_ocr_time = 0
    fps_time = time.time()
    fps = 0
    frame_count = 0
    
    # Track object sizes for trajectory (approaching vs moving away)
    object_history = defaultdict(lambda: deque(maxlen=10))

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Frame rate calculation
            frame_count += 1
            if time.time() - fps_time >= 1.0:
                fps = frame_count
                frame_count = 0
                fps_time = time.time()

            # Automatic night vision processing
            frame, night_vision_on = enhance_low_light(frame)
            frame_height, frame_width = frame.shape[:2]
            
            # Handle key events
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                mode = "READING" if mode == "NAVIGATION" else "NAVIGATION"
                assistant.announce(f"{mode.lower()} mode activated")
                
            if mode == "NAVIGATION":
                # Using model.track() to preserve object IDs across frames
                results = model.track(frame, persist=True, verbose=False)
                detected_objects = []
                
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0])
                        
                        if conf > 0.6:
                            class_name = model.names[cls_id]
                            
                            # Safely extract ID (it could be None if tracking loses the object briefly)
                            obj_id = int(box.id[0]) if box.id is not None else -1
                            
                            area = (x2 - x1) * (y2 - y1)
                            
                            # Determine Movement Trajectory
                            trajectory = ""
                            if obj_id != -1:
                                history = object_history[obj_id]
                                history.append(area)
                                if len(history) == 10:
                                    old_area = sum(list(history)[:3]) / 3
                                    new_area = sum(list(history)[-3:]) / 3
                                    # Thresholds for moving approach / recede
                                    if new_area > old_area * 1.2:
                                        trajectory = "approaching"
                                    elif new_area < old_area * 0.8:
                                        trajectory = "moving away"
                            
                            # Determine Horizontal Position
                            x_center = (x1 + x2) / 2
                            width_frac = x_center / frame_width
                            if width_frac < 0.33:
                                h_pos = "on the left"
                            elif width_frac > 0.66:
                                h_pos = "on the right"
                            else:
                                h_pos = "in front"
                                
                            # Determine Distance
                            height_frac = (y2 - y1) / frame_height
                            if height_frac > 0.65:
                                dist = "very close"
                            elif height_frac > 0.3:
                                dist = "nearby"
                            else:
                                dist = "in the distance"
                                
                            # Imminent Collision Warning!
                            if dist == "very close" and h_pos == "in front":
                                assistant.announce_urgent(f"WARNING: {class_name} directly ahead!")
                                # Draw red flashing danger border
                                if int(time.time() * 5) % 2 == 0:
                                    cv2.rectangle(frame, (0,0), (frame_width-1, frame_height-1), (0,0,255), 10)
                                    
                            detected_objects.append({
                                "class": class_name,
                                "position": f"{dist} {h_pos}",
                                "area": area,
                                "trajectory": trajectory
                            })
                            
                            # Render bounding boxes
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            label = f"{trajectory} {class_name} {conf:.2f}".strip()
                            cv2.putText(frame, label, (x1, max(y1-10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                if detected_objects:
                    assistant.announce_objects(detected_objects)
                    
            elif mode == "READING":
                # In Reading mode, scan every 3 seconds
                # OCR inference pauses the loop momentarily
                current_time = time.time()
                if current_time - last_ocr_time > 3.0:
                    text_results = reader.readtext(frame, detail=0)
                    if text_results:
                        combined_text = " ".join(text_results)
                        # Avoid spelling purely 1-letter noise
                        if len(combined_text.strip()) > 3:
                            assistant.announce(f"Text detected: {combined_text}")
                    last_ocr_time = current_time
                    
                # Render visual guide for reading
                cv2.rectangle(frame, (100, 80), (frame_width-100, frame_height-100), (255, 255, 0), 2)
                cv2.putText(frame, "Align text within yellow box", (110, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # Draw sleek UI overlay
            draw_hud(frame, fps, mode, night_vision_on, assistant.last_spoken_text)
            
            # Display frame
            cv2.imshow("AI Vision Assistant", frame)

    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down...")
        assistant.shutdown()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
