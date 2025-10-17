import face_recognition
import cv2
import os
import time
import threading
import collections # <-- 1. IMPORT COLLECTIONS

class FacialRecognizer:
    """
    A class to handle facial recognition tasks in a separate thread.
    This version uses an aggregate state logic over a time window to reduce jitter.
    """

    def __init__(self, trusted_faces_dir, tolerance=0.6, model="cnn"):
        """
        Initializes the FacialRecognizer.
        ...
        """
        self.trusted_faces_dir = trusted_faces_dir
        self.trusted_face_encodings = []
        self.trusted_face_names = []
        self.tolerance = tolerance
        self.model = model
        
        # --- NEW State Variables ---
        self.is_verified = False 
        # Defines the time window (in seconds) for aggregating detection states.
        self.state_window_seconds = 3 
        # A deque to store recent detections (timestamp, status).
        # It's an efficient way to keep a rolling list of recent events.
        self.detection_history = collections.deque()
        
        # --- Threading Control ---
        self._running = False
        self._recognition_thread = None
        
        print(f"Loading trusted faces... (using '{self.model}' model for detection)")
        self._load_trusted_faces()

    def _load_trusted_faces(self):
        # This method remains unchanged
        """
        Loads and encodes faces from the trusted faces directory.
        """
        if not os.path.isdir(self.trusted_faces_dir):
            return 

        for filename in os.listdir(self.trusted_faces_dir):
            filepath = os.path.join(self.trusted_faces_dir, filename)
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    image = face_recognition.load_image_file(filepath)
                    face_encodings = face_recognition.face_encodings(image)
                    if face_encodings:
                        self.trusted_face_encodings.append(face_encodings[0])
                        self.trusted_face_names.append(os.path.splitext(filename)[0])
                        print(f"Successfully loaded and encoded: {filename}")
                    else:
                        print(f"Warning: No faces found in {filename}. Skipping.")
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
        
        if not self.trusted_face_encodings:
            print("\nWarning: No trusted faces were loaded. The system will not recognize anyone.")
        else:
            print(f"\nFinished loading {len(self.trusted_face_encodings)} trusted faces.")

    def process_frame(self, frame):
        # This method remains unchanged
        """
        Processes a single video frame to detect and recognize faces.
        ...
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_frame, model=self.model)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations, num_jitters=2)

        detected_faces = []
        is_trusted_person_present = False

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(self.trusted_face_encodings, face_encoding, self.tolerance)
            name = "Untrusted"

            if True in matches:
                is_trusted_person_present = True
                first_match_index = matches.index(True)
                name = self.trusted_face_names[first_match_index]

            detected_faces.append((face_location, name))

        if not face_encodings:
            overall_status = "No Face Detected"
        else:
            overall_status = "Trusted" if is_trusted_person_present else "Untrusted"
            
        return overall_status, detected_faces

    def _recognition_loop(self):
        """The main recognition loop with the new aggregate state logic."""
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            print("\nError: Could not open video stream.")
            return

        last_verified_state = self.is_verified
        print(f"Initial State: {'Verified' if self.is_verified else 'Unverified'}")
        
        window_name = "Facial Recognition"

        while self._running:
            ret, frame = video_capture.read()
            if not ret:
                print("Failed to grab frame.")
                time.sleep(1) 
                continue
            
            status, detected_faces = self.process_frame(frame)

            # --- START: NEW AGGREGATE STATE LOGIC ---
            current_time = time.time()
            
            # 1. Add the latest detection status to our history
            self.detection_history.append((current_time, status))

            # 2. Remove any old detections that are outside our 3-second window
            while self.detection_history and current_time - self.detection_history[0][0] > self.state_window_seconds:
                self.detection_history.popleft()

            # 3. Determine the state based on the majority in the current window
            if self.detection_history:
                # Count how many times a "Trusted" face was seen in the window
                trusted_count = sum(1 for _, s in self.detection_history if s == "Trusted")
                total_count = len(self.detection_history)
                
                # If trusted detections make up at least 50% of the history, we are verified.
                # You can adjust this threshold (e.g., to > 0.5) to be stricter.
                if (trusted_count / total_count) >= 0.5:
                    self.is_verified = True
                else:
                    self.is_verified = False
            else:
                # If the history is empty, default to unverified
                self.is_verified = False
            # --- END: NEW AGGREGATE STATE LOGIC ---

            if self.is_verified != last_verified_state:
                print(f"State changed to: {'Verified' if self.is_verified else 'Unverified'}")
                last_verified_state = self.is_verified
            
            # --- Visual Feedback Drawing (unchanged) ---
            for (top, right, bottom, left), name in detected_faces:
                box_color = (0, 255, 0) if name != "Untrusted" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), box_color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

            state_text = f"System State: {'Verified' if self.is_verified else 'Unverified'}"
            state_color = (0, 255, 0) if self.is_verified else (0, 0, 255)
            cv2.putText(frame, state_text, (10, 30), cv2.FONT_HERSHEY_DUPLEX, 1.0, state_color, 2)

            cv2.imshow(window_name, frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self._running = False
        
        video_capture.release()
        cv2.destroyAllWindows()
        print("Recognition loop stopped and camera released.")


    def start_recognition(self):
        # This method remains unchanged
        """
        Starts the recognition process in a background thread.
        """
        if not os.path.isdir(self.trusted_faces_dir) or not any(f.lower().endswith(('.png', '.jpg', '.jpeg')) for f in os.listdir(self.trusted_faces_dir)):
            print(f"\n--- IMPORTANT ---")
            print(f"Directory '{self.trusted_faces_dir}' does not exist or is empty.")
            print("Please create it and add images of trusted people.")
            print("-----------------")
            return
        
        if self._running:
            print("Recognition is already running.")
            return

        self._running = True
        self._recognition_thread = threading.Thread(target=self._recognition_loop, daemon=True)
        self._recognition_thread.start()
        print("\nRecognition thread started.")

    def stop_recognition(self):
        # This method remains unchanged
        """Stops the recognition process."""
        if not self._running:
            print("Recognition is not running.")
            return

        print("\nStopping recognition process...")
        self._running = False
        self._recognition_thread.join() 
        print("Recognition thread stopped.")