"use client";

import { useCallback, useEffect, useState } from "react";

import EntryDetail from "./components/EntryDetail";
import EntryList from "./components/EntryList";
import NewEntryForm from "./components/NewEntryForm";
import { createEntry, fetchEntries } from "./lib/api";
import type { Entry } from "./types";

export default function Home() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Entry | null>(null);

  const loadEntries = useCallback(async () => {
    setListError(null);
    try {
      setEntries(await fetchEntries());
    } catch (err) {
      setListError(err instanceof Error ? err.message : "Failed to load entries");
    }
  }, []);

  useEffect(() => {
    loadEntries().finally(() => setLoadingList(false));
  }, [loadEntries]);

  async function handleSubmit(text: string) {
    const created = await createEntry(text);
    await loadEntries();
    setSelected(created);
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-white">AI Content Assistant</h1>
        <p className="mt-1 text-sm text-neutral-400">
          Submit a note or transcript and get back a concise summary and three tags.
        </p>
      </header>

      <NewEntryForm onSubmit={handleSubmit} />

      <section className="mt-10">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-400">
            Saved entries
          </h2>
          {entries.length > 0 && (
            <span className="text-xs text-neutral-500">{entries.length} total</span>
          )}
        </div>

        {listError && (
          <p
            role="alert"
            className="rounded-lg border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-300"
          >
            {listError}
          </p>
        )}

        {loadingList ? (
          <p className="text-sm text-neutral-500">Loading entries…</p>
        ) : (
          !listError && (
            <EntryList entries={entries} selectedId={selected?.id ?? null} onSelect={setSelected} />
          )
        )}
      </section>

      {selected && <EntryDetail entry={selected} onClose={() => setSelected(null)} />}
    </main>
  );
}
