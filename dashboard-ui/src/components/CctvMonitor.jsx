import { useState } from 'react';
import { assetUrl } from '../api';
import { Maximize2, Circle } from 'lucide-react';

const CAMS = [
  { id: 'CAM1', label: 'Entry', sub: 'Threshold gate', file: '/assets/cctv/entry.mp4' },
  { id: 'CAM2', label: 'Main floor', sub: 'Skincare aisle', file: '/assets/cctv/main_floor.mp4' },
  { id: 'CAM3', label: 'Billing', sub: 'Queue & POS', file: '/assets/cctv/billing.mp4' },
  { id: 'CAM4', label: 'Haircare', sub: 'Aisle B', file: '/assets/cctv/cam4.mp4' },
  { id: 'CAM5', label: 'Billing 2', sub: 'Wide angle', file: '/assets/cctv/cam5.mp4' },
];

export default function CctvMonitor({ storeId, fullPage }) {
  const [active, setActive] = useState('CAM1');
  const main = CAMS.find((c) => c.id === active) || CAMS[0];

  return (
    <section className={`cctv-section glass ${fullPage ? 'cctv-full' : ''}`}>
      <div className="panel-head">
        <div>
          <h2>Live CCTV — 5 camera mesh</h2>
          <p className="hint">{storeId} · YOLOv8 pipeline · staff black-coat detection on legacy UI</p>
        </div>
        <span className="live-pill on">
          <span className="live-dot" />
          REC
        </span>
      </div>

      <div className="cctv-stage">
        <video
          key={main.file}
          className="cctv-main-video"
          src={assetUrl(main.file)}
          autoPlay
          muted
          loop
          playsInline
          controls
        />
        <div className="cctv-overlay">
          <div className="overlay-tag">
            <Maximize2 size={14} />
            {main.label} · {main.sub}
          </div>
          <div className="overlay-stats">
            <span><Circle size={8} fill="#34d399" color="#34d399" /> LIVE</span>
            <span>30 FPS · 1080p</span>
          </div>
        </div>
      </div>

      <div className="pip-grid">
        {CAMS.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`pip-card ${c.id === active ? 'active' : ''}`}
            onClick={() => setActive(c.id)}
          >
            <div className="pip-video-wrap">
              <video src={assetUrl(c.file)} muted loop playsInline preload="metadata" />
              {c.id === active && <span className="pip-live">LIVE</span>}
            </div>
            <div className="pip-meta">
              <strong>{c.id}</strong>
              <span>{c.label}</span>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
