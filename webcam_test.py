
import cv2

# Open the default webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Webcam could not be opened.")
    exit()

print("Webcam started successfully!")
print("Press Q to close the camera.")

while True:
    success, frame = camera.read()

    if not success:
        print("ERROR: Cannot read webcam.")
        break

    cv2.imshow("My First AI Attendance Project", frame)

    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()

print("Webcam closed successfully.")
