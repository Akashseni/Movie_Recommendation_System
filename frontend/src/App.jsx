import React, { useState, useEffect } from 'react';
import { listMovies, getRecommendations } from './api.js';

export default function App() {
  const [movies, setMovies] = useState([]);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);
  const [recs, setRecs] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listMovies()
      .then(setMovies)
      .catch((e) => setError(e.message));
  }, []);

  const filtered = query
    ? movies.filter((m) => m.title.toLowerCase().includes(query.toLowerCase()))
    : movies;

  const handleSelect = async (movie) => {
    setSelected(movie);
    setError('');
    setLoading(true);
    try {
      const results = await getRecommendations(movie.title, 6);
      setRecs(results);
    } catch (e) {
      setError(e.message);
      setRecs([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>🎬 CineMatch</h1>
        <p>Content-based movie recommendations</p>
      </header>

      <input
        className="search"
        placeholder="Search movies..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {error && <div className="error">{error}</div>}

      <div className="layout">
        <section className="catalog">
          <h2>Catalog ({filtered.length})</h2>
          <ul>
            {filtered.map((m) => (
              <li
                key={m.id}
                className={selected?.id === m.id ? 'active' : ''}
                onClick={() => handleSelect(m)}
              >
                <strong>{m.title}</strong> <span>({m.year})</span>
                <div className="genres">{m.genres}</div>
              </li>
            ))}
          </ul>
        </section>

        <section className="recs">
          <h2>
            {selected ? `Because you picked "${selected.title}"` : 'Pick a movie to get recommendations'}
          </h2>
          {loading && <p>Loading recommendations...</p>}
          <ul>
            {recs.map((r) => (
              <li key={r.id}>
                <strong>{r.title}</strong> <span>({r.year})</span>
                <div className="genres">{r.genres}</div>
                <div className="score">match: {(r.similarity * 100).toFixed(0)}%</div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
