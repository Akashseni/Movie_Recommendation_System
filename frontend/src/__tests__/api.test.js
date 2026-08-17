import { describe, it, expect, vi, beforeEach } from 'vitest';
import { listMovies, getRecommendations } from '../api.js';

beforeEach(() => {
  global.fetch = vi.fn();
});

describe('api client', () => {
  it('listMovies calls /movies and returns json', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => [{ id: 1, title: 'The Matrix' }],
    });
    const result = await listMovies();
    expect(result).toEqual([{ id: 1, title: 'The Matrix' }]);
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/movies'));
  });

  it('getRecommendations throws on non-ok response', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Movie not found' }),
    });
    await expect(getRecommendations('Nope')).rejects.toThrow('Movie not found');
  });
});
