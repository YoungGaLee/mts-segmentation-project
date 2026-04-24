import streamlit as st
import numpy as np
import cv2
from PIL import Image

from pipeline.detector import Detector
from pipeline.analyzer import Analyzer

detector = Detector()
analyzer = Analyzer()

st.title("원형 물체 분석기")
st.caption("쟁반 또는 냄비의 지름을 측정하고 찌그러짐을 판별합니다.")

st.info("정확한 측정을 위해 **물체 바로 위에서 내려다보며** 촬영해 주세요.", icon="📷")

source = st.radio("입력 방식", ["이미지 업로드", "웹캠"])

image_bgr = None

if source == "이미지 업로드":
    uploaded = st.file_uploader("이미지를 업로드하세요", type=["jpg", "jpeg", "png"])
    if uploaded:
        pil_image = Image.open(uploaded).convert("RGB")
        image_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

else:
    captured = st.camera_input("웹캠으로 촬영하세요")
    if captured:
        pil_image = Image.open(captured).convert("RGB")
        image_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

if image_bgr is not None:
    st.image(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB), caption="입력 이미지", use_container_width=True)

    with st.spinner("분석 중..."):
        mask = detector.detect(image_bgr)

    if not isinstance(mask, np.ndarray):
        st.error("물체를 감지하지 못했습니다. 다른 이미지를 사용해 주세요.")
    else:
        result = analyzer.analyze(mask)

        if not result:
            st.error("윤곽선 분석에 실패했습니다.")
        else:
            if result["view_type"] == "측면":
                st.warning(
                    "측면에서 촬영된 이미지입니다. "
                    "정확한 지름 측정을 위해 **물체 바로 위에서** 다시 촬영해 주세요. "
                    "찌그러짐 판별은 계속 진행합니다.",
                    icon="⚠️",
                )

            st.subheader("분석 결과")
            col1, col2, col3 = st.columns(3)
            col1.metric("촬영 방향", result["view_type"])
            col2.metric("장축", f"{result['major_px']} px")
            col3.metric("단축", f"{result['minor_px']} px")

            if result["view_type"] == "정면":
                st.metric("단축/장축 비율", result["ratio"])
            else:
                st.metric("Solidity", result["solidity"])

            status = result["status"]
            if status == "온전한 원형":
                st.success(f"상태: {status}")
            elif status == "약간 찌그러짐":
                st.warning(f"상태: {status}")
            else:
                st.error(f"상태: {status}")

            vis = image_bgr.copy()
            colored_mask = np.zeros_like(vis)
            colored_mask[mask == 1] = (0, 200, 0)
            vis = cv2.addWeighted(vis, 0.7, colored_mask, 0.3, 0)
            cv2.ellipse(vis, result["ellipse"], (0, 255, 255), 2)
            st.image(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB), caption="분석 결과 시각화", use_container_width=True)
