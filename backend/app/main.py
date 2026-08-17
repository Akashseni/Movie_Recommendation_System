from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.recommender import get_recommender

app = FastAPI(
    title="Movie Recommendation API",
    description="Content-based movie recommendation service",
    version="1.0.0",
)

# In production, restrict this to the actual frontend origin via env var.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class MovieOut(BaseModel):
    id: int
    title: str
    genres: str
    year: int
    rating: float


class RecommendationOut(MovieOut):
    similarity: float


@app.get("/health")
def health() -> dict:
    """Used by Docker healthchecks and the Jenkins post-deploy smoke test."""
    return {"status": "ok"}


@app.get("/movies", response_model=list[MovieOut])
def list_movies():
    return get_recommender().list_movies()


@app.get("/movies/search", response_model=list[MovieOut])
def search_movies(q: str = Query(..., min_length=1)):
    return get_recommender().search(q)


@app.get("/recommend", response_model=list[RecommendationOut])
def recommend(
    title: str = Query(..., description="Exact movie title to base recommendations on"),
    top_n: int = Query(5, ge=1, le=20),
):
    try:
        return get_recommender().recommend(title, top_n=top_n)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/recommend/genre", response_model=list[MovieOut])
def recommend_by_genre(
    genre: str = Query(..., min_length=1),
    top_n: int = Query(5, ge=1, le=20),
):
    return get_recommender().recommend_by_genre(genre, top_n=top_n)
