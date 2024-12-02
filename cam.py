import face_recognition
import cv2
import numpy as np
import os

os.environ["QT_QPA_PLATFORM"] = "xcb"


# Function to load known faces from a local folder
def load_known_faces_from_folder(folder_path):
    known_face_encodings = []
    known_face_names = []

    # Iterate through all files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith((".jpg", ".jpeg", ".png")):  # Check for image files
            name = os.path.splitext(filename)[0]  # Extract name from filename
            photo_path = os.path.join(folder_path, filename)
            try:
                # Load the image and encode the face
                image = face_recognition.load_image_file(photo_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:  # Ensure at least one face is detected
                    encoding = encodings[0]
                    known_face_encodings.append(encoding)
                    known_face_names.append(name)
                else:
                    print(f"No faces detected in {photo_path}. Skipping...")
            except Exception as e:
                print(f"Error processing {photo_path}: {e}")

    return known_face_encodings, known_face_names


# Basic anti-spoofing function
def is_real_face(frame, face_location):
    """
    Check if the detected face is real using basic anti-spoofing measures.
    This function measures changes in brightness around the face region.

    Returns True if the face is likely real, False otherwise.
    """
    top, right, bottom, left = face_location
    # Extract the face region
    face_region = frame[top:bottom, left:right]

    # Convert to grayscale for intensity analysis
    gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)

    # Calculate the Laplacian variance to detect flat or 3D-like surfaces
    laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()

    # Heuristic threshold: adjust based on testing
    if laplacian_var > 15:
        return True  # Likely real face
    else:
        return False  # Likely spoofed face (flat surface)

# Function to recognize faces in real-time
def recognize_faces():
    folder_path = "C:/Users/danii/Python_codes/bloque/Fotos/victor"  # Replace with your folder path
    known_face_encodings, known_face_names = load_known_faces_from_folder(folder_path)
    if not known_face_encodings:
        print("No faces found in the folder. Please add photos first.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open the webcam.")
        return

    print("Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read the frame.")
            break

        # Resize the frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        # Find all face locations and encodings in the current frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Apply anti-spoofing
            scaled_face_location = tuple(coord * 4 for coord in face_location)  # Scale back for anti-spoofing
            if not is_real_face(frame, scaled_face_location):
                face_names.append("Spoof Attempt")
                continue

            # Compare the face with known faces
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # Use the known face with the smallest distance if a match exists
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            face_names.append(name)

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame is scaled down
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a rectangle around the face
            color = (0, 255, 0) if name != "Spoof Attempt" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

        # Show the video feed
        cv2.imshow("Face Recognition with Anti-Spoofing", frame)

        # Quit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# Main logic
if __name__ == "__main__":
    recognize_faces()
