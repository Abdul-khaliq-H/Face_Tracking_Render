"use client";

import { FormEvent, useState } from "react";
import { apiRequest, AuthResponse } from "../lib/api";

type Mode = "login" | "register";

export function AuthForm() {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("");
  const [isError, setIsError] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setIsError(false);
    setStatus("");

    try {
      const response = await apiRequest<AuthResponse>(`/auth/${mode === "login" ? "login" : "register"}`, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      localStorage.setItem("creatortrack_token", response.access_token);
      localStorage.setItem("creatortrack_email", response.email);
      setStatus(`Signed in as ${response.email}. You can now upload videos on the Try now page.`);
    } catch (error) {
      setIsError(true);
      setStatus(error instanceof Error ? error.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card auth-card">
      <div className="pill">{mode === "login" ? "Welcome back" : "Create your account"}</div>
      <h1 className="section-title">{mode === "login" ? "Sign in" : "Sign up"}</h1>
      <p className="section-copy">
        Use your email and password to access the video processing dashboard.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            placeholder="creator@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>

        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>

        <div className="form-row" style={{ marginTop: 18 }}>
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Need an account?" : "Already have an account?"}
          </button>
        </div>
      </form>

      {status ? (
        <p className={`status-text ${isError ? "error" : "success"}`}>{status}</p>
      ) : null}
    </div>
  );
}

