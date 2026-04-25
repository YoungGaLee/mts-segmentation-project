import numpy as np
import cv2

VIEW_THRESHOLD = 0.97  # 이 값 미만이면 측면으로 판별


class Analyzer:
    def _extract_rim_contour(self, mask: np.ndarray, image: np.ndarray | None = None) -> np.ndarray | None:
        """마스크 영역에서 Canny 엣지 기반으로 rim 컨투어 추출."""
        # 마스크 영역의 bounding box
        ys, xs = np.where(mask > 0)
        if len(ys) == 0:
            return None
        y_min, y_max = int(ys.min()), int(ys.max())
        x_min, x_max = int(xs.min()), int(xs.max())
        mask_h = y_max - y_min
        mask_w = x_max - x_min

        # 원본 이미지가 있으면 컬러 엣지, 없으면 마스크 경계 엣지
        if image is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.bitwise_and(gray, gray, mask=mask)
        else:
            gray = (mask * 255).astype(np.uint8)

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 100)

        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        if not contours:
            return None

        # rim 후보: 마스크 상단 50% 내에 있고, 마스크 너비의 60% 이상을 가로지르는 컨투어
        rim_candidates = []
        for c in contours:
            if len(c) < 5:
                continue
            pts = c.reshape(-1, 2)
            c_y_min = pts[:, 1].min()
            c_x_min, c_x_max = pts[:, 0].min(), pts[:, 0].max()
            c_width = c_x_max - c_x_min

            # 상단 50% 안에 있는지
            if c_y_min > y_min + mask_h * 0.5:
                continue
            # 마스크 너비의 60% 이상 가로지르는지
            if c_width < mask_w * 0.6:
                continue

            rim_candidates.append(c)

        if not rim_candidates:
            return None

        # 가장 위쪽(y_min 최소)에 있는 컨투어 선택
        best = min(rim_candidates, key=lambda c: c.reshape(-1, 2)[:, 1].min())
        return best if len(best) >= 5 else None

    def analyze(self, mask: np.ndarray, image: np.ndarray | None = None) -> dict | list:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # Image, mode(가장 바깥 윤곽선), method(윤곽선 저장방식)

        if not contours:
            return []

        mask_contour = max(contours, key=cv2.contourArea) # 가장 큰 객체만 분석

        if len(mask_contour) < 5: # fitEllipse 실패
            return []

        # 전체 마스크로 측면 여부 판단
        ellipse_full = cv2.fitEllipse(mask_contour)
        minor_full, major_full = sorted(ellipse_full[1])
        view_ratio = minor_full / major_full

        # 측면이면 rim 컨투어로 타원 재측정 (fit_quality는 항상 마스크 컨투어 기준)
        contour = mask_contour
        rim_ellipse = None
        if view_ratio < VIEW_THRESHOLD:
            rim_contour = self._extract_rim_contour(mask, image)
            if rim_contour is not None:
                contour = rim_contour
                rim_ellipse = cv2.fitEllipse(rim_contour)

        ellipse = cv2.fitEllipse(contour)
        minor_px, major_px = sorted(ellipse[1])
        view_ratio = minor_px / major_px

        view_type = "정면" if view_ratio >= VIEW_THRESHOLD else "측면"
        mask_area = cv2.contourArea(mask_contour)
        ellipse_area = np.pi * (major_px / 2) * (minor_px / 2)
        fit_quality = mask_area / ellipse_area if ellipse_area > 0 else 1.0

        return {
            "view_type": view_type,
            "major_px": round(major_px, 2),
            "minor_px": round(minor_px, 2),
            "ratio": round(view_ratio, 4),
            "fit_quality": round(fit_quality, 4),
            "status": self._get_status(fit_quality),
            "ellipse": ellipse,
            "rim_ellipse": rim_ellipse,
        }

    def _get_status(self, fit_quality: float) -> str:
        if fit_quality >= 0.82:
            return "온전한 원형"
        if fit_quality >= 0.70:
            return "약간 찌그러짐"
        return "찌그러진 상태"
