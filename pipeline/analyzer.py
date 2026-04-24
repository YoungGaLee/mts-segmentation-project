import numpy as np
import cv2

VIEW_THRESHOLD = 0.6  # 이 값 미만이면 측면으로 판별


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
        view_ratio = minor_px / major_px

        if view_ratio >= VIEW_THRESHOLD:
            return self._analyze_top(contour, ellipse, major_px, minor_px, view_ratio)
        else:
            return self._analyze_side(contour, ellipse, major_px, minor_px, view_ratio)

    def _analyze_top(self, contour, ellipse, major_px, minor_px, ratio) -> dict:
        return {
            "view_type": "정면",
            "major_px": round(major_px, 2),
            "minor_px": round(minor_px, 2),
            "ratio": round(ratio, 4),
            "status": self._get_status_top(ratio),
            "ellipse": ellipse,
        }

    def _analyze_side(self, contour, ellipse, major_px, minor_px, view_ratio) -> dict:
        area = cv2.contourArea(contour)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 1.0

        return {
            "view_type": "측면",
            "major_px": round(major_px, 2),
            "minor_px": round(minor_px, 2),
            "ratio": round(view_ratio, 4),
            "solidity": round(solidity, 4),
            "status": self._get_status_side(solidity),
            "ellipse": ellipse,
        }

    def _get_status_top(self, ratio: float) -> str:
        if ratio >= 0.95:
            return "온전한 원형"
        if ratio >= 0.90:
            return "약간 찌그러짐"
        return "찌그러진 상태"

    def _get_status_side(self, solidity: float) -> str:
        if solidity >= 0.97:
            return "온전한 원형"
        if solidity >= 0.93:
            return "약간 찌그러짐"
        return "찌그러진 상태"
