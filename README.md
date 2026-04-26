# 원형 물체 분석기
> 이미지 또는 웹캠으로 냄비·그릇의 **지름 측정 + 찌그러짐 판별**을 수행하는 컴퓨터 비전 프로젝트

</br>

## 🎯 주요 기능
* 지름 측정 (px / cm)
* 찌그러짐 자동 판별
* 웹캠 실시간 분석 (WebSocket 기반)
* 신용카드 기반 자동 캘리브레이션

</br>

### 시연 영상

[![Demo](https://img.youtube.com/vi/y45FGJO3G0c/0.jpg)](https://youtube.com/watch?v=y45FGJO3G0c)

</br>

## 결과 화면
### 성공
#### [ 실시간 웹캠 ]
<img width="1218" height="1772" alt="image" src="https://github.com/user-attachments/assets/cc0c58cc-8c63-4776-9ebe-1203ef9f41fb" />

<br>

#### [ 이미지 업로드 ]

<img width="1182" height="2704" alt="image" src="https://github.com/user-attachments/assets/e4bae89a-dcae-45ec-964b-0118fa2f95de" />

<br>

<br>

---

<br>

### 실패

<img width="1274" height="3034" alt="image" src="https://github.com/user-attachments/assets/34652979-5b5e-451f-8347-b5bc8548ef3b" />


<br>

<br>

## ⚠️  한계 및 보완점

#### 1. 측면 촬영 시 입구 지름 측정 오차

현재 파이프라인은 객체 전체 마스크를 기반으로 타원을 fitting하기 때문에, 측면에서 촬영할 경우 냄비 몸통과 입구가 뒤섞여 오차가 발생합니다.     
(실측 11cm 그릇이 약 12.5cm로 측정되는 경우 확인)

- **보완 방향**

  > 입구 테두리(rim)를 별도 클래스로 정의하고 polygon 어노테이션으로 파인튜닝하면 정확도를 크게 향상시킬 수 있습니다. 다만 1,000장 이상의 데이터에 수작업 라벨링이 필요하여 시간부족으로 이번 프로젝트에서는 적용하지 못했습니다.

</br>

#### 2. 높이 차이로 인한 원근 오차

카드와 냄비를 바닥에 두고 위에서 촬영할 경우, 냄비 높이만큼 카메라 거리가 달라져 냄비가 실제보다 크게 측정됩니다.

- **보완 방향**

  > 현재 상황에서는 카드를 냄비 입구와 같은 높이에 맞춰 측정하면 비교적 실제와 비슷하게 측정할 수 있습니다. 추후 깊이 추정(depth estimation) 모델을 연계해 원근 보정을 자동화하는 방법을 고려할 수 있습니다.

</br>

#### 3. 찌그러짐 판단 미흡

- **보완 방향**

  > 현재 사용하고 있는 fitEllipse에 의존하지 않는 원형도(Circularity) 지표를 도입하면 보다 안정적인 판별이 가능할 것으로 예상합니다.

</br>

## 🧱 기술 스택

| 구분 | 기술 |
|---------|----------------|
| AI 모델 | YOLOv8-seg (Ultralytics) |
| 이미지 처리 | OpenCV |
| 딥러닝 프레임워크 | PyTorch |
| 백엔드 | FastAPI + Uvicorn |
| 프론트엔드 | React 18 + Vite |
| 실시간 통신 | WebSocket |


</br>

## ⚙️ 설치 및 실행

<details>

<summary> 펼치기 </summary>


### Step 1 &nbsp; &nbsp; 저장소 클론

```bash
git clone https://github.com/younggalee/mts-segmentation-project.git
cd mts-segmentation-project
git checkout dev
```

</br>

### Step 2 &nbsp; &nbsp;  백엔드 설치

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# 패키지 설치
pip install fastapi uvicorn python-multipart \
            ultralytics opencv-python \
            torch torchvision numpy pillow
```

</br>

### Step 3 &nbsp; &nbsp;  프론트엔드 설치

```bash
cd frontend
npm install
cd ..
```

</br>

### Step 4 &nbsp; &nbsp;  실행
**터미널을 2개 열고 각각 아래 명령어를 실행하세요.**

</br>

#### 터미널 A (백엔드)
```bash
source venv/bin/activate
uvicorn api:app --reload
```
`http://localhost:8000` 에서 실행됩니다.

</br>

#### 터미널 B (프론트엔드)
```bash
cd frontend
npm run dev
```

</br>

**브라우저에서 `http://localhost:5173` 로 접속하세요.**

</details>

</br>

</br>

</br>

## 프로젝트 상세설명

### 🔄 동작 흐름 (pipeline)

#### 1. 객체 감지 &nbsp; Detector
COCO pretrained 모델(`bowl`, ID 45)과 냄비 파인튜닝 모델(`pot`, ID 0)을 동시에 추론합니다.  
두 모델 모두 감지에 성공하면 **confidence가 높은 결과를 선택**하고, 해당 객체의 **픽셀 마스크**를 다음 단계로 전달합니다.

</br>

#### 2. 캘리브레이션 &nbsp; Calibrator
이미지에서 **신용카드(85.6×54mm)** 를 자동으로 검출해 `px_per_cm` 비율을 계산합니다.  
- Canny 엣지 기반 사각형 윤곽선 검출  
- 가로·세로 비율(1.585)로 카드 여부 검증  

카드가 감지되지 않으면 이전 프레임 값을 캐싱해 사용하며, 초기부터 카드가 없는 경우에는 **px 단위 결과만 반환**합니다.

</br>

#### 3. 지름 측정 및 찌그러짐 판별 &nbsp; Analyzer
마스크 윤곽선에 `fitEllipse`를 적용해 장축(major axis)과 단축(minor axis)을 계산합니다.

- 단축/장축 비율로 **정면 vs 측면 촬영 여부 판단**
- 측면으로 판정되면 Canny 엣지에서 **rim 컨투어 재추출 후 재측정**
- `fit_quality = 마스크 면적 / 타원 면적` 기준으로 찌그러짐 판별

값이 **1에 가까울수록 온전한 원형**입니다.

</br>

#### 4. 시각화 및 응답 &nbsp; Visualizer → API
- 마스크 오버레이, 타원, 카드 영역을 이미지에 렌더링  
- 결과 이미지를 **base64로 인코딩**

</br>

</br>

## 기술 선택 이유

<details>

<summary> AI 기반 접근 방식 </summary>

</br>

OpenCV 만을 이용해서도 원을 인식할 수 있지만 (HoughCircles, fitEllipse 활용)
배경이 달라지거나, 촬영 각도가 달라지는 환경에서는 적합하지 않다고 생각했습니다.
이번 과제는 정해진 조건은 없었지만 카메라가 고정되어있지 않은 상황이 자연스럽다 생각되어 다양한 환경에서도 객체를 안정적으로 인식할 수 있는 AI 기반 접근 방식을 도입했습니다.
</details>

<details>
<summary> YOLOv8-seg </summary>

</br>

원형 객체의 정확한 지름을 측정하기 위해서는 객체의 형태를 그대로 추출할 수 있는 Segmentation 모델이 필요하다 생각했고, 웹캠으로 실시간 처리가 가능할만큼 가벼우면서도 추가학습없이도 좋은 성능을 내는 pretrained 모델을 찾았습니다. 그 결과 COCO 데이터셋으로 pretrained + YOLOv8의 nano segmentation 버전인 yolov8n-seg를 사용하게 되었습니다. 
</details>


<details>

<summary> fine-tuning한 이유  </summary>

</br> 

안타깝게도에는 `bowl` 클래스는 존재하지만, 냄비(`pot`)는 별도의 클래스로 포함되어 있지 않습니다.    
이로 인해 냄비 객체에 대한 인식 성능이 충분하지 않았으며, 이를 개선하기 위해 냄비 이미지를 직접 수집·라벨링을 진행하였습니다.


`pot` 클래스로 약 700장의 데이터를 활용해 파인튜닝을 진행했습니다.



Pot Dataset : https://drive.google.com/drive/folders/10221cC1ipBsRfpemoyNBq103g6jiOnjs?usp=drive_link

</br> 

또한 `bowl` 데이터 역시 대부분 측면에서 촬영된 이미지로 구성되어 있어,위에서 내려다보는(top-view) 환경에서는 인식률이 떨어지는 한계가 있습니다. 실제로 과제에서 구현한 서비스에서도 이러한 문제가 발생하기도 하였습니다. 



</br>

</details>

<details>

<summary> 신용카드를 캘리브레이션 기준으로 사용한 이유  </summary>

</br>

카메라마다 해상도와 촬영 거리가 달라 고정된 px/cm 값을 쓸 수 없었고, 신용카드가 국제규격이 정해져서 기준 물체로 활용될 수 있다는 걸 알게 되었습니다.
따라서 물체만이 인식되는 상황에서는 px값을 출력하다가 카드가 인식되면 자동으로 캘리브레이션이 되도록 구현하였습니다. 

</br>

</details>

<details>
  <summary> WebSocket 사용한 이유  </summary>
  
</br>
  
REST API 폴링 방식은 클라이언트가 매 요청마다 새 HTTP 연결을 맺어 레이턴시가 높아집니다. WebSocket은 연결을 한 번 수립한 뒤 프레임을 연속으로 전송하므로, 300ms 간격의 실시간 분석에 적합합니다. 또한 서버가 결과를 비동기로 push할 수 있어 프레임 처리 지연이 누적되지 않습니다.

</br>

</details>

</br>

</br>





</br>

### 프로젝트 구조

```
mts-segmentation-project/
├── api.py                   # FastAPI 진입점
├── requirements.txt
├── train.py                 # YOLOv8 파인튜닝 스크립트
├── pipeline/
│   ├── detector.py          # YOLOv8-seg 추론
│   ├── analyzer.py          # 지름 측정 · 찌그러짐 판별
│   └── calibration.py       # 신용카드 기준 px→cm 변환
├── utils/
│   └── visualizer.py        # 결과 시각화
├── models/
│   └── yolov8n-seg.pt       # COCO pretrained 모델
├── runs/
│   └── segment/runs/pot-finetune/weights/best.pt   # 냄비 파인튜닝 모델
├── dataset/                 # 파인튜닝용 데이터셋
└── frontend/                # React + Vite 프론트엔드
    └── src/
        └── App.jsx
```

</br>

### 파인튜닝 데이터셋
Pot Dataset : https://drive.google.com/drive/folders/10221cC1ipBsRfpemoyNBq103g6jiOnjs?usp=drive_link

