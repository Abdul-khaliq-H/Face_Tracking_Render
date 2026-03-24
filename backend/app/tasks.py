from celery import Celery
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import JobStatus, VideoJob
from app.processor import process_video


celery = Celery("creatortrack", broker=settings.redis_url, backend=settings.redis_url)


def update_job_progress(job_id: int, progress: int) -> None:
    with SessionLocal() as db:
        job = db.scalar(select(VideoJob).where(VideoJob.id == job_id))
        if not job:
            return
        job.progress = progress
        job.status = JobStatus.processing
        db.commit()


def run_video_job(job_id: int) -> None:
    with SessionLocal() as db:
        job = db.scalar(select(VideoJob).where(VideoJob.id == job_id))
        if not job:
            return
        job.status = JobStatus.processing
        job.progress = 5
        db.commit()

        try:
            process_video(
                job.input_path,
                job.output_path or "",
                lambda value: update_job_progress(job_id, value),
            )
            job = db.scalar(select(VideoJob).where(VideoJob.id == job_id))
            if job:
                job.status = JobStatus.completed
                job.progress = 100
                db.commit()
        except Exception as exc:
            job = db.scalar(select(VideoJob).where(VideoJob.id == job_id))
            if job:
                job.status = JobStatus.failed
                job.error_message = str(exc)
                db.commit()
            raise


@celery.task(name="process-video-job")
def process_video_job(job_id: int) -> None:
    run_video_job(job_id)
