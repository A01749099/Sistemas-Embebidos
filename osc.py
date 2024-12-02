import cv2
import time
import numpy as np
import face_recognition
import dlib
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import os
import io
from PIL import Image


# Google Drive Constants
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_ID = '1WaXj_U5QL0nCEeFPuA_8uRmrwNeYnY5G'

known_face_encodings = []
known_face_names = []

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
            while not downloader.next_chunk()[1]:  # Descargar imagen
                pass

            file_data.seek(0)
            image_np = np.array(Image.open(file_data))
            encodings = face_recognition.face_encodings(image_np)
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


def main():
    try:
        service = authenticate_google_drive()
        load_images_from_drive(service, FOLDER_ID)
    except Exception as e:
        print(f"Error loading images from Google Drive: {e}")
        return

    if not known_face_encodings:
        print("No faces found in Google Drive. Please add people first.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open the webcam.")
        return

    print("Starting motion and face detection... Press 'q' to quit.")
    detector = dlib.get_frontal_face_detector()

    # Variables for photo capturing
    last_no_motion_photo_time = time.time()
    last_motion_photo_time = time.time()
    photo_count = 0
    UNKNOWN_FOLDER_ID = '1j1eDGdEqxpQiJDTxBoNIX9g-S3oMO9g2'  # Replace with the ID of your "unknown" folder

    # Variables for detecting motion
    motion_threshold = 777777
    ret, previous_frame = cap.read()
    if not ret:
        print("Error: Could not read the initial frame.")
        return
    previous_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read the frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect motion using frame difference
        frame_diff = cv2.absdiff(previous_gray, gray)
        _, motion_mask = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        motion_level = np.sum(motion_mask)
        previous_gray = gray

        if motion_level > motion_threshold:
            print("Motion detected.")

            # Check for face recognition
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

            face_encodings = face_recognition.face_encodings(rgb_small_frame)
            face_detected = False

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                if True in matches:
                    face_detected = True
                    break

            if not face_detected and time.time() - last_motion_photo_time >= 5:
                print("Unknown person detected. Taking a photo every 5 seconds.")
                photo_path = f"unknown_{photo_count}.jpg"
                cv2.imwrite(photo_path, frame)  # Save photo locally
                upload_to_drive(service, photo_path, UNKNOWN_FOLDER_ID)  # Upload to Google Drive
                os.remove(photo_path)  # Remove the local photo after upload
                last_motion_photo_time = time.time()
                photo_count += 1

        elif time.time() - last_no_motion_photo_time >= 60:
            print("No motion detected. Taking a photo every 1 minute.")
            last_no_motion_photo_time = time.time()

        # Display the video feed
        cv2.putText(frame, "Motion and Face Detection Mode", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Motion and Face Detection", frame)

        # Quit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
