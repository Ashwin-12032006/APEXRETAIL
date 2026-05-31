import { useState } from 'react';
import { assetUrl } from '../api';

const CAMS = [
  { id: 'CAM1', label: 'CAM 1 · Entry', file: '/assets/cctv/entry.mp4', apiCam: 'CAM_ENTRY_02' },
  { id: 'CAM2', label: 'CAM 2 · Floor', file: '/assets/cctv/main_floor.mp4', apiCam: 'CAM_MAIN_02' },
  { id: 'CAM3', label: 'CAM 3 · Billing', file: '/assets/cctv/billing.mp4', apiCam: 'CAM_BILL_02' },
  { id: 'CAM4', label: 'CAM 4 · Haircare', file: '/assets/cctv/cam4.mp4', apiCam: 'CAM_MAIN_02' },
  { id: 'CAM5', label: 'CAM 5 · Billing 2', file: '/assets/cctv/cam5.mp4', apiCam: 'CAM_BILL_02' },
];

export default function CctvMonitor({ storeId }) {
  const [active, setActive] = useState('CAM1');
  const main = CAMS.find((c) => c.id === active) || CAMS[0];

  return (
    <section className="glass panel cctv-panel">
      <h2>Live CCTV — 5 cameras</h2>
      <p className="hint">{storeId} · YOLO pipeline + browser overlay (legacy UI at :8000)</p>
      <div className="cctv-main">
        <video
          key={main.file}
          src={assetUrl(main.file)}
          autoPlay
          muted
          loop
          playsInline
          controls
        />
      </div>
      <div className="pip-row">
        {CAMS.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`pip ${c.id === active ? 'active' : ''}`}
            onClick={() => setActive(c.id)}
          >
            <video src={assetUrl(c.file)} muted loop playsInline preload="metadata" />
            <span>{c.label}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
