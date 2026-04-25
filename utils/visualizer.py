import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FONT_SIZE = 28

STATUS_COLOR = {
    "온전한 원형": (0, 200, 0),
    "약간 찌그러짐": (255, 165, 0),
    "찌그러진 상태": (220, 50, 50),
}


def draw_result(image_bgr: np.ndarray, mask: np.ndarray, result: dict, card_rect=None) -> np.ndarray:
    vis = image_bgr.copy()

    vis[mask == 1] = (vis[mask == 1] * 0.6 + np.array([0, 200, 0]) * 0.4).astype("uint8")
    cv2.ellipse(vis, result["ellipse"], (0, 255, 255), 2)
    if result.get("rim_ellipse") is not None:
        cv2.ellipse(vis, result["rim_ellipse"], (0, 100, 255), 2)  # 주황색으로 rim 표시

    if card_rect is not None:
        cv2.drawContours(vis, [card_rect], 0, (0, 200, 255), 2)
        cx, cy = card_rect.mean(axis=0).astype(int)
        cv2.putText(vis, "CARD", (cx - 25, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

    vis_rgb = cv2.cvtColor(vis, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(vis_rgb)
    draw = ImageDraw.Draw(pil_img)

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()

    status = result["status"]
    color = STATUS_COLOR.get(status, (255, 255, 255))

    view_label = "정면" if result["view_type"] == "정면" else "측면"
    fit_quality = result.get("fit_quality", 0)

    lines = [
        f"촬영 방향: {view_label}",
        f"장축: {result['major_px']:.1f}px",
        f"단축: {result['minor_px']:.1f}px",
        f"fit_quality: {fit_quality:.4f}",
        f"상태: {status}",
    ]

    x, y = 20, 20
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += FONT_SIZE + 8

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
