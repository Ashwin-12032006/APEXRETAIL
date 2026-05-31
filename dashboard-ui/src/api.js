const API_BASE = import.meta.env.VITE_API_URL || '';

export function apiUrl(path) {
  if (API_BASE) return `${API_BASE.replace(/\/$/, '')}${path}`;
  return `/api${path}`;
}

export function assetUrl(path) {
  if (API_BASE) return `${API_BASE.replace(/\/$/, '')}${path}`;
  return path;
}

/** Extract Google Drive file id from a share or direct URL. */
export function googleDriveFileId(src) {
  if (!src || typeof src !== 'string') return null;
  return src.match(/\/d\/([a-zA-Z0-9_-]+)/)?.[1]
    || src.match(/[?&]id=([a-zA-Z0-9_-]+)/)?.[1]
    || null;
}

export function isGoogleDriveSource(src) {
  return !!googleDriveFileId(src);
}

/** iframe embed — reliable for public Drive MP4s (video tag often fails). */
export function driveEmbedUrl(src, autoplay = true) {
  const id = googleDriveFileId(src);
  if (!id) return null;
  return `https://drive.google.com/file/d/${id}/preview${autoplay ? '?autoplay=1' : ''}`;
}

/** Local/API path or direct mp4 URL for HTML5 video. */
export function resolveVideoUrl(src) {
  if (!src) return '';
  if (isGoogleDriveSource(src)) return driveEmbedUrl(src);
  if (!/^https?:\/\//i.test(src)) return assetUrl(src);
  return src;
}

export async function fetchJson(path) {
  const res = await fetch(apiUrl(path));
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
}
