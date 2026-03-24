export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

export type AuthResponse = {
  access_token: string;
  token_type: string;
  email: string;
};

export type Job = {
  id: number;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  error_message: string | null;
  input_url: string;
  output_url: string | null;
  download_url: string | null;
  created_at: string;
};

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? "Request failed");
  }

  return response.json() as Promise<T>;
}
