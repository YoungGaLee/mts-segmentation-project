import numpy as np
import cv2
import torch
from ultralytics import YOLO

BOWL_CLASS_ID = 45


def _get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class Detector:
    def __init__(self, model_path: str = "models/yolov8n-seg.pt", conf_threshold: float = 0.3):
        self.model = YOLO(model_path)
        self.device = _get_device()
        self.model.to(self.device)
        self.conf_threshold = conf_threshold

    def detect(self, image: np.ndarray) -> np.ndarray | list:

        results = self.model(image, verbose=False)[0]

        if results.masks is None:
            return []

        best_mask = None
        best_area = 0

        for i, cls_id in enumerate(results.boxes.cls):
            if int(cls_id) != BOWL_CLASS_ID:
                continue

            score = float(results.boxes.conf[i])
            if score < self.conf_threshold:
                continue

            raw_mask = results.masks.data[i].cpu().numpy()
            mask = cv2.resize(
                raw_mask,
                (image.shape[1], image.shape[0]),
                interpolation=cv2.INTER_NEAREST,
            ).astype(np.uint8)

            area = int(mask.sum())
            if area > best_area:
                best_area = area
                best_mask = mask

        if best_mask is None:
            return []

        return best_mask #가장 큰 객체만 인식