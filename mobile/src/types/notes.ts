/**
 * KOROBOS — Second Brain Operating System
 * Copyright (c) 2026 Saravana Perumal K
 * Licensed under the GNU Affero General Public License v3.
 *
 * Shared TypeScript types for the Notes & Knowledge feature — Sprint 6 §12.
 */

export interface Note {
  id: string;
  user_id: string;
  title: string;
  content_md: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface NoteListResponse {
  notes: Note[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface BacklinkListResponse {
  backlinks: Note[];
  total: number;
}

export interface NoteLinkResponse {
  id: string;
  source_note_id: string;
  target_note_id: string;
}

export interface CreateNotePayload {
  title: string;
  content_md: string;
  tags?: string[];
}

export interface UpdateNotePayload {
  title?: string;
  content_md?: string;
  tags?: string[];
}

/** Offline draft stored locally before sync. */
export interface NoteDraft {
  local_id: string;
  title: string;
  content_md: string;
  tags: string[];
  created_at: string;
  synced: boolean;
}
