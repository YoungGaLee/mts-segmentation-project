import numpy as np
import cv2
import torch
from ultralytics import YOLO

BOWL_CLASS_ID = 45
POT_CLASS_ID = 0


def _get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class Detector:
    def __init__(
        self,
        bowl_model_path: str = "models/yolov8n-seg.pt",
        pot_model_path: str = "runs/segment/runs/pot-finetune/weights/best.pt",
        conf_threshold: float = 0.3,
    ):
        self.device = _get_device()
        self.bowl_model = YOLO(bowl_model_path)
        self.bowl_model.to(self.device)
        self.pot_model = YOLO(pot_model_path)
        self.pot_model.to(self.device)
        self.conf_threshold = conf_threshold

    def _best_detection(self, results, target_class_id: int) -> tuple | None:
        if results.masks is None:
            return None
        best = None
        for i, cls_id in enumerate(results.boxes.cls):
            if int(cls_id) != target_class_id:
                continue
            score = float(results.boxes.conf[i])
            if score < self.conf_threshold:
                continue
            if best is None or score > best[2]:
                best = (i, results, score)
        if best is None:
            return None
        i, res, score = best
        raw_mask = res.masks.data[i].cpu().numpy()
        return raw_mask, res.names[int(res.boxes.cls[i])], score

    def detect(self, image: np.ndarray) -> tuple[np.ndarray, str, float] | list:
        bowl_res = self.bowl_model(image, verbose=False)[0]
        pot_res = self.pot_model(image, verbose=False)[0]

        bowl = self._best_detection(bowl_res, BOWL_CLASS_ID)
        pot = self._best_detection(pot_res, POT_CLASS_ID)

        if bowl is None and pot is None:
            return []

        raw_mask, class_name, conf = (
            pot if bowl is None else
            bowl if pot is None else
            (pot if pot[2] >= bowl[2] else bowl)
        )

        mask = cv2.resize(
            raw_mask,
            (image.shape[1], image.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        ).astype(np.uint8)

        return mask, class_name, conf