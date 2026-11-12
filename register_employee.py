
import cv2
import json
from pathlib import Path

# Project folders
BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / "dataset"
EMPLOYEE_FILE = BASE_DIR / "employees.json"

DATASET_DIR.mkdir(exist_ok=True)

# Load existing employee records
if EMPLOYEE_FILE.exists():
    employees = json.loads(EMPLOYEE_FILE.read_text(encoding="utf-8"))
else:
    employees = {}

# Employee information
employee_id = input("Enter Employee ID: ").strip().upper()
employee_name = input("Enter Employee Name: ").strip()

if not employee_id or not employee_name:
    print("Employee ID and Name are required.")
    raise SystemExit

if not employee_id.isalnum():
    print("Use only letters and numbers in Employee ID.")
    raise SystemExit

if employee_id in employees:
    print("This Employee ID is already registered.")
    raise SystemExit

# Employee image folder
employee_folder = DATASET_DIR / employee_id
employee_folder.mkdir(exist_ok=True)

# Save employee details
employees[employee_id] = {
    "name": employee_name
}

EMPLOYEE_FILE.write_text(
    json.dumps(employees, indent=4),
    encoding="utf-8"
)

# Face detector
detector = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Webcam could not open.")
    raise SystemExit

print("\nEmployee registration started!")
print("Look at the camera.")
print("Press S to save a face sample.")
print("Press Q to finish.")

saved_count = 0
target_samples = 10

while saved_count < target_samples:

    success, frame = camera.read()

    if not success:
        print("Cannot read webcam.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    for (x, y, w, h) in faces:
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

    cv2.putText(
        frame,
        f"Samples: {saved_count}/{target_samples}",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.imshow("Employee Registration", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):

        if len(faces) != 1:
            print("Please show exactly one face.")
            continue

        filename = employee_folder / f"{saved_count + 1}.jpg"

        cv2.imwrite(str(filename), frame)

        saved_count += 1

        print(f"Saved sample {saved_count}/{target_samples}")

    elif key == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()

print("\nRegistration session finished.")
print("Samples saved:", saved_count)
print("Employee ID:", employee_id)
print("Employee Name:", employee_name)
print("Image folder:", employee_folder)
