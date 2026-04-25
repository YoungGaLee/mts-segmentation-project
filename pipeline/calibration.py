import numpy as np
import cv2


class Calibrator:
    CARD_LONG_CM = 8.56
    CARD_SHORT_CM = 5.40
    CARD_RATIO = CARD_LONG_CM / CARD_SHORT_CM  # ≈ 1.585
    RATIO_TOLERANCE = 0.1
    MIN_AREA_PX = 1000

    def calibrate(self, image: np.ndarray) -> float | None:
        """이미지에서 신용카드를 감지해 px_per_cm 반환. 실패 시 None."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        best_long_px = None
        best_area = 0

        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            if len(approx) != 4:
                continue

            rect = cv2.minAreaRect(contour)
            w, h = rect[1]

            if w == 0 or h == 0:
                continue

            long_px = max(w, h)
            short_px = min(w, h)
            area = long_px * short_px

            if area < self.MIN_AREA_PX:
                continue

            ratio = long_px / short_px
            if abs(ratio - self.CARD_RATIO) > self.RATIO_TOLERANCE:
                continue

            if area > best_area:
                best_area = area
                best_long_px = long_px

        if best_long_px is None:
            return None

        return best_long_px / self.CARD_LONG_CM

    def px_to_cm(self, px: float, px_per_cm: float) -> float:
        """픽셀값을 cm로 변환."""
        return round(px / px_per_cm, 1)
