# 원형 물체 분석기 (쟁반/냄비 지름 측정 및 찌그러짐 판별)

쟁반 또는 냄비 이미지를 업로드하거나 웹캠으로 촬영하면 지름(px/cm)을 측정하고 찌그러짐 여부를 판별합니다.

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| Language | Python 3.10+ |
| AI 모델 | YOLOv8-seg (COCO pretrained + 냄비 파인튜닝) |
| 이미지 처리 | OpenCV |
| 백엔드 | FastAPI + Uvicorn |
| 프론트엔드 | React + Vite |

---

## 사전 요구사항

- Python 3.10 이상
- Node.js 18 이상

---

## 설치 및 실행

### 1. 저장소 클론

```bash
git clone https://github.com/younggalee/mts-segmentation-project.git
cd mts-segmentation-project
git checkout dev
```

### 2. 백엔드 설정

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 의존성 설치
pip install fastapi uvicorn python-multipart ultralytics opencv-python torch torchvision numpy pillow
```

> Mac에서 MPS(GPU) 가속이 자동으로 활성화됩니다. CUDA GPU가 있는 경우도 자동 감지합니다.

### 3. 프론트엔드 설정

```bash
cd frontend
npm install
cd ..
```

---

## 실행

터미널 두 개를 열고 각각 실행합니다.

**터미널 1 — 백엔드**

```bash
source venv/bin/activate
uvicorn api:app --reload
```

백엔드가 `http://localhost:8000` 에서 실행됩니다.

**터미널 2 — 프론트엔드**

```bash
cd frontend
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

---

## 모델 파일

| 파일 | 설명 |
|------|------|
| `models/yolov8n-seg.pt` | COCO pretrained (쟁반/그릇 인식) |
| `runs/segment/runs/pot-finetune/weights/best.pt` | 냄비 파인튜닝 모델 |

두 파일 모두 저장소에 포함되어 있습니다.

---

## 주요 기능

### 이미지 업로드 모드
- JPEG, PNG 이미지를 드래그&드롭 또는 클릭으로 업로드
- 결과: 지름(px/cm), 찌그러짐 상태, 분석 이미지 시각화

### 웹캠 모드
- 실시간 촬영 및 분석 (WebSocket 통신)
- 300ms 간격으로 프레임 전송

### cm 단위 변환 (캘리브레이션)
- 신용카드(85.6×54mm)를 물체 옆에 두고 촬영 시 자동으로 px → cm 변환
- 카드 미감지 시 px 단위만 표시

### 찌그러짐 판별 기준

| 단축/장축 비율 | 상태 |
|------|------|
| 0.95 이상 | 온전한 원형 |
| 0.90 ~ 0.95 | 약간 찌그러짐 |
| 0.90 미만 | 찌그러진 상태 |

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/analyze` | 이미지 업로드 분석 |
| WebSocket | `/ws/webcam` | 웹캠 실시간 분석 |
