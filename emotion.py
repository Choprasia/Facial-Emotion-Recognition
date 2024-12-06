import cv2
from deepface import DeepFace
import os
import time
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Authenticate Google Drive
def authenticate_drive():
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile("C:\\Users\\Lenovo\\Downloads\\faciaal\\client_secret_984184219801-knv08mh4sneu7hh6id62f0qb37gf55gq.apps.googleusercontent.com.json")
    gauth.LocalWebserverAuth()  
    return GoogleDrive(gauth)


# Save image to Google Drive
def upload_to_drive(drive, local_path, folder_id=None):
    # Ensure folder exists and you have access to it
    if folder_id:
        folder = drive.CreateFile({'id': folder_id})
        folder.FetchMetadata(fields="title, mimeType, owners")
        print(f"Folder title: {folder['title']}, Owner: {folder['owners']}")
    file = drive.CreateFile({"title": os.path.basename(local_path), "parents": [{"id": folder_id}] if folder_id else None})
    file.SetContentFile(local_path)
    file.Upload()
    print(f"Uploaded {local_path} to Google Drive.")
    return file['id']


# Categorize and move file to emotion folder in Google Drive
def move_to_emotion_folder(drive, file_id, master_folder_id, emotion):
    # Create emotion folder if it doesn't exist
    folder_list = drive.ListFile({'q': f"'{master_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"}).GetList()
    emotion_folder = next((f for f in folder_list if f['title'] == emotion), None)

    if not emotion_folder:
        emotion_folder = drive.CreateFile({"title": emotion, "mimeType": "application/vnd.google-apps.folder", "parents": [{"id": master_folder_id}]})
        emotion_folder.Upload()
        print(f"Created folder for emotion: {emotion}")

    # Move file to emotion folder
    file = drive.CreateFile({'id': file_id})
    file['parents'] = [{'id': emotion_folder['id']}]
    file.Upload()
    print(f"Moved file to {emotion} folder.")

# Load face cascade classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Authenticate and connect to Google Drive
drive = authenticate_drive()
master_folder_id = "1MrST3Rg806Z8wZWPsLwlcJvxXYiOxPUs"  # Replace with your Google Drive folder ID

# Start capturing video
cap = cv2.VideoCapture(0)  # 0 for default camera

if not cap.isOpened():
    print("Error: Camera not accessible!")
    exit()

print("Press 's' to capture a photo. Press 'q' to quit.")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    if not ret or frame is None:
        print("Failed to capture frame.")
        continue

    # Display the frame
    cv2.imshow('Capture Photo', frame)

    # Press 's' to save the photo
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        # Save captured photo locally with timestamp
        photo_path = f"captured_photo_{int(time.time())}.jpg"
        cv2.imwrite(photo_path, frame)
        print(f"Photo saved locally as {photo_path}.")

        try:
            # Perform emotion analysis
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            emotion = result[0]['dominant_emotion']
            print(f"Detected emotion: {emotion}")

            # Upload photo to Google Drive
            file_id = upload_to_drive(drive, photo_path, folder_id=master_folder_id)

            # Categorize photo by emotion
            move_to_emotion_folder(drive, file_id, master_folder_id, emotion)
        except Exception as e:
            print(f"Error in processing photo: {e}")

    # Press 'q' to quit
    if key == ord('q'):
        break

# Release the capture and close all windows
cap.release()
cv2.destroyAllWindows()
