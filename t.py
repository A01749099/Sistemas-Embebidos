#t.py
import cv2
import time
import numpy as np
import face_recognition
import dlib
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import io
from PIL import Image

# Google Drive Constants
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_ID = '1WaXj_U5QL0nCEeFPuA_8uRmrwNeYnY5G'
UNKNOWN_FOLDER_ID = '1j1eDGdEqxpQiJDTxBoNIX9g-S3oMO9g2'

# Timing constants
MOTION_PHOTO_INTERVAL = 5  # seconds between photos when motion is detected
NO_MOTION_PHOTO_INTERVAL = 300  # seconds (5 minutes) between photos when no motion
KNOWN_FACES_PAUSE_DURATION = 10  # seconds to pause detection when known faces are present

known_face_encodings = []
known_face_names = []

def test_camera(index):
    """Test a single camera and return detailed information"""
    print(f"\nTesting camera {index}...")
    cap = cv2.VideoCapture(index)
    
    if cap is None:
        print(f"Camera {index}: Failed to create VideoCapture object")
        return None
        
    if not cap.isOpened():
        print(f"Camera {index}: Failed to open")
        return None
    
    ret, frame = cap.read()
    if not ret:
        print(f"Camera {index}: Failed to read frame")
        cap.release()
        return None
    
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Camera {index} successfully initialized:")
    print(f"- Resolution: {width}x{height}")
    print(f"- FPS: {fps}")
    
    cap.release()
    return True

def authenticate_google_drive():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def list_subfolders(service, folder_id):
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])

def load_images_from_drive(service, folder_id):
    subfolders = list_subfolders(service, folder_id)
    for subfolder in subfolders:
        person_name = subfolder['name']
        subfolder_id = subfolder['id']
        query = f"'{subfolder_id}' in parents and (mimeType='image/jpeg' or mimeType='image/png')"
        images = service.files().list(q=query, fields="files(id, name)").execute().get('files', [])

        for image_file in images:
            file_id = image_file['id']
            request = service.files().get_media(fileId=file_id)
            file_data = io.BytesIO()
            downloader = MediaIoBaseDownload(file_data, request)
            while not downloader.next_chunk()[1]:
                pass

            file_data.seek(0)
            image_np = np.array(Image.open(file_data))
            if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                rgb_image = image_np
            else:
                rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_image)
            if face_locations:
                encodings = face_recognition.face_encodings(rgb_image, face_locations)
                if encodings:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(person_name)

def upload_to_drive(service, file_path, folder_id):
    """Upload a file to Google Drive."""
    try:
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f"Photo uploaded to Google Drive with ID: {uploaded_file.get('id')}")
    except Exception as e:
        print(f"Error uploading photo to Google Drive: {e}")

def process_frame(frame, scale=0.25):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    small_frame = cv2.resize(rgb_frame, (0, 0), fx=scale, fy=scale)
    return small_frame

def detect_motion(previous_frame, current_frame, threshold=777777):
    frame_diff = cv2.absdiff(previous_frame, current_frame)
    _, motion_mask = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
    motion_level = np.sum(motion_mask)
    return motion_level > threshold

def recognize_faces(frame, known_encodings, known_names):
    rgb_small_frame = process_frame(frame)
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    detected_names = []
    
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        if True in matches:
            first_match_index = matches.index(True)
            detected_names.append(known_names[first_match_index])
    return detected_names

def initialize_cameras():
    """Initialize cameras with detailed diagnostics"""
    print("Starting camera diagnostics...")
    working_cameras = []
    for i in range(10):  # Buscar en más índices
        result = test_camera(i)
        if result:
            working_cameras.append(i)
    
    print(f"\nFound {len(working_cameras)} working camera(s) at indices: {working_cameras}")
    
    if len(working_cameras) < 2:
        raise Exception(f"Need 2 cameras but only found {len(working_cameras)}")
    
    cap1 = cv2.VideoCapture(working_cameras[0])
    cap2 = cv2.VideoCapture(working_cameras[1])  # Cambiar a índice siguiente
    
    if not cap1.isOpened() or not cap2.isOpened():
        raise Exception("Failed to initialize one or both cameras")
    
    return cap1, cap2

def main():
    try:
        print("Authenticating with Google Drive...")
        service = authenticate_google_drive()
        print("Loading known faces from Drive...")
        load_images_from_drive(service, FOLDER_ID)
    except Exception as e:
        print(f"Error setting up Google Drive or loading known faces: {e}")
        return

    if not known_face_encodings:
        print("No known faces available. Exiting.")
        return

    try:
        print("Initializing cameras with diagnostics...")
        cap1, cap2 = initialize_cameras()
        print("Camera initialization successful!")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Diagnostic information:")
        print("- Check if both cameras are properly connected")
        print("- Check if cameras are recognized by the system (ls /dev/video*)")
        print("- Verify user has permission to access cameras (groups | grep video)")
        return

    # Initialize motion detection variables
    ret1, prev_frame1 = cap1.read()
    ret2, prev_frame2 = cap2.read()
    prev_gray1 = cv2.cvtColor(prev_frame1, cv2.COLOR_BGR2GRAY)
    prev_gray2 = cv2.cvtColor(prev_frame2, cv2.COLOR_BGR2GRAY)
    
    last_photo_time = time.time()
    photo_count = 0

    # Nuevas variables para rastrear detección de caras conocidas
    known_faces_start_time = None
    detection_paused = False

    try:
        print("Starting detection... Press CTRL+C to stop.")
        while True:
            # Read frames from both cameras
            ret1, frame1 = cap1.read()
            ret2, frame2 = cap2.read()
            
            if not ret1 or not ret2:
                print("Error reading frames. Exiting.")
                break

            # Process frames for motion detection
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

            # Detect motion in both cameras
            motion1 = detect_motion(prev_gray1, gray1)
            motion2 = detect_motion(prev_gray2, gray2)
            motion_detected = motion1 or motion2

            # Update previous frames
            prev_gray1 = gray1
            prev_gray2 = gray2

            # Recognize faces in both frames
            names_camera1 = recognize_faces(frame1, known_face_encodings, known_face_names)
            names_camera2 = recognize_faces(frame2, known_face_encodings, known_face_names)
            
            current_time = time.time()

            # Lógica para pausar la detección cuando hay caras conocidas
            if names_camera1 and names_camera2:
                if known_faces_start_time is None:
                    known_faces_start_time = current_time
                elif current_time - known_faces_start_time >= KNOWN_FACES_PAUSE_DURATION:
                    detection_paused = True
                    print("Detection paused: Known faces detected in both cameras")
            else:
                known_faces_start_time = None
                if detection_paused:
                    detection_paused = False
                    print("Detection resumed")

            # Solo continúa con la lógica si NO está en pausa
            if not detection_paused:
                time_since_last_photo = current_time - last_photo_time
                
                # Set photo interval based on conditions
                required_interval = MOTION_PHOTO_INTERVAL if motion_detected else NO_MOTION_PHOTO_INTERVAL

                # Check if it's time to take photos
                if time_since_last_photo >= required_interval:
                    should_take_photo = False
                    photo_reason = ""

                    # Case 1: No faces detected in either camera
                    if not names_camera1 and not names_camera2:
                        should_take_photo = True
                        photo_reason = "unknown_person"
                        if not motion_detected:
                            photo_reason = "periodic_check"
                    
                    # Case 2: Face detected in camera 1 but not in camera 2
                    elif names_camera1 and not names_camera2:
                        should_take_photo = True
                        photo_reason = f"discrepancy_cam1_{'-'.join(names_camera1)}"
                    
                    # Case 3: Face detected in camera 2 but not in camera 1
                    elif names_camera2 and not names_camera1:
                        should_take_photo = True
                        photo_reason = f"discrepancy_cam2_{'-'.join(names_camera2)}"

                    if should_take_photo:
                        print(f"Taking photos... Reason: {photo_reason}")
                        for i, frame in enumerate([frame1, frame2]):
                            photo_path = f"{photo_reason}_cam{i+1}_{photo_count}.jpg"
                            cv2.imwrite(photo_path, frame)
                            upload_to_drive(service, photo_path, UNKNOWN_FOLDER_ID)
                            os.remove(photo_path)
                        
                        last_photo_time = current_time
                        photo_count += 1

                # Print detections
                if names_camera1:
                    print(f"Camera 1 detected: {names_camera1}")
                if names_camera2:
                    print(f"Camera 2 detected: {names_camera2}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nDetection stopped by user.")
    finally:
        cap1.release()
        cap2.release()

if __name__ == "__main__":
    main()