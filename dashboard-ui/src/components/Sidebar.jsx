import { BarChart3, Video, ExternalLink, ScanEye } from 'lucide-react';

export default function Sidebar({ tab, onTab, legacyUrl }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <ScanEye size={24} strokeWidth={2} />
        </div>
        <div>
          <strong className="brand-name">Apex Lens</strong>
          <span className="brand-sub">by Apex Retail</span>
        </div>
      </div>

      <p className="sidebar-tagline">CCTV → events → decisions</p>

      <nav className="sidebar-nav">
        <button
          type="button"
          className={tab === 'analytics' ? 'active' : ''}
          onClick={() => onTab('analytics')}
        >
          <BarChart3 size={18} />
          Store pulse
        </button>
        <button
          type="button"
          className={tab === 'cctv' ? 'active' : ''}
          onClick={() => onTab('cctv')}
        >
          <Video size={18} />
          Floor vision
        </button>
      </nav>

      <div className="sidebar-foot">
        <a href={legacyUrl} target="_blank" rel="noreferrer" className="legacy-link">
          <ExternalLink size={14} />
          Open CV lab (face + staff boxes)
        </a>
        <p className="sidebar-note">Live detection overlay runs on port 8000</p>
      </div>
    </aside>
  );
}
