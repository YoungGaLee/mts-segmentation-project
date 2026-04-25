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


def draw_result(image_bgr: np.ndarray, mask: np.ndarray, result: dict) -> np.ndarray:
    vis = image_bgr.copy()

    vis[mask == 1] = (vis[mask == 1] * 0.6 + np.array([0, 200, 0]) * 0.4).astype("uint8")
    cv2.ellipse(vis, result["ellipse"], (0, 255, 255), 2)

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
    metric_key = "ratio" if result["view_type"] == "정면" else "solidity"
    metric_val = result.get("ratio") if result["view_type"] == "정면" else result.get("solidity")

    lines = [
        f"촬영 방향: {view_label}",
        f"장축: {result['major_px']:.1f}px",
        f"단축: {result['minor_px']:.1f}px",
        f"{metric_key}: {metric_val:.4f}",
        f"상태: {status}",
    ]

    x, y = 20, 20
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += FONT_SIZE + 8

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
