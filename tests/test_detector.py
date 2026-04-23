from pipeline.detector import Detector
import numpy as np

detector = Detector()

dummy = np.zeros((640, 640, 3), dtype=np.uint8)
result = detector.detect(dummy)
print("결과:", result)
print("정상 동작" if result == [] else f"마스크 shape: {result.shape}")
