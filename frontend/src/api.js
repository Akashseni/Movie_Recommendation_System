// Backend base URL is injected at build/runtime via env var so the same
// image can point at different environments (dev / staging / prod) without
// a rebuild — set in docker-compose or the Jenkins deploy stage.
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const listMovies = () => request('/movies');

export const searchMovies = (q) =>
  request(`/movies/search?q=${encodeURIComponent(q)}`);

export const getRecommendations = (title, topN = 5) =>
  request(`/recommend?title=${encodeURIComponent(title)}&top_n=${topN}`);

export const getByGenre = (genre, topN = 5) =>
  request(`/recommend/genre?genre=${encodeURIComponent(genre)}&top_n=${topN}`);
