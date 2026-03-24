"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { API_BASE_URL, apiRequest, Job } from "../lib/api";

const POLL_INTERVAL_MS = 2500;

type PreviewState = Record<number, { source: string; objectUrl: string }>;

function getToken() {
  if (typeof window === "undefined") {
    return "";
  }
  return localStorage.getItem("creatortrack_token") ?? "";
}

export function TryNowClient() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [previewState, setPreviewState] = useState<PreviewState>({});
  const [status, setStatus] = useState("Sign in first, then upload a video to start processing.");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const previewStateRef = useRef<PreviewState>({});

  async function fetchJobs() {
    const token = getToken();
    if (!token) {
      return;
    }

    try {
      const response = await apiRequest<Job[]>("/jobs", {}, token);
      setJobs(response);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Could not load jobs");
    }
  }

  useEffect(() => {
    fetchJobs();
    const interval = window.setInterval(fetchJobs, POLL_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      return;
    }

    const abortController = new AbortController();

    async function loadPreviews() {
      const nextEntries = await Promise.all(
        jobs.map(async (job) => {
          const targetUrl = job.output_url ?? job.input_url;
          if (!targetUrl) {
            return null;
          }

          const existing = previewStateRef.current[job.id];
          if (existing && existing.source === targetUrl) {
            return [job.id, existing] as const;
          }

          try {
            const response = await fetch(targetUrl, {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              signal: abortController.signal,
            });

            if (!response.ok) {
              return null;
            }

            const blob = await response.blob();
            return [
              job.id,
              {
                source: targetUrl,
                objectUrl: URL.createObjectURL(blob),
              },
            ] as const;
          } catch {
            return null;
          }
        })
      );

      setPreviewState((previous) => {
        const nextState = Object.fromEntries(
          nextEntries.filter(Boolean) as Array<readonly [number, { source: string; objectUrl: string }]>
        );

        Object.entries(previous).forEach(([jobId, value]) => {
          if (!nextState[Number(jobId)] || nextState[Number(jobId)].objectUrl !== value.objectUrl) {
            URL.revokeObjectURL(value.objectUrl);
          }
        });

        previewStateRef.current = nextState;
        return nextState;
      });
    }

    if (jobs.length > 0) {
      loadPreviews();
    }

    return () => {
      abortController.abort();
    };
  }, [jobs]);

  useEffect(() => {
    return () => {
      Object.values(previewStateRef.current).forEach((value) => {
        URL.revokeObjectURL(value.objectUrl);
      });
    };
  }, []);

  async function handleDownload(job: Job) {
    const token = getToken();
    if (!token || !job.download_url) {
      setError("Please sign in before downloading processed videos.");
      return;
    }

    try {
      const response = await fetch(job.download_url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Download failed");
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = `tracked-job-${job.id}.mp4`;
      anchor.click();
      URL.revokeObjectURL(objectUrl);
    } catch (downloadError) {
      setError(downloadError instanceof Error ? downloadError.message : "Download failed");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setStatus("");

    const token = getToken();
    if (!token) {
      setError("Please sign in on the sign-in page before uploading.");
      return;
    }

    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      setError("Choose a video file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    try {
      const job = await apiRequest<Job>(
        "/jobs",
        {
          method: "POST",
          body: formData,
        },
        token
      );

      setJobs((previous) => [job, ...previous]);
      setStatus("Upload received. Processing has started in the background.");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="try-layout shell">
      <div className="card upload-card">
        <div className="pill">Creator workflow</div>
        <h1 className="section-title">Upload and track your face automatically</h1>
        <p className="section-copy">
          Drop in a creator video, monitor the processing progress, preview the result, and download the final
          face-tracked output once the worker completes the job.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="video">Video file</label>
            <input id="video" ref={fileInputRef} type="file" accept="video/*" required />
          </div>
          <div className="form-row" style={{ marginTop: 18 }}>
            <button className="primary-button" type="submit" disabled={uploading}>
              {uploading ? "Uploading..." : "Start processing"}
            </button>
            <a className="secondary-button" href="/sign-in">
              Go to sign in
            </a>
          </div>
        </form>

        {status ? <p className="status-text success">{status}</p> : null}
        {error ? <p className="status-text error">{error}</p> : null}
      </div>

      <div className="jobs-grid">
        {jobs.map((job) => (
          <article className="card job-card" key={job.id}>
            <div className="pill">Job #{job.id}</div>
            <strong>Status: {job.status}</strong>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${job.progress}%` }} />
            </div>
            <span className="status-text">{job.progress}% complete</span>

            {job.output_url ? (
              <video className="video-frame" controls src={previewState[job.id]?.objectUrl}>
                <track kind="captions" />
              </video>
            ) : (
              <video className="video-frame" controls src={previewState[job.id]?.objectUrl}>
                <track kind="captions" />
              </video>
            )}

            {job.error_message ? <p className="status-text error">{job.error_message}</p> : null}

            {job.download_url ? (
              <button className="primary-button" type="button" onClick={() => handleDownload(job)}>
                Download video
              </button>
            ) : (
              <span className="status-text">
                {job.status === "failed"
                  ? "Processing failed"
                  : "Download link will appear once the output is ready"}
              </span>
            )}

            <span className="status-text">
              Preview served from {API_BASE_URL.replace("http://", "").replace("https://", "")}
            </span>
          </article>
        ))}
      </div>
    </div>
  );
}
