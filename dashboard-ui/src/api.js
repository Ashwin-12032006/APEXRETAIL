const API_BASE = import.meta.env.VITE_API_URL || '';

export function apiUrl(path) {
  if (API_BASE) return `${API_BASE.replace(/\/$/, '')}${path}`;
  return `/api${path}`;
}

export function assetUrl(path) {
  if (API_BASE) return `${API_BASE.replace(/\/$/, '')}${path}`;
  return path;
}

export async function fetchJson(path) {
  const res = await fetch(apiUrl(path));
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
}
