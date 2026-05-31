const API_BASE = import.meta.env.VITE_API_URL || '';

export function apiUrl(path) {
  if (API_BASE) return `${API_BASE.replace(/\/$/, '')}${path}`;
  return `/api${path}`;
}

export function assetUrl(path) {
  if (API_BASE) return `${API_BASE.replace(/\/$/, '')}${path}`;
  return path;
}

/** Turn Google Drive share links into a direct-play URL for <video src>. */
export function resolveVideoUrl(src) {
  if (!src) return '';
  if (!/^https?:\/\//i.test(src)) return assetUrl(src);
  const fileId = src.match(/\/d\/([a-zA-Z0-9_-]+)/)?.[1]
    || src.match(/[?&]id=([a-zA-Z0-9_-]+)/)?.[1];
  if (fileId) return `https://drive.google.com/uc?export=view&id=${fileId}`;
  return src;
}

export async function fetchJson(path) {
  const res = await fetch(apiUrl(path));
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
}
