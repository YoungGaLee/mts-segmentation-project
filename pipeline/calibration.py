import numpy as np
import cv2

SCALE = 50  # 보정 공간에서 1cm = 50px


class Calibrator:
    CARD_LONG_CM = 8.56
    CARD_SHORT_CM = 5.40
    CARD_W_PX = int(CARD_LONG_CM * SCALE)  # 428px
    CARD_H_PX = int(CARD_SHORT_CM * SCALE)  # 270px
    MIN_AREA_RATIO = 0.003
    MAX_AREA_RATIO = 0.4
    # 원근 왜곡을 허용하기 위해 비율 허용오차를 넓게
    RATIO_TOLERANCE = 0.25

    def __init__(self):
        self._cached_px_per_cm: float | None = None
        self._cached_M: np.ndarray | None = None  # perspective transform 행렬
        self.last_card_rect: np.ndarray | None = None

    def calibrate(self, image: np.ndarray) -> float | None:
        h, w = image.shape[:2]
        min_area = w * h * self.MIN_AREA_RATIO
        max_area = w * h * self.MAX_AREA_RATIO

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        best_corners = None
        best_area = 0
        for low, high in [(30, 100), (50, 150), (80, 200)]:
            edges = cv2.Canny(blurred, low, high)
            corners, area = self._find_card_corners(edges, min_area, max_area)
            if corners is not None and area > best_area:
                best_area = area
                best_corners = corners

        if best_corners is None:
            self.last_card_rect = None  # 감지 안 되면 표시 제거
            return self._cached_px_per_cm

        ordered = self._order_corners(best_corners)
        dst = np.array([
            [0, 0],
            [self.CARD_W_PX - 1, 0],
            [self.CARD_W_PX - 1, self.CARD_H_PX - 1],
            [0, self.CARD_H_PX - 1],
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(ordered, dst)
        self._cached_M = M
        self.last_card_rect = best_corners.astype(int)

        # 원본 이미지에서 카드 장변의 실제 픽셀 크기로 px_per_cm 계산
        top    = np.linalg.norm(ordered[1] - ordered[0])
        bottom = np.linalg.norm(ordered[2] - ordered[3])
        long_px = (top + bottom) / 2
        self._cached_px_per_cm = float(long_px / self.CARD_LONG_CM)
        return self._cached_px_per_cm

    @property
    def transform_matrix(self) -> np.ndarray | None:
        return self._cached_M

    def _order_corners(self, pts: np.ndarray) -> np.ndarray:
        pts = pts.reshape(4, 2).astype(np.float32)
        s = pts.sum(axis=1)
        d = np.diff(pts, axis=1).ravel()
        return np.array([
            pts[np.argmin(s)],   # 좌상
            pts[np.argmin(d)],   # 우상
            pts[np.argmax(s)],   # 우하
            pts[np.argmax(d)],   # 좌하
        ], dtype=np.float32)

    def _find_card_corners(self, edges: np.ndarray, min_area: float, max_area: float) -> tuple:
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        best_corners = None
        best_area = 0

        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = None
            for eps in [0.02, 0.03, 0.04, 0.05, 0.06]:
                a = cv2.approxPolyDP(contour, eps * peri, True)
                if len(a) == 4:
                    approx = a
                    break
            if approx is None:
                continue

            pts = approx.reshape(4, 2).astype(float)
            s = pts.sum(axis=1)
            d = np.diff(pts, axis=1).ravel()
            ordered = pts[[np.argmin(s), np.argmin(d), np.argmax(s), np.argmax(d)]]

            top    = np.linalg.norm(ordered[1] - ordered[0])
            right  = np.linalg.norm(ordered[2] - ordered[1])
            bottom = np.linalg.norm(ordered[3] - ordered[2])
            left   = np.linalg.norm(ordered[0] - ordered[3])

            width  = (top + bottom) / 2
            height = (left + right) / 2
            if width == 0 or height == 0:
                continue

            long_px  = max(width, height)
            short_px = min(width, height)
            area = cv2.contourArea(approx)

            if not (min_area <= area <= max_area):
                continue

            ratio = long_px / short_px
            if abs(ratio - (self.CARD_LONG_CM / self.CARD_SHORT_CM)) > self.RATIO_TOLERANCE:
                continue

            if area > best_area:
                best_area = area
                best_corners = pts.astype(np.float32)

        return best_corners, best_area

    def px_to_cm(self, px: float, px_per_cm: float) -> float:
        return round(px / px_per_cm, 1)
