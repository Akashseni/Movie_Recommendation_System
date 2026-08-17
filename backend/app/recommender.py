"""
Content-based movie recommender.

Builds a TF-IDF matrix over each movie's combined "genres + overview" text
and recommends movies by cosine similarity. Kept dependency-light (scikit-learn
+ pandas) so the whole thing is fast to install and test in a CI pipeline.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "movies.csv")


@dataclass
class Movie:
    id: int
    title: str
    genres: str
    overview: str
    year: int
    rating: float


class MovieRecommender:
    """Loads the catalog once and serves similarity-based recommendations."""

    def __init__(self, data_path: str = DATA_PATH):
        self.data_path = data_path
        self.df = pd.read_csv(data_path)
        self._validate_schema()
        self.df["soup"] = (
            self.df["genres"].fillna("") + " " + self.df["overview"].fillna("")
        )
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.df["soup"])
        self.similarity = cosine_similarity(self.matrix)
        self._title_index = {
            t.lower(): i for i, t in enumerate(self.df["title"])
        }

    def _validate_schema(self) -> None:
        required = {"id", "title", "genres", "overview", "year", "rating"}
        missing = required - set(self.df.columns)
        if missing:
            raise ValueError(f"movies.csv missing required columns: {missing}")
        if self.df.empty:
            raise ValueError("movies.csv contains no rows")

    def list_movies(self) -> List[dict]:
        return self.df[["id", "title", "genres", "year", "rating"]].to_dict(
            orient="records"
        )

    def get_movie(self, title: str) -> dict | None:
        idx = self._title_index.get(title.lower())
        if idx is None:
            return None
        return self.df.iloc[idx].to_dict()

    def search(self, query: str) -> List[dict]:
        query = query.lower().strip()
        if not query:
            return []
        matches = self.df[self.df["title"].str.lower().str.contains(query)]
        return matches[["id", "title", "genres", "year", "rating"]].to_dict(
            orient="records"
        )

    def recommend(self, title: str, top_n: int = 5) -> List[dict]:
        idx = self._title_index.get(title.lower())
        if idx is None:
            raise KeyError(f"Movie '{title}' not found in catalog")

        scores = list(enumerate(self.similarity[idx]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        # skip index 0 -> that's the movie itself
        top = [s for s in scores if s[0] != idx][:top_n]

        results = []
        for i, score in top:
            row = self.df.iloc[i]
            results.append(
                {
                    "id": int(row["id"]),
                    "title": row["title"],
                    "genres": row["genres"],
                    "year": int(row["year"]),
                    "rating": float(row["rating"]),
                    "similarity": round(float(score), 4),
                }
            )
        return results

    def recommend_by_genre(self, genre: str, top_n: int = 5) -> List[dict]:
        genre = genre.lower().strip()
        matches = self.df[self.df["genres"].str.lower().str.contains(genre)]
        matches = matches.sort_values("rating", ascending=False).head(top_n)
        return matches[["id", "title", "genres", "year", "rating"]].to_dict(
            orient="records"
        )


@lru_cache(maxsize=1)
def get_recommender() -> MovieRecommender:
    """Cached singleton so the TF-IDF matrix is built once per process."""
    return MovieRecommender()
