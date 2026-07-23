/**
 * Recent search history for the Advanced Search bar — stored in the
 * browser's localStorage only (per-browser/device, no backend involved).
 */

const STORAGE_KEY = "documind:recent-searches";
const MAX_ITEMS = 8;

export const getSearchHistory = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export const addSearchHistory = (query) => {
  const trimmed = query.trim();
  if (!trimmed) return getSearchHistory();

  const existing = getSearchHistory().filter(
    (item) => item.toLowerCase() !== trimmed.toLowerCase()
  );
  const updated = [trimmed, ...existing].slice(0, MAX_ITEMS);

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // localStorage unavailable (private mode, quota, etc.) — fail silently
  }
  return updated;
};

export const removeSearchHistory = (query) => {
  const updated = getSearchHistory().filter((item) => item !== query);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // ignore
  }
  return updated;
};

export const clearSearchHistory = () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
  return [];
};