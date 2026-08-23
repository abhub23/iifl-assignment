import type { Entry } from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function parseError(res: Response): Promise<never> {
  let message = `Request failed (${res.status})`;
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") message = body.detail;
  } catch {
    // keep the generic message
  }
  throw new Error(message);
}

export async function fetchEntries(): Promise<Entry[]> {
  const res = await fetch(`${API_BASE}/entries`, { cache: "no-store" });
  if (!res.ok) return parseError(res);
  return res.json();
}

export async function createEntry(text: string): Promise<Entry> {
  const res = await fetch(`${API_BASE}/entries`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) return parseError(res);
  return res.json();
}
