
import cv2
import json
import os

from attendance_db import create_attendance_table, mark_attendance
from zone_config import (
    ZONE_X,
    ZONE_Y,
    ZONE_WIDTH,
    ZONE_HEIGHT
)

# Configuration
DETECTOR_MODEL = "models/face_detection_yunet_2023mar.onnx"
RECOGNIZER_MODEL = "models/face_recognition_sface_2021dec.onnx"

DATASET_DIR = "dataset"
EMPLOYEES_FILE = "employees.json"
THRESHOLD = 0.363

# Initialize attendance database
create_attendance_table()

# Load employees
with open(EMPLOYEES_FILE, "r", encoding="utf-8") as file:
    employees = json.load(file)

# Load face detection model
detector = cv2.FaceDetectorYN.create(
    DETECTOR_MODEL,
    "",
    (320, 320),
    score_threshold=0.8,
    nms_threshold=0.3,
    top_k=5000
)

# Load face recognition model
recognizer = cv2.FaceRecognizerSF.create(
    RECOGNIZER_MODEL,
    ""
)

# Build employee face database
face_database = {}

print("Building employee face database...")

for employee_id, details in employees.items():

    employee_folder = os.path.join(DATASET_DIR, employee_id)
    features = []

    if not os.path.isdir(employee_folder):
        continue

    for filename in os.listdir(employee_folder):

        if not filename.lower().endswith(
            (".jpg", ".jpeg", ".png")
        ):
            continue

        image_path = os.path.join(employee_folder, filename)
        image = cv2.imread(image_path)

        if image is None:
            continue

        height, width = image.shape[:2]
        detector.setInputSize((width, height))

        _, faces = detector.detect(image)

        if faces is None or len(faces) != 1:
            continue

        aligned = recognizer.alignCrop(image, faces[0])
        feature = recognizer.feature(aligned)

        features.append(feature)

    if features:
        face_database[employee_id] = {
            "name": details["name"],
            "features": features
        }

        print(
            f"Loaded {details['name']}: {len(features)} samples"
        )

if not face_database:
    print("ERROR: No registered faces found.")
    raise SystemExit

print("Face database ready!")

# Open webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Webcam could not open.")
    raise SystemExit

# Request webcam resolution
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Load permanent zone coordinates
zone_x = ZONE_X
zone_y = ZONE_Y
zone_w = ZONE_WIDTH
zone_h = ZONE_HEIGHT

print("\nPermanent attendance zone loaded!")
print("Zone position:", zone_x, zone_y)
print("Zone size:", zone_w, zone_h)
print("No manual selection required.")
print("Press Q to stop attendance.")

# Track employees currently inside the zone
last_seen = {}

while True:

    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read webcam.")
        break

    height, width = frame.shape[:2]

    # Keep the configured zone inside the camera frame
    x1 = max(0, min(zone_x, width))
    y1 = max(0, min(zone_y, height))

    x2 = max(0, min(zone_x + zone_w, width))
    y2 = max(0, min(zone_y + zone_h, height))

    current_seen = set()

    # Process only the selected zone
    if x2 > x1 and y2 > y1:

        zone_frame = frame[y1:y2, x1:x2]

        zone_height, zone_width = zone_frame.shape[:2]

        detector.setInputSize(
            (zone_width, zone_height)
        )

        _, faces = detector.detect(zone_frame)

        if faces is not None:

            for face in faces:

                # Extract live facial features
                aligned = recognizer.alignCrop(
                    zone_frame,
                    face
                )

                live_feature = recognizer.feature(aligned)

                best_score = -1
                best_employee_id = None
                best_name = "Unknown"

                # Compare with registered employees
                for employee_id, employee in face_database.items():

                    for registered_feature in employee["features"]:

                        score = recognizer.match(
                            live_feature,
                            registered_feature,
                            cv2.FaceRecognizerSF_FR_COSINE
                        )

                        if score > best_score:
                            best_score = score
                            best_employee_id = employee_id
                            best_name = employee["name"]

                fx, fy, fw, fh = face[:4].astype(int)

                # Convert zone coordinates to camera coordinates
                fx += x1
                fy += y1

                if best_score >= THRESHOLD:

                    label = f"{best_name} ({best_score:.2f})"
                    color = (0, 255, 0)

                    current_seen.add(best_employee_id)

                    # Record attendance once per appearance
                    if best_employee_id not in last_seen:

                        mark_attendance(
                            best_employee_id,
                            best_name
                        )

                        last_seen[best_employee_id] = 0

                else:

                    label = f"Unknown ({best_score:.2f})"
                    color = (0, 0, 255)

                # Draw face rectangle
                cv2.rectangle(
                    frame,
                    (fx, fy),
                    (fx + fw, fy + fh),
                    color,
                    2
                )

                # Display employee name
                cv2.putText(
                    frame,
                    label,
                    (fx, max(25, fy - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

    # Clear tracking when employee leaves the zone
    for employee_id in list(last_seen):

        if employee_id not in current_seen:
            last_seen.pop(employee_id)

    # Draw permanent attendance zone
    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (255, 255, 0),
        3
    )

    cv2.putText(
        frame,
        "ATTENDANCE ZONE",
        (x1, max(25, y1 - 12)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    cv2.imshow(
        "Permanent Zone AI Attendance",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release resources
camera.release()
cv2.destroyAllWindows()

print("\nZone attendance system stopped.")
