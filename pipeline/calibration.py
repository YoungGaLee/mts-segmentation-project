import numpy as np
import cv2


class Calibrator:
    CARD_LONG_CM = 8.56
    CARD_SHORT_CM = 5.40
    CARD_RATIO = CARD_LONG_CM / CARD_SHORT_CM  # ≈ 1.585
    RATIO_TOLERANCE = 0.18
    MIN_AREA_RATIO = 0.002  # 이미지 전체 면적 대비 최소 카드 면적

    def __init__(self):
        self._cached_px_per_cm: float | None = None

    def calibrate(self, image: np.ndarray) -> float | None:
        """이미지에서 신용카드를 감지해 px_per_cm 반환. 실패 시 None."""
        h, w = image.shape[:2]
        min_area = w * h * self.MIN_AREA_RATIO

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 조명 조건에 따라 두 임계값 모두 시도
        candidates = []
        for low, high in [(30, 100), (50, 150), (80, 200)]:
            edges = cv2.Canny(blurred, low, high)
            best = self._find_card(edges, min_area)
            if best:
                candidates.append(best)

        if not candidates:
            return self._cached_px_per_cm

        best_long_px = max(candidates)
        self._cached_px_per_cm = best_long_px / self.CARD_LONG_CM
        return self._cached_px_per_cm

    def _find_card(self, edges: np.ndarray, min_area: float) -> float | None:
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        best_long_px = None
        best_area = 0

        for contour in contours:
            if not cv2.isContourConvex(cv2.convexHull(contour)):
                continue

            peri = cv2.arcLength(contour, True)
            # 여러 epsilon으로 시도해 4꼭짓점이 나오는 경우 탐색
            approx = None
            for eps in [0.02, 0.03, 0.04, 0.05]:
                a = cv2.approxPolyDP(contour, eps * peri, True)
                if len(a) == 4:
                    approx = a
                    break
            if approx is None:
                continue

            rect = cv2.minAreaRect(contour)
            rw, rh = rect[1]
            if rw == 0 or rh == 0:
                continue

            long_px = max(rw, rh)
            short_px = min(rw, rh)
            area = long_px * short_px

            if area < min_area:
                continue

            ratio = long_px / short_px
            if abs(ratio - self.CARD_RATIO) > self.RATIO_TOLERANCE:
                continue

            if area > best_area:
                best_area = area
                best_long_px = long_px

        return best_long_px

    def px_to_cm(self, px: float, px_per_cm: float) -> float:
        """픽셀값을 cm로 변환."""
        return round(px / px_per_cm, 1)
