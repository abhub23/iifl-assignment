"use client";

import { useState } from "react";

const MAX_LENGTH = 10_000;

type Props = {
  onSubmit: (text: string) => Promise<void>;
};

export default function NewEntryForm({ onSubmit }: Props) {
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmed = text.trim();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(trimmed);
      setText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-border-subtle bg-surface-raised p-5"
    >
      <label htmlFor="entry-text" className="mb-2 block text-sm font-medium text-neutral-200">
        Submit text
      </label>
      <div className="overflow-hidden rounded-xl border border-border-subtle bg-surface transition focus-within:border-indigo-400/60 focus-within:ring-2 focus-within:ring-indigo-400/20">
        <textarea
          id="entry-text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste a note, article draft, or meeting transcript…"
          rows={8}
          maxLength={MAX_LENGTH}
          className="block w-full min-h-52 resize-y bg-transparent p-3 text-sm leading-relaxed text-neutral-100 outline-none disabled:opacity-50"
          disabled={submitting}
        />
      </div>
      <div className="mt-1 flex items-center justify-between text-xs text-neutral-500">
        <span>
          {text.length.toLocaleString()} / {MAX_LENGTH.toLocaleString()}
        </span>
      </div>

      {error && (
        <p
          role="alert"
          className="mt-3 rounded-lg border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-300"
        >
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting || !trimmed}
        className="mt-4 inline-flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto"
      >
        {submitting && (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
        )}
        {submitting ? "Summarizing…" : "Summarize & tag"}
      </button>
    </form>
  );
}
