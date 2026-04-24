import numpy as np
import cv2


class Analyzer:
    def analyze(self, mask: np.ndarray) -> dict | list:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return []

        contour = max(contours, key=cv2.contourArea)

        if len(contour) < 5:
            return []

        ellipse = cv2.fitEllipse(contour)
        minor_px, major_px = sorted(ellipse[1])

        ratio = minor_px / major_px

        return {
            "major_px": round(major_px, 2),
            "minor_px": round(minor_px, 2),
            "ratio": round(ratio, 4),
            "status": self._get_status(ratio),
            "ellipse": ellipse,
        }

    def _get_status(self, ratio: float) -> str:
        if ratio >= 0.95:
            return "온전한 원형"
        if ratio >= 0.90:
            return "약간 찌그러짐"
        return "찌그러진 상태"