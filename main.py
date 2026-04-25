import threading
import time

import streamlit as st
import numpy as np
import cv2
from PIL import Image
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av

from pipeline.detector import Detector
from pipeline.analyzer import Analyzer
from utils.visualizer import draw_result

detector = Detector()
analyzer = Analyzer()


def _render_metrics(col, result):
    with col:
        st.subheader("분석 결과")

        if result["view_type"] == "측면":
            st.warning("측면 촬영입니다. 위에서 촬영하면 더 정확합니다.", icon="⚠️")

        st.metric("촬영 방향", result["view_type"])
        st.metric("장축", f"{result['major_px']:.1f} px")
        st.metric("단축", f"{result['minor_px']:.1f} px")

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


st.set_page_config(layout="centered")

st.markdown("""
<style>
.block-container { max-width: 80%; padding-left: 2rem; padding-right: 2rem; }

iframe[title="streamlit_webrtc.component"] {
    aspect-ratio: 1 / 1;
    width: 100% !important;
    height: auto !important;
}

[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #ccc;
    border-radius: 12px;
    padding: 2.5rem 1rem;
    text-align: center;
    background-color: #f9f9f9;
    cursor: pointer;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #4A90E2;
    background-color: #f0f5ff;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    font-size: 1rem;
    color: #444;
}
</style>
""", unsafe_allow_html=True)

st.title("원형 물체 분석기")
st.caption("쟁반 또는 냄비의 지름을 측정하고 찌그러짐을 판별합니다.")
st.info("정확한 측정을 위해 **물체 바로 위에서 내려다보며** 촬영해 주세요.", icon="📷")

tab_upload, tab_cam = st.tabs(["이미지 업로드", "웹캠 촬영"])

with tab_upload:
    uploaded = st.file_uploader(
        "클릭하거나 이미지를 여기에 끌어다 놓으세요",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )
    st.caption("JPEG, PNG 지원")

    if uploaded:
        pil_image = Image.open(uploaded).convert("RGB")
        image_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        with st.spinner("분석 중..."):
            mask = detector.detect(image_bgr)

        if not isinstance(mask, np.ndarray):
            st.error("물체를 감지하지 못했습니다. 다른 이미지를 사용해 주세요.")
        else:
            result = analyzer.analyze(mask)
            if not result:
                st.error("윤곽선 분석에 실패했습니다.")
            else:
                vis = draw_result(image_bgr, mask, result)
                col_img, col_result = st.columns(2)
                with col_img:
                    st.image(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB), caption="분석 이미지", use_container_width=True)
                _render_metrics(col_result, result)

with tab_cam:
    class BowlAnalyzer(VideoProcessorBase):
        def __init__(self):
            self.result = None
            self._lock = threading.Lock()

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            image_bgr = frame.to_ndarray(format="bgr24")
            mask = detector.detect(image_bgr)

            if not hasattr(mask, "shape"):
                cv2.putText(image_bgr, "No bowl detected", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                with self._lock:
                    self.result = None
                return av.VideoFrame.from_ndarray(image_bgr, format="bgr24")

            result = analyzer.analyze(mask)
            if not result:
                return av.VideoFrame.from_ndarray(image_bgr, format="bgr24")

            with self._lock:
                self.result = result

            vis = draw_result(image_bgr, mask, result)
            return av.VideoFrame.from_ndarray(vis, format="bgr24")

    col_cam, col_result = st.columns(2)

    with col_cam:
        ctx = webrtc_streamer(
            key="bowl",
            video_processor_factory=BowlAnalyzer,
            media_stream_constraints={"video": True, "audio": False},
            translations={
                "start": "시작",
                "stop": "중지",
                "select_device": "",
            },
        )

    result_placeholder = col_result.empty()

    if ctx.state.playing and ctx.video_processor:
        with ctx.video_processor._lock:
            result = ctx.video_processor.result
        if result:
            with result_placeholder.container():
                _render_metrics(col_result, result)
        time.sleep(0.5)
        st.rerun()
