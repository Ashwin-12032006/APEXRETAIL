import { BarChart3, Video, ExternalLink, Sparkles } from 'lucide-react';

export default function Sidebar({ tab, onTab, legacyUrl }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Sparkles size={22} strokeWidth={2.2} />
        </div>
        <div>
          <strong>Purplle</strong>
          <span>Store Intelligence</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <button
          type="button"
          className={tab === 'analytics' ? 'active' : ''}
          onClick={() => onTab('analytics')}
        >
          <BarChart3 size={18} />
          Analytics
        </button>
        <button
          type="button"
          className={tab === 'cctv' ? 'active' : ''}
          onClick={() => onTab('cctv')}
        >
          <Video size={18} />
          Live CCTV
        </button>
      </nav>

      <div className="sidebar-foot">
        <a href={legacyUrl} target="_blank" rel="noreferrer" className="legacy-link">
          <ExternalLink size={14} />
          Advanced CV overlay
        </a>
        <p className="sidebar-note">Face detection & staff uniforms on port 8000</p>
      </div>
    </aside>
  );
}
