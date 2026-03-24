# CreatorTrack

CreatorTrack is a micro SaaS for social media creators who want to upload a video and get back a face-tracked output.

## Stack

- Frontend: Next.js 15 + TypeScript
- Backend API: FastAPI
- Worker: Celery + Redis
- Database: PostgreSQL
- Storage: local disk by default, ready to swap to S3 later

## Features

- Landing page with value proposition and samples
- Email/password authentication
- Upload and process page with live progress polling
- Video preview and download once processing finishes
- Job queue architecture for multiple simultaneous customers

## Local development

1. Copy `.env.example` to `.env`
2. Start the stack:

```bash
docker compose up --build
```

3. Open:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

## Fast local test mode

The default `.env` uses `PROCESSOR_MODE=mock` so the app can be tested on a laptop without downloading the heavy computer-vision stack first.

In mock mode:

- uploads work
- job progress updates work
- preview works
- download works
- the output is a copied test file instead of real face tracking

When you want the full processor later, switch `PROCESSOR_MODE=real` and install the extra runtime dependencies for OpenCV, MediaPipe, SciPy, NumPy, and ffmpeg.

## Deployment notes

- Run the frontend, backend, worker, Postgres, and Redis as separate services in production
- Set `FRONTEND_ORIGIN` and `NEXT_PUBLIC_API_BASE_URL` to your real domain values
- Replace local file storage with S3-compatible storage when you want durable cloud media storage
- Scale the worker horizontally to process more videos in parallel

## Render demo deploy

This repo now includes a free-tier-friendly Render demo setup in [render.yaml](/Users/abdul-23344/Projects/Codex_face_track/render.yaml).

Demo deployment shape:

- free Render web service for the frontend
- free Render web service for the FastAPI backend
- free Render Postgres database
- no separate worker for the demo
- mock processor mode enabled
- inline background job execution enabled

Why this shape:

- Render free plans do not support free background workers in the same way as web services
- the demo avoids Redis and Celery so it can run on the free tier
- uploads, job progress, preview, and download still work for demos

Deploy steps:

1. Push this repo to GitHub
2. In Render, create a new Blueprint deployment from the repo
3. Render will read `render.yaml` and create the frontend, API, and Postgres services
4. Open the frontend Render URL and test the demo flow

Important demo limitations:

- free Render web services spin down when idle
- free Postgres is not for production
- uploaded files are stored on ephemeral disk and can disappear after redeploys or restarts
- `PROCESSOR_MODE=mock` means the output is for demo/testing, not real face tracking

## Plugging in your real face-tracking code

The real face-tracking implementation is already wired into `backend/app/processor.py`.

The processor supports two modes:

- `mock`: lightweight local testing
- `real`: your actual face-tracking pipeline
