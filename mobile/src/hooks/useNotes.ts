/**
 * KOROBOS — Second Brain Operating System
 * Copyright (c) 2026 Saravana Perumal K
 * Licensed under the GNU Affero General Public License v3.
 *
 * React hooks for note state management with offline draft support — Sprint 6 §12.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useState } from "react";
import * as NotesApi from "../services/notesApi";
import type { Note, NoteDraft, NoteListResponse } from "../types/notes";

const DRAFTS_KEY = "korobos:note_drafts";

// ── Offline draft storage ────────────────────────────────────────────────────

export function useDrafts() {
  const [drafts, setDrafts] = useState<NoteDraft[]>([]);

  useEffect(() => {
    AsyncStorage.getItem(DRAFTS_KEY).then((raw) => {
      if (raw) setDrafts(JSON.parse(raw));
    });
  }, []);

  const saveDraft = useCallback(
    async (draft: Omit<NoteDraft, "local_id" | "synced" | "created_at">) => {
      const newDraft: NoteDraft = {
        ...draft,
        local_id: `draft_${Date.now()}`,
        created_at: new Date().toISOString(),
        synced: false,
      };
      const updated = [...drafts, newDraft];
      setDrafts(updated);
      await AsyncStorage.setItem(DRAFTS_KEY, JSON.stringify(updated));
      return newDraft;
    },
    [drafts],
  );

  const removeDraft = useCallback(
    async (local_id: string) => {
      const updated = drafts.filter((d) => d.local_id !== local_id);
      setDrafts(updated);
      await AsyncStorage.setItem(DRAFTS_KEY, JSON.stringify(updated));
    },
    [drafts],
  );

  /** Sync all unsynced drafts to the API. */
  const syncDrafts = useCallback(
    async (token: string) => {
      const unsynced = drafts.filter((d) => !d.synced);
      for (const draft of unsynced) {
        try {
          await NotesApi.createNote(token, {
            title: draft.title,
            content_md: draft.content_md,
            tags: draft.tags,
          });
          await removeDraft(draft.local_id);
        } catch {
          // Keep draft for next sync attempt
        }
      }
    },
    [drafts, removeDraft],
  );

  return { drafts, saveDraft, removeDraft, syncDrafts };
}

// ── Notes list ───────────────────────────────────────────────────────────────

export function useNotesList(token: string) {
  const [response, setResponse] = useState<NoteListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPage = useCallback(
    async (p: number) => {
      if (!token) return;
      setLoading(true);
      setError(null);
      try {
        const data = await NotesApi.listNotes(token, p, 20);
        setResponse(data);
        setPage(p);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load notes");
      } finally {
        setLoading(false);
      }
    },
    [token],
  );

  useEffect(() => {
    fetchPage(1);
  }, [fetchPage]);

  return {
    notes: response?.notes ?? [],
    total: response?.total ?? 0,
    pages: response?.pages ?? 1,
    page,
    loading,
    error,
    refresh: () => fetchPage(1),
    nextPage: () => page < (response?.pages ?? 1) && fetchPage(page + 1),
    prevPage: () => page > 1 && fetchPage(page - 1),
  };
}

// ── Single note ──────────────────────────────────────────────────────────────

export function useNote(token: string, noteId: string) {
  const [note, setNote] = useState<Note | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !noteId) return;
    setLoading(true);
    NotesApi.getNote(token, noteId)
      .then(setNote)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token, noteId]);

  return { note, loading, error };
}
