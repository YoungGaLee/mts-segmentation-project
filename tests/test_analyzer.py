import cv2
import numpy as np
from pipeline.detector import Detector
from pipeline.analyzer import Analyzer

detector = Detector()
analyzer = Analyzer()

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    mask = detector.detect(frame)

    if not hasattr(mask, 'shape'):
        cv2.putText(frame, "No bowl detected", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    else:
        result = analyzer.analyze(mask)

        if not result:
            cv2.putText(frame, "Contour analysis failed", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        else:
            frame[mask == 1] = (frame[mask == 1] * 0.6 + np.array([0, 200, 0]) * 0.4).astype('uint8')
            cv2.ellipse(frame, result["ellipse"], (0, 255, 255), 2)

            view = "Top" if result["view_type"] == "정면" else "Side"
            status_map = {"온전한 원형": "Perfect", "약간 찌그러짐": "Slightly dented", "찌그러진 상태": "Dented"}
            status = status_map[result["status"]]
            major = result["major_px"]
            minor = result["minor_px"]
            metric_val = result["ratio"] if result["view_type"] == "정면" else result["solidity"]
            metric_key = "ratio" if result["view_type"] == "정면" else "solidity"

            lines = [
                f"View  : {view}",
                f"Status: {status}",
                f"Major : {major:.1f}px",
                f"Minor : {minor:.1f}px",
                f"{metric_key}: {metric_val:.4f}",
            ]

            color = (0, 255, 0) if status == "Perfect" else (0, 165, 255) if status == "Slightly dented" else (0, 0, 255)
            for i, line in enumerate(lines):
                cv2.putText(frame, line, (20, 40 + i * 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Pipeline Test", frame)

    if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
        break

cap.release()
cv2.destroyAllWindows()
