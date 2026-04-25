import base64
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from pipeline.detector import Detector
from pipeline.analyzer import Analyzer
from pipeline.calibration import Calibrator
from utils.visualizer import draw_result

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = Detector()
analyzer = Analyzer()
calibrator = Calibrator()


def _encode_image(image_bgr: np.ndarray) -> str:
    _, buffer = cv2.imencode(".jpg", image_bgr)
    return base64.b64encode(buffer).decode("utf-8")


def _build_response(image_bgr: np.ndarray, mask: np.ndarray, result: dict) -> dict:
    px_per_cm = calibrator.calibrate(image_bgr)
    vis = draw_result(image_bgr, mask, result)
    response = {
        "detected": True,
        "analyzed": True,
        "view_type": result["view_type"],
        "major_px": result["major_px"],
        "minor_px": result["minor_px"],
        "ratio": result.get("ratio"),
        "solidity": result.get("solidity"),
        "status": result["status"],
        "image": _encode_image(vis),
    }
    if px_per_cm:
        response["major_cm"] = calibrator.px_to_cm(result["major_px"], px_per_cm)
        response["minor_cm"] = calibrator.px_to_cm(result["minor_px"], px_per_cm)
    return response


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    mask = detector.detect(image_bgr)
    if not isinstance(mask, np.ndarray):
        return {"detected": False}

    result = analyzer.analyze(mask)
    if not result:
        return {"detected": True, "analyzed": False}

    return _build_response(image_bgr, mask, result)


@app.websocket("/ws/webcam")
async def webcam_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            frame_bytes = base64.b64decode(data)
            nparr = np.frombuffer(frame_bytes, np.uint8)
            image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image_bgr is None:
                continue

            mask = detector.detect(image_bgr)
            if not isinstance(mask, np.ndarray):
                await websocket.send_json({"detected": False})
                continue

            result = analyzer.analyze(mask)
            if not result:
                await websocket.send_json({"detected": True, "analyzed": False})
                continue

            await websocket.send_json(_build_response(image_bgr, mask, result))

    except WebSocketDisconnect:
        pass
