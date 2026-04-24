from ultralytics import YOLO

MODEL_PATH = "models/yolov8n-seg.pt"
DATA_PATH = "dataset/data.yaml"
EPOCHS = 50
IMG_SIZE = 640
BATCH = 8

model = YOLO(MODEL_PATH)

model.train(
    data=DATA_PATH,
    epochs=EPOCHS,
    imgsz=IMG_SIZE,
    batch=BATCH,
    device="mps",
    project="runs",
    name="bowl-finetune",
)

print("학습 완료: runs/bowl-finetune/weights/best.pt")
