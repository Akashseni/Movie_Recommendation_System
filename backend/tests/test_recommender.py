import pytest

from app.recommender import MovieRecommender, DATA_PATH


@pytest.fixture(scope="module")
def recommender():
    return MovieRecommender(DATA_PATH)


def test_loads_catalog(recommender):
    assert len(recommender.df) > 0


def test_list_movies_shape(recommender):
    movies = recommender.list_movies()
    assert isinstance(movies, list)
    assert set(movies[0].keys()) == {"id", "title", "genres", "year", "rating"}


def test_recommend_returns_top_n(recommender):
    results = recommender.recommend("The Matrix", top_n=5)
    assert len(results) == 5
    titles = [r["title"] for r in results]
    assert "The Matrix" not in titles  # never recommends itself


def test_recommend_similar_scifi(recommender):
    results = recommender.recommend("Inception", top_n=10)
    titles = {r["title"] for r in results}
    # Interstellar shares Sci-Fi / similar themes and should rank highly
    assert "Interstellar" in titles or "The Prestige" in titles


def test_recommend_unknown_movie_raises(recommender):
    with pytest.raises(KeyError):
        recommender.recommend("Not A Real Movie Title")


def test_search_case_insensitive(recommender):
    results = recommender.search("matrix")
    assert any(r["title"] == "The Matrix" for r in results)


def test_recommend_by_genre(recommender):
    results = recommender.recommend_by_genre("Animation", top_n=3)
    assert len(results) <= 3
    assert all("Animation" in r["genres"] for r in results)
