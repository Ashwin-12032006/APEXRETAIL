import { useEffect, useState } from 'react';
import {
  assetUrl,
  driveEmbedUrl,
  fetchJson,
  isDirectVideoUrl,
  isGoogleDriveSource,
  resolveVideoUrl,
} from '../api';
import { Maximize2, Circle } from 'lucide-react';

const CAM_META = [
  { id: 'CAM1', label: 'Entry', sub: 'Threshold gate', fallback: '/assets/cctv/entry.mp4' },
  { id: 'CAM2', label: 'Main floor', sub: 'Skincare aisle', fallback: '/assets/cctv/main_floor.mp4' },
  { id: 'CAM3', label: 'Billing', sub: 'Queue & POS', fallback: '/assets/cctv/billing.mp4' },
  { id: 'CAM4', label: 'Haircare', sub: 'Aisle B', fallback: '/assets/cctv/cam4.mp4' },
  { id: 'CAM5', label: 'Billing 2', sub: 'Wide angle', fallback: '/assets/cctv/cam5.mp4' },
];

function firstSource(raw, fallback) {
  if (Array.isArray(raw)) return raw[0] || fallback;
  if (typeof raw === 'string' && raw.trim()) return raw.trim();
  return fallback;
}

function resolveCamSource(external, fallback) {
  const raw = firstSource(external, fallback);
  if (isDirectVideoUrl(raw)) {
    const videoSrc = /^https?:\/\//i.test(raw) ? raw : assetUrl(raw);
    return { raw, driveEmbed: null, videoSrc, crossOrigin: true };
  }
  const driveEmbed = driveEmbedUrl(raw);
  return {
    raw,
    driveEmbed,
    videoSrc: driveEmbed ? null : resolveVideoUrl(raw),
    crossOrigin: false,
  };
}

function CctvFeed({ source, className, pip }) {
  if (source.driveEmbed) {
    return (
      <iframe
        title="CCTV feed"
        src={source.driveEmbed}
        className={className}
        allow="autoplay; fullscreen; encrypted-media"
        loading={pip ? 'lazy' : 'eager'}
        style={pip ? { pointerEvents: 'none' } : undefined}
      />
    );
  }
  return (
    <video
      className={className}
      src={source.videoSrc}
      crossOrigin={source.crossOrigin ? 'anonymous' : undefined}
      autoPlay
      muted
      loop
      playsInline
      controls={false}
      preload="auto"
    />
  );
}

export default function CctvMonitor({ storeId, fullPage }) {
  const [active, setActive] = useState('CAM1');
  const [sources, setSources] = useState({});

  useEffect(() => {
    fetchJson('/cctv/feeds.json')
      .then((feeds) => {
        const mapped = {};
        CAM_META.forEach((c) => {
          const fromStore = feeds?.stores?.[storeId]?.[c.id]?.sources;
          const fromDefault = feeds?.default?.[c.id]?.sources;
          mapped[c.id] = fromStore || fromDefault || [];
        });
        setSources(mapped);
      })
      .catch(() => {
        fetch('/cctv-sources.json')
          .then((r) => (r.ok ? r.json() : {}))
          .then((data) => setSources(data))
          .catch(() => setSources({}));
      });
  }, [storeId]);

  const cams = CAM_META.map((c) => ({
    ...c,
    source: resolveCamSource(sources[c.id], c.fallback),
  }));
  const main = cams.find((c) => c.id === active) || cams[0];
  const usingDrive = isGoogleDriveSource(firstSource(sources[main.id], main.fallback));

  return (
    <section className={`cctv-section glass ${fullPage ? 'cctv-full' : ''}`}>
      <div className="panel-head">
        <div>
          <h2>Live CCTV — 5 camera mesh</h2>
          <p className="hint">
            {storeId} · {usingDrive ? 'Google Drive stream' : 'Direct MP4 · CV-ready'} · legacy UI for face + staff
          </p>
        </div>
        <span className="live-pill on">
          <span className="live-dot" />
          REC
        </span>
      </div>

      <div className={`cctv-stage ${main.source.driveEmbed ? 'cctv-stage-embed' : ''}`}>
        <CctvFeed source={main.source} className="cctv-main-video" />
        <div className="cctv-overlay">
          <div className="overlay-tag">
            <Maximize2 size={14} />
            {main.label} · {main.sub}
          </div>
          <div className="overlay-stats">
            <span><Circle size={8} fill="#34d399" color="#34d399" /> LIVE</span>
            <span>{usingDrive ? 'Drive embed' : 'MP4 · face detect'}</span>
          </div>
        </div>
      </div>

      <div className="pip-grid">
        {cams.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`pip-card ${c.id === active ? 'active' : ''}`}
            onClick={() => setActive(c.id)}
          >
            <div className="pip-video-wrap">
              <CctvFeed source={c.source} className="pip-video" pip />
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
