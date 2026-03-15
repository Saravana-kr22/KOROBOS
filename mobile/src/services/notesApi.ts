/**
 * KOROBOS — Second Brain Operating System
 * Copyright (c) 2026 Saravana Perumal K
 * Licensed under the GNU Affero General Public License v3.
 *
 * Notes API client for React Native — Sprint 6 §12.
 *
 * All requests are routed through the API Gateway.
 * The X-User-ID header is injected by the gateway after JWT validation;
 * the mobile client must supply a valid Bearer token in Authorization.
 */

import type {
  BacklinkListResponse,
  CreateNotePayload,
  Note,
  NoteListResponse,
  NoteLinkResponse,
  UpdateNotePayload,
} from "../types/notes";

const API_BASE =
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8080/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token: string },
): Promise<T> {
  const { token, ...rest } = options;
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(rest.headers ?? {}),
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Notes CRUD ───────────────────────────────────────────────────────────────

/** Fetch a paginated list of the user's notes. */
export async function listNotes(
  token: string,
  page = 1,
  limit = 20,
): Promise<NoteListResponse> {
  return request<NoteListResponse>(`/notes?page=${page}&limit=${limit}`, {
    method: "GET",
    token,
  });
}

/** Fetch a single note by ID. */
export async function getNote(token: string, noteId: string): Promise<Note> {
  return request<Note>(`/notes/${noteId}`, { method: "GET", token });
}

/** Create a new note. */
export async function createNote(
  token: string,
  payload: CreateNotePayload,
): Promise<Note> {
  return request<Note>("/notes", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

/** Update an existing note (partial update). */
export async function updateNote(
  token: string,
  noteId: string,
  payload: UpdateNotePayload,
): Promise<Note> {
  return request<Note>(`/notes/${noteId}`, {
    method: "PUT",
    token,
    body: JSON.stringify(payload),
  });
}

/** Delete a note. */
export async function deleteNote(token: string, noteId: string): Promise<void> {
  return request<void>(`/notes/${noteId}`, { method: "DELETE", token });
}

// ── Backlinks & Links ────────────────────────────────────────────────────────

/** Get all notes that reference this note via [[wiki-links]]. */
export async function getBacklinks(
  token: string,
  noteId: string,
): Promise<BacklinkListResponse> {
  return request<BacklinkListResponse>(`/notes/${noteId}/backlinks`, {
    method: "GET",
    token,
  });
}

/** Create an explicit link between two notes. */
export async function createLink(
  token: string,
  sourceNoteId: string,
  targetNoteId: string,
): Promise<NoteLinkResponse> {
  return request<NoteLinkResponse>(`/notes/${sourceNoteId}/links`, {
    method: "POST",
    token,
    body: JSON.stringify({ target_note_id: targetNoteId }),
  });
}
