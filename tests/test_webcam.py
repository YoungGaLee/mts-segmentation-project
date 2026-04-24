import cv2
from pipeline.detector import Detector

detector = Detector()

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    result = detector.detect(frame)

    if isinstance(result, list):
        cv2.putText(frame, "No bowl detected", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    else:
        mask = result
        frame[mask == 1] = [0, 255, 0]
        cv2.putText(frame, "Bowl detected!", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Webcam Test", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:  # q 또는 ESC
        break

cap.release()
cv2.destroyAllWindows()
