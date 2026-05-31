import { BarChart3, Video, ExternalLink, ScanEye } from 'lucide-react';

export default function Sidebar({ tab, onTab, legacyUrl }) {
  return (
    <aside className="sidebar sidebar-desktop">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <ScanEye size={24} strokeWidth={2} />
        </div>
        <div className="sidebar-brand-text">
          <strong className="brand-name">Apex Lens</strong>
          <span className="brand-sub">by Apex Retail</span>
        </div>
      </div>

      <p className="sidebar-tagline">CCTV → events → decisions</p>

      <nav className="sidebar-nav" aria-label="Dashboard sections">
        <button
          type="button"
          className={tab === 'analytics' ? 'active' : ''}
          onClick={() => onTab('analytics')}
          aria-label="Store pulse"
          aria-current={tab === 'analytics' ? 'page' : undefined}
        >
          <BarChart3 size={18} />
          <span className="nav-label">Store pulse</span>
        </button>
        <button
          type="button"
          className={tab === 'cctv' ? 'active' : ''}
          onClick={() => onTab('cctv')}
          aria-label="Floor vision"
          aria-current={tab === 'cctv' ? 'page' : undefined}
        >
          <Video size={18} />
          <span className="nav-label">Floor vision</span>
        </button>
      </nav>

      <div className="sidebar-foot">
        <a href={legacyUrl} target="_blank" rel="noreferrer" className="legacy-link" aria-label="Open CV lab">
          <ExternalLink size={14} />
          <span className="legacy-link-text">CV lab</span>
        </a>
        <p className="sidebar-note">Live detection overlay runs on port 8000</p>
      </div>
    </aside>
  );
}
