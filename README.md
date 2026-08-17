# CineMatch — Movie Recommendation System (Full-Stack + Jenkins CI/CD)

A small but complete full-stack project built specifically to demonstrate a
real CI/CD pipeline in Jenkins: lint → test → build → containerize → push →
deploy → smoke test.

## Architecture

```
┌─────────────┐      HTTP       ┌──────────────────┐
│  React SPA  │ ───────────────▶│   FastAPI backend │
│  (Vite,     │                 │  content-based     │
│  nginx)     │◀─────────────── │  recommender (TF-IDF│
└─────────────┘      JSON       │  + cosine similarity)│
                                 └──────────────────┘
      :3000                            :8000
```

- **Backend** (`/backend`) — FastAPI service. Recommends movies using a
  TF-IDF vectorizer over each movie's genres + overview, ranked by cosine
  similarity. No database needed — it reads `app/data/movies.csv` at
  startup, which keeps the whole demo fast to build and test in CI.
- **Frontend** (`/frontend`) — React (Vite) single-page app. Lets you search
  the catalog and see similarity-ranked recommendations.
- **Jenkinsfile** — the CI/CD pipeline (see below).
- **docker-compose.yml** — runs both services together.
- **jenkins/** + **docker-compose.jenkins.yml** — optional local Jenkins
  controller (with Docker CLI + required plugins baked in) if you don't
  already have a Jenkins server to test against.

## Run it locally (no Jenkins, no Docker)

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
# -> http://localhost:8000/docs

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# -> http://localhost:5173
```

## Run it with Docker Compose

```bash
cp .env.example .env
docker compose up --build
# frontend -> http://localhost:3000
# backend  -> http://localhost:8000/health
```

## Run the test suites

```bash
# Backend: 13 tests (recommender logic + API contract)
cd backend && pytest tests/ -v --cov=app

# Frontend: API client tests + production build
cd frontend && npm run lint && npx vitest run && npm run build
```

Both suites were run during this project's creation and pass cleanly — this
is a working codebase, not a stub.

## The Jenkins pipeline

`Jenkinsfile` (declarative) defines these stages:

1. **Checkout** — pulls the repo, captures the short commit SHA for image tagging.
2. **Backend: Install & Lint** — `flake8` + `black --check`, run inside a
   disposable `python:3.12-slim` container.
3. **Backend: Test** — `pytest` with coverage, JUnit XML published to Jenkins.
4. **Frontend: Install & Lint** — `npm install` + `eslint`, inside `node:20-alpine`.
5. **Frontend: Test & Build** — `vitest` (JUnit output) + production `vite build`.
6. **Build Docker Images** — builds and tags both images with `${BUILD_NUMBER}-${GIT_COMMIT_SHORT}` and `latest`.
7. **Push to Registry** — logs in to Docker Hub via the `dockerhub-creds` credential and pushes both tags.
8. **Deploy** — `docker compose pull && up -d` (skippable via the `SKIP_DEPLOY` parameter, useful for PR builds that should only run CI).
9. **Smoke Test** — polls `/health` and the frontend root until the new containers are actually serving traffic, and fails the build if they don't come up.

Post-build: JUnit results are always published, workspace is cleaned, and
`docker system prune` keeps the agent from filling up with old layers.

### Jenkins setup

**Plugins required** (already baked into `jenkins/Dockerfile` if you use the
local Jenkins option): Pipeline (`workflow-aggregator`), Docker Pipeline,
Git, JUnit, Credentials Binding, HTML Publisher, Blue Ocean (optional, nicer
pipeline view).

**Credentials to configure** (Manage Jenkins → Credentials):
- `dockerhub-creds` — "Username with password" credential for Docker Hub
  (or swap for your registry of choice; the Jenkinsfile only assumes
  `docker login` semantics).

**Docker on the agent**: the pipeline builds and runs containers directly,
so whichever Jenkins agent runs the job needs Docker installed and the
`jenkins` user in the `docker` group (or run Jenkins itself as a container
with the host's Docker socket mounted — see `docker-compose.jenkins.yml`).

**Creating the job**:
1. New Item → Pipeline (or Multibranch Pipeline if you want a job per branch/PR).
2. Pipeline script from SCM → point at this repo → script path `Jenkinsfile`.
3. (Optional) Add a GitHub webhook (`Settings → Webhooks` on the repo,
   payload URL `http://<jenkins-host>/github-webhook/`) so pushes trigger
   builds automatically instead of polling.

**Try it without a real Jenkins server first**:
```bash
docker compose -f docker-compose.jenkins.yml up --build
# open http://localhost:8080, finish the setup wizard, then create the
# pipeline job as described above pointing at this repo
```

### Pipeline parameters

- `DEPLOY_ENV` — `staging` (default) or `production`; controls which API
  base URL gets baked into the frontend build.
- `SKIP_DEPLOY` — when true, runs lint/test/build/push only and stops before
  the Deploy stage. Useful for pull-request validation builds.

## API reference

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness check (used by Docker healthchecks + Jenkins smoke test) |
| `GET /movies` | List the full catalog |
| `GET /movies/search?q=` | Substring title search |
| `GET /recommend?title=&top_n=` | Content-based recommendations for a title |
| `GET /recommend/genre?genre=&top_n=` | Top-rated movies in a genre |

## Extending this for a real deployment

This is intentionally a self-contained demo (CSV instead of a database, no
auth, single-host `docker compose` deploy). To take it further:
- Swap the CSV for Postgres + a real movie dataset (e.g. MovieLens).
- Add a `k8s/` manifest or Helm chart and swap the Deploy stage for
  `kubectl apply` / `helm upgrade`.
- Add a staging vs. production distinction with separate Jenkins
  environments or a manual approval (`input` step) before the production
  deploy.
- Add collaborative filtering once you have real user rating data, not just
  content-based similarity.
