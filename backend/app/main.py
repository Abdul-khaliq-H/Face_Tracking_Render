from pathlib import Path
import time

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.exc import OperationalError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import JobStatus, User, VideoJob
from app.schemas import AuthResponse, JobResponse, LoginRequest, RegisterRequest
from app.security import (
    create_access_token,
    get_current_user,
    get_db,
    hash_password,
    verify_password,
)
from app.storage import ensure_storage_dirs, make_output_path, make_upload_path
from app.tasks import process_video_job, run_video_job

app = FastAPI(title=settings.app_name)

allowed_origins = ["*"] if settings.cors_allow_all else [settings.frontend_origin, "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    ensure_storage_dirs()

    for attempt in range(1, settings.startup_db_retries + 1):
        try:
            with SessionLocal() as db:
                db.execute(select(1))
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError:
            if attempt == settings.startup_db_retries:
                raise
            time.sleep(settings.startup_db_retry_delay_seconds)


def serialize_job(job: VideoJob) -> JobResponse:
    input_url = f"{settings.api_base_url}/jobs/{job.id}/preview?kind=input"

    output_url = None
    download_url = None
    if job.output_path and Path(job.output_path).exists():
        output_url = f"{settings.api_base_url}/jobs/{job.id}/preview?kind=output"
        download_url = f"{settings.api_base_url}/jobs/{job.id}/download"

    return JobResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        input_url=input_url,
        output_url=output_url,
        download_url=download_url,
        created_at=job.created_at,
    )


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthResponse(
        access_token=create_access_token(user.id),
        email=user.email,
    )


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return AuthResponse(
        access_token=create_access_token(user.id),
        email=user.email,
    )


@app.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "id": current_user.id}


@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    upload_path = make_upload_path(file.filename)
    output_path = make_output_path(file.filename)

    with upload_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    job = VideoJob(
        user_id=current_user.id,
        original_filename=file.filename,
        input_path=str(upload_path),
        output_path=str(output_path),
        status=JobStatus.queued,
        progress=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if settings.job_runner_mode == "inline":
        background_tasks.add_task(run_video_job, job.id)
    else:
        process_video_job.delay(job.id)
    return serialize_job(job)


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    jobs = db.scalars(
        select(VideoJob).where(VideoJob.user_id == current_user.id).order_by(VideoJob.id.desc())
    ).all()
    return [serialize_job(job) for job in jobs]


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.scalar(
        select(VideoJob).where(VideoJob.id == job_id, VideoJob.user_id == current_user.id)
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_job(job)


@app.get("/jobs/{job_id}/download")
def download_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.scalar(
        select(VideoJob).where(VideoJob.id == job_id, VideoJob.user_id == current_user.id)
    )
    if not job or not job.output_path:
        raise HTTPException(status_code=404, detail="Output file not found")

    path = Path(job.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(path, media_type="video/mp4", filename=f"tracked-{job.original_filename}")


@app.get("/jobs/{job_id}/preview")
def preview_job_media(
    job_id: int,
    kind: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if kind not in {"input", "output"}:
        raise HTTPException(status_code=400, detail="Invalid preview kind")

    job = db.scalar(
        select(VideoJob).where(VideoJob.id == job_id, VideoJob.user_id == current_user.id)
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    path = Path(job.input_path if kind == "input" else job.output_path or "")
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
