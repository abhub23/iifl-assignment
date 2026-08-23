"use client";

import type { Entry } from "../types";
import { formatTimestamp } from "./EntryList";

type Props = {
  entry: Entry;
  onClose: () => void;
};

export default function EntryDetail({ entry, onClose }: Props) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Entry detail"
    >
      <div
        className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-border-subtle bg-surface-raised p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-white">Entry #{entry.id}</h2>
            <p className="text-xs text-neutral-500">{formatTimestamp(entry.created_at)} (UTC)</p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close detail view"
            className="rounded-lg border border-border-subtle px-3 py-1.5 text-sm text-neutral-300 transition hover:bg-surface"
          >
            Close
          </button>
        </div>

        <section className="mb-4">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-400">
            Summary
          </h3>
          <p className="rounded-xl bg-surface p-4 text-sm leading-relaxed text-neutral-100">
            {entry.summary}
          </p>
        </section>

        <section className="mb-4">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-400">
            Tags
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {entry.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300"
              >
                {tag}
              </span>
            ))}
          </div>
        </section>

        <section>
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-400">
            Original text
          </h3>
          <p className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-xl bg-surface p-4 text-sm leading-relaxed text-neutral-300">
            {entry.original_text}
          </p>
        </section>
      </div>
    </div>
  );
}
