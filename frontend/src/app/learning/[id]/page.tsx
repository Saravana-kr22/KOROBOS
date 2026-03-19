"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface LearningSession {
  id: string;
  user_id: string;
  topic: string;
  topic_id: string | null;
  duration: number;
  notes: string | null;
  status: string;
  start_time: string | null;
  end_time: string | null;
  created_at: string;
  updated_at: string;
}

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params.id as string;

  const [session, setSession] = useState<LearningSession | null>(null);
  const [noteIds, setNoteIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [linking, setLinking] = useState(false);
  const [linkNoteId, setLinkNoteId] = useState("");
  const [deleting, setDeleting] = useState(false);

  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  const authHeaders = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  const loadSession = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [sessRes, notesRes] = await Promise.all([
        fetch(`/api/v1/learning/sessions/${sessionId}`, {
          headers: authHeaders,
        }),
        fetch(`/api/v1/learning/sessions/${sessionId}/notes`, {
          headers: authHeaders,
        }),
      ]);

      if (sessRes.ok) {
        setSession(await sessRes.json());
      } else if (sessRes.status === 404) {
        setError("Session not found");
      } else {
        setError("Failed to load session");
      }

      if (notesRes.ok) {
        const data = await notesRes.json();
        setNoteIds(data.note_ids || []);
      }
    } catch {
      setError("Failed to load session");
    } finally {
      setLoading(false);
    }
  }, [sessionId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!token || !sessionId) return;
    loadSession();
  }, [token, sessionId, loadSession]);

  const handleLinkNote = async (e: FormEvent) => {
    e.preventDefault();
    if (!linkNoteId.trim()) return;
    try {
      const res = await fetch(`/api/v1/learning/sessions/${sessionId}/notes`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ note_id: linkNoteId.trim() }),
      });
      if (res.ok) {
        setLinkNoteId("");
        setLinking(false);
        await loadSession();
      } else {
        setError("Failed to link note");
      }
    } catch {
      setError("Failed to link note");
    }
  };

  const handleUnlinkNote = async (noteId: string) => {
    try {
      const res = await fetch(
        `/api/v1/learning/sessions/${sessionId}/notes/${noteId}`,
        {
          method: "DELETE",
          headers: authHeaders,
        },
      );
      if (res.ok) {
        await loadSession();
      } else {
        setError("Failed to unlink note");
      }
    } catch {
      setError("Failed to unlink note");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Delete this session? This cannot be undone.")) return;
    setDeleting(true);
    try {
      const res = await fetch(`/api/v1/learning/sessions/${sessionId}`, {
        method: "DELETE",
        headers: authHeaders,
      });
      if (res.ok) {
        window.location.href = "/learning";
      } else {
        setError("Failed to delete session");
        setDeleting(false);
      }
    } catch {
      setError("Failed to delete session");
      setDeleting(false);
    }
  };

  if (loading) return <div style={{ padding: "20px" }}>Loading...</div>;
  if (error && !session)
    return <div style={{ padding: "20px", color: "red" }}>{error}</div>;
  if (!session) return null;

  const statusColor =
    session.status === "completed"
      ? "#2e7d32"
      : session.status === "active"
      ? "#1565c0"
      : "#f57f17";
  const statusBg =
    session.status === "completed"
      ? "#e8f5e9"
      : session.status === "active"
      ? "#e3f2fd"
      : "#fff8e1";

  return (
    <div style={{ maxWidth: "720px", margin: "0 auto", padding: "20px" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <Link
          href="/learning"
          style={{ color: "#007bff", textDecoration: "none" }}
        >
          ← Learning
        </Link>
        <button
          onClick={handleDelete}
          disabled={deleting}
          style={{
            padding: "6px 12px",
            backgroundColor: "transparent",
            color: "#dc3545",
            border: "1px solid #dc3545",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          {deleting ? "Deleting…" : "Delete"}
        </button>
      </div>

      {error && (
        <div style={{ color: "red", marginBottom: "12px" }}>{error}</div>
      )}

      {/* Session details */}
      <div
        style={{
          border: "1px solid #eee",
          borderRadius: "8px",
          padding: "20px",
          marginBottom: "20px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "12px",
          }}
        >
          <h2 style={{ margin: 0 }}>{session.topic}</h2>
          <span
            style={{
              fontSize: "13px",
              padding: "3px 10px",
              borderRadius: "12px",
              backgroundColor: statusBg,
              color: statusColor,
            }}
          >
            {session.status}
          </span>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "12px",
            marginBottom: "12px",
          }}
        >
          <div>
            <div
              style={{ fontSize: "12px", color: "#999", marginBottom: "2px" }}
            >
              Duration
            </div>
            <div style={{ fontWeight: 500 }}>{session.duration} minutes</div>
          </div>
          <div>
            <div
              style={{ fontSize: "12px", color: "#999", marginBottom: "2px" }}
            >
              Created
            </div>
            <div style={{ fontWeight: 500 }}>
              {new Date(session.created_at).toLocaleString()}
            </div>
          </div>
          {session.start_time && (
            <div>
              <div
                style={{ fontSize: "12px", color: "#999", marginBottom: "2px" }}
              >
                Started
              </div>
              <div style={{ fontWeight: 500 }}>
                {new Date(session.start_time).toLocaleTimeString()}
              </div>
            </div>
          )}
          {session.end_time && (
            <div>
              <div
                style={{ fontSize: "12px", color: "#999", marginBottom: "2px" }}
              >
                Ended
              </div>
              <div style={{ fontWeight: 500 }}>
                {new Date(session.end_time).toLocaleTimeString()}
              </div>
            </div>
          )}
        </div>

        {session.notes && (
          <div>
            <div
              style={{ fontSize: "12px", color: "#999", marginBottom: "4px" }}
            >
              Notes
            </div>
            <div style={{ whiteSpace: "pre-wrap", color: "#333" }}>
              {session.notes}
            </div>
          </div>
        )}
      </div>

      {/* Linked Notes */}
      <div
        style={{
          border: "1px solid #eee",
          borderRadius: "8px",
          padding: "20px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "12px",
          }}
        >
          <h3 style={{ margin: 0 }}>Linked Notes ({noteIds.length})</h3>
          <button
            onClick={() => setLinking(!linking)}
            style={{
              padding: "6px 12px",
              backgroundColor: "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            {linking ? "Cancel" : "Link Note"}
          </button>
        </div>

        {linking && (
          <form
            onSubmit={handleLinkNote}
            style={{ display: "flex", gap: "8px", marginBottom: "12px" }}
          >
            <input
              type="text"
              placeholder="Note ID (UUID)"
              value={linkNoteId}
              onChange={(e) => setLinkNoteId(e.target.value)}
              style={{
                flex: 1,
                padding: "8px",
                borderRadius: "4px",
                border: "1px solid #ddd",
              }}
              autoFocus
            />
            <button
              type="submit"
              style={{
                padding: "8px 14px",
                backgroundColor: "#28a745",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Link
            </button>
          </form>
        )}

        {noteIds.length === 0 ? (
          <p style={{ color: "#999", margin: 0, fontSize: "14px" }}>
            No notes linked yet.
          </p>
        ) : (
          <div>
            {noteIds.map((noteId) => (
              <div
                key={noteId}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "8px 12px",
                  border: "1px solid #eee",
                  borderRadius: "6px",
                  marginBottom: "6px",
                }}
              >
                <span
                  style={{
                    fontFamily: "monospace",
                    fontSize: "13px",
                    color: "#333",
                  }}
                >
                  {noteId}
                </span>
                <button
                  onClick={() => handleUnlinkNote(noteId)}
                  style={{
                    padding: "3px 8px",
                    backgroundColor: "transparent",
                    color: "#dc3545",
                    border: "1px solid #dc3545",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontSize: "12px",
                  }}
                >
                  Unlink
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
