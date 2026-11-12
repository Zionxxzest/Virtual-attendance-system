
import cv2
import json
import os

from attendance_db import create_attendance_table, mark_attendance

DETECTOR_MODEL = "models/face_detection_yunet_2023mar.onnx"
RECOGNIZER_MODEL = "models/face_recognition_sface_2021dec.onnx"

DATASET_DIR = "dataset"
EMPLOYEES_FILE = "employees.json"
THRESHOLD = 0.363

# Create attendance database
create_attendance_table()

# Load employee information
with open(EMPLOYEES_FILE, "r", encoding="utf-8") as file:
    employees = json.load(file)

# Load AI models
detector = cv2.FaceDetectorYN.create(
    DETECTOR_MODEL, "", (320, 320),
    score_threshold=0.8,
    nms_threshold=0.3,
    top_k=5000
)

recognizer = cv2.FaceRecognizerSF.create(
    RECOGNIZER_MODEL, ""
)

# Build registered face database
face_database = {}

print("Building employee face database...")

for employee_id, details in employees.items():
    employee_folder = os.path.join(DATASET_DIR, employee_id)
    features = []

    if not os.path.isdir(employee_folder):
        continue

    for filename in os.listdir(employee_folder):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image = cv2.imread(os.path.join(employee_folder, filename))

        if image is None:
            continue

        height, width = image.shape[:2]
        detector.setInputSize((width, height))
        _, faces = detector.detect(image)

        if faces is None or len(faces) != 1:
            continue

        aligned = recognizer.alignCrop(image, faces[0])
        features.append(recognizer.feature(aligned))

    if features:
        face_database[employee_id] = {
            "name": details["name"],
            "features": features
        }
        print(f"Loaded {details['name']}: {len(features)} samples")

if not face_database:
    print("ERROR: No registered faces found.")
    raise SystemExit

print("Face database ready!")
print("Starting attendance camera...")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Webcam could not open.")
    raise SystemExit

# Avoid repeated attendance checks for the same face
last_seen = {}

while True:
    success, frame = camera.read()

    if not success:
        break

    height, width = frame.shape[:2]
    detector.setInputSize((width, height))
    _, faces = detector.detect(frame)

    current_seen = set()

    if faces is not None:
        for face in faces:
            aligned = recognizer.alignCrop(frame, face)
            live_feature = recognizer.feature(aligned)

            best_score = -1
            best_employee_id = None
            best_name = "Unknown"

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

            x, y, w, h = face[:4].astype(int)

            if best_score >= THRESHOLD:
                label = f"{best_name} ({best_score:.2f})"
                color = (0, 255, 0)

                current_seen.add(best_employee_id)

                # Record attendance only once per appearance.
                # Database prevents another check-in that day.
                if best_employee_id not in last_seen:
                    mark_attendance(best_employee_id, best_name)
                    last_seen[best_employee_id] = 0
                else:
                    last_seen[best_employee_id] += 1

            else:
                label = f"Unknown ({best_score:.2f})"
                color = (0, 0, 255)

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                color,
                2
            )

            cv2.putText(
                frame,
                label,
                (x, max(25, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

    # Allow a future re-check after the face disappears.
    for employee_id in list(last_seen):
        if employee_id not in current_seen:
            last_seen.pop(employee_id)

    cv2.imshow("AI Attendance System", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()

print("Attendance camera stopped.")
