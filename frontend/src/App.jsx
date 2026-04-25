import { useState, useRef, useCallback, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_BASE = API_BASE.replace(/^http/, 'ws')

const STATUS_COLOR = {
  '온전한 원형': '#22c55e',
  '약간 찌그러짐': '#f97316',
  '찌그러진 상태': '#ef4444',
}


function LimitationNote() {
  return (
    <div className="limitation-note">
      <h4>💡 한계 및 개선 방향</h4>
      <p>
        현재 파이프라인에서는 냄비(또는 그릇)의 원형 입구(rim)를 별도로 추출하지 못하고,
        객체 전체 마스크를 기반으로 지름을 산출하고 있습니다.
        이로 인해 지름 측정값에 오차가 발생하고 있습니다.
        (살제 11cm인 그릇이 약 12.5cm로 출력됨. 케이스에 따라 더 큰 오차발생예상)
      </p>
      <p>
        이를 개선하기 위해서는 입구 테두리(rim)를 별도의 클래스로 정의하고, 해당 영역에 대한 polygon 어노테이션을 추가하여 모델을 파인튜닝하면 지름 정확도를 크게 향상시킬 수 있을 것이라 예상됩니다.
      </p>
      <p>
        Roboflow 등 클라우드 라벨링 서비스에서 bowl/pot 전체 영역의 자동 segmentation은 지원하지만,
        <strong> rim polygon 라벨링은 자동화가 불가능하여 수작업이 요구되어 시간 제약으로 인해 실행하지 못했습니다.</strong>
      </p>
    </div>
  )
}

function ResultPanel({ result }) {
  const isPot = result.class_name === 'pot'
  const diameter = isPot
    ? (result.minor_cm != null ? `${result.minor_cm} cm` : `${result.minor_px?.toFixed(1)} px`)
    : (result.major_cm != null ? `${result.major_cm} cm` : `${result.major_px?.toFixed(1)} px`)

  return (
    <div className="result-panel">
      <h3>분석 결과</h3>

      {result.view_type === '측면' && (
        <div className="warning">⚠️ 측면 촬영입니다. 위에서 촬영하면 더 정확하게 측정가능합니다.</div>
      )}

      <div className="metrics">
        <div className="metric">
          <span className="label">인식 클래스</span>
          <span className="value">{result.class_name} ({result.conf}%)</span>
        </div>
        <div className="metric">
          <span className="label">지름</span>
          <span className="value">{diameter}</span>
        </div>
        <div className="metric">
          <span className="label">상태</span>
          <span className="value" style={{ color: STATUS_COLOR[result.status] }}>{result.status}</span>
        </div>
        {result.major_cm == null && (
          <div className="info-msg">💳 카드를 주변에 두면 지름의 길이(cm)를 알 수 있습니다</div>
        )}
      </div>
    </div>
  )
}

function UploadTab() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef()

  const handleFile = async (file) => {
    if (!file) return
    setLoading(true)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/analyze`, { method: 'POST', body: formData })
      const data = await res.json()
      setResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0])
  }, [])

  return (
    <div>
      <div
        className={`dropzone ${dragOver ? 'dragover' : ''}`}
        onClick={() => inputRef.current.click()}
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
      >
        <div className="upload-icon">⬆</div>
        <p>클릭하거나 이미지를 여기에 끌어다 놓으세요</p>
        <p className="sub">JPEG, PNG 지원</p>
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      {loading && <div className="loading">분석 중...</div>}

      {result && (
        result.detected === false ? (
          <div className="error-msg">물체를 감지하지 못했습니다.</div>
        ) : result.analyzed === false ? (
          <div className="error-msg">윤곽선 분석에 실패했습니다.</div>
        ) : (
          <>
            <div className="result-layout">
              <img src={`data:image/jpeg;base64,${result.image}`} alt="분석 결과" className="result-img" />
              <ResultPanel result={result} />
            </div>
            {result.major_cm != null && <LimitationNote />}
          </>
        )
      )}
    </div>
  )
}

function WebcamTab() {
  const videoRef = useRef()
  const canvasRef = useRef()
  const wsRef = useRef()
  const intervalRef = useRef()
  const [active, setActive] = useState(false)
  const [connected, setConnected] = useState(false)
  const [result, setResult] = useState(null)
  const [visImage, setVisImage] = useState(null)

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    videoRef.current.srcObject = stream
    await videoRef.current.play()
    setActive(true)

    const ws = new WebSocket(`${WS_BASE}/ws/webcam`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      intervalRef.current = setInterval(() => {
        if (ws.readyState !== WebSocket.OPEN) return
        const canvas = canvasRef.current
        const video = videoRef.current
        if (!canvas || !video || video.videoWidth === 0) return
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        canvas.getContext('2d').drawImage(video, 0, 0)
        const b64 = canvas.toDataURL('image/jpeg', 0.92).split(',')[1]
        ws.send(b64)
      }, 300)
    }

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      setResult(data)
      setVisImage(data.analyzed ? data.image : null)
    }

    ws.onerror = () => setConnected(false)
    ws.onclose = () => setConnected(false)
  }

  const stop = () => {
    clearInterval(intervalRef.current)
    wsRef.current?.close()
    videoRef.current?.srcObject?.getTracks().forEach(t => t.stop())
    setActive(false)
    setResult(null)
    setVisImage(null)
  }

  useEffect(() => {
    start()
    return () => stop()
  }, [])

  return (
    <div>
      <div className="result-layout" style={{ display: active ? 'grid' : 'none' }}>
        <div className="video-container">
          <video ref={videoRef} className="video-feed" autoPlay muted playsInline />
          <canvas ref={canvasRef} style={{ display: 'none' }} />
          {visImage && (
            <img
              src={`data:image/jpeg;base64,${visImage}`}
              alt="분석 오버레이"
              className="vis-overlay"
            />
          )}
        </div>
        <div>
          {!connected && <div className="error-msg">서버 연결 중...</div>}
          {connected && !result && <div className="loading">카메라를 bowl에 향해주세요</div>}
          {result && !result.detected && <div className="loading">물체를 감지하지 못했습니다</div>}
          {result?.analyzed && <ResultPanel result={result} />}
        </div>
      </div>
      {result?.major_cm != null && <LimitationNote />}
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState('upload')

  return (
    <div className="container">
      <h1>원형 물체 분석기</h1>
      <p className="subtitle">쟁반 또는 냄비의 지름을 측정하고 찌그러짐을 판별합니다.</p>
      <div className="info-box">
        📷 정확한 측정을 위해 물체 바로 위에서 내려다보며 촬영해 주세요.
      </div>

      <div className="tabs">
        <button className={`tab ${tab === 'upload' ? 'active' : ''}`} onClick={() => setTab('upload')}>
          이미지 업로드
        </button>
        <button className={`tab ${tab === 'webcam' ? 'active' : ''}`} onClick={() => setTab('webcam')}>
          웹캠 촬영
        </button>
      </div>

      <div className="tab-content">
        {tab === 'upload' ? <UploadTab /> : <WebcamTab />}
      </div>
    </div>
  )
}
