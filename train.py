from ultralytics import YOLO

MODEL_PATH = "models/yolov8n-seg.pt"
DATA_PATH = "/Users/younggalee/Downloads/pot-dataset/data.yaml"
EPOCHS = 70
IMG_SIZE = 640
BATCH = 8

model = YOLO(MODEL_PATH)

model.train(
    data=DATA_PATH,
    epochs=EPOCHS,
    imgsz=IMG_SIZE,
    batch=BATCH,
    device="mps",
    patience=20,
    project="runs",
    name="pot-finetune",
)

print("학습 완료: runs/pot-finetune/weights/best.pt")
