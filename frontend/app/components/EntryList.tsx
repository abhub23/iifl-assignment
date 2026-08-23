"use client";

import type { Entry } from "../types";

export function formatTimestamp(utc: string): string {
  const iso = utc.includes("T") ? utc : utc.replace(" ", "T") + "Z";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

type Props = {
  entries: Entry[];
  selectedId: number | null;
  onSelect: (entry: Entry) => void;
};

export default function EntryList({ entries, selectedId, onSelect }: Props) {
  if (entries.length === 0) {
    return (
      <p className="rounded-2xl border border-dashed border-border-subtle p-8 text-center text-sm text-neutral-500">
        No saved entries yet, submit some text to get started.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {entries.map((entry) => (
        <li key={entry.id}>
          <button
            onClick={() => onSelect(entry)}
            aria-current={selectedId === entry.id || undefined}
            className="w-full rounded-2xl border border-border-subtle bg-surface-raised p-4 text-left transition hover:border-indigo-400/50 hover:bg-[#1b1b23]"
          >
            <div className="flex items-start justify-between gap-3">
              <p className="line-clamp-2 text-sm leading-relaxed text-neutral-100">
                {entry.summary}
              </p>
              <span className="shrink-0 text-xs text-neutral-500">
                #{entry.id} · {formatTimestamp(entry.created_at)}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {entry.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-xs font-medium text-indigo-300"
                >
                  {tag}
                </span>
              ))}
            </div>
          </button>
        </li>
      ))}
    </ul>
  );
}
