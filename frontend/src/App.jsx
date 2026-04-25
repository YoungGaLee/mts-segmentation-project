import { useState, useRef, useCallback, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_BASE = API_BASE.replace(/^http/, 'ws')

const STATUS_COLOR = {
  '온전한 원형': '#22c55e',
  '약간 찌그러짐': '#f97316',
  '찌그러진 상태': '#ef4444',
}

function ResultPanel({ result }) {
  return (
    <div className="result-panel">
      <h3>분석 결과</h3>

      {result.view_type === '측면' && (
        <div className="warning">⚠️ 측면 촬영입니다. 위에서 촬영하면 더 정확합니다.</div>
      )}

      <div className="metrics">
        <div className="metric">
          <span className="label">촬영 방향</span>
          <span className="value">{result.view_type}</span>
        </div>
        <div className="metric">
          <span className="label">장축</span>
          <span className="value">{result.major_px?.toFixed(1)} px</span>
        </div>
        <div className="metric">
          <span className="label">단축</span>
          <span className="value">{result.minor_px?.toFixed(1)} px</span>
        </div>
        <div className="metric">
          <span className="label">{result.view_type === '정면' ? '단축/장축 비율' : 'Solidity'}</span>
          <span className="value">
            {result.view_type === '정면' ? result.ratio : result.solidity}
          </span>
        </div>
      </div>

      <div className="status-badge" style={{ backgroundColor: STATUS_COLOR[result.status] }}>
        {result.status}
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
          <div className="result-layout">
            <img src={`data:image/jpeg;base64,${result.image}`} alt="분석 결과" className="result-img" />
            <ResultPanel result={result} />
          </div>
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
        const b64 = canvas.toDataURL('image/jpeg', 0.7).split(',')[1]
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

  useEffect(() => () => stop(), [])

  return (
    <div>
      <div className="webcam-controls">
        {!active
          ? <button className="btn-primary" onClick={start}>시작</button>
          : <button className="btn-danger" onClick={stop}>중지</button>
        }
      </div>

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
