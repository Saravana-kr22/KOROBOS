"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";

interface Topic {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export default function TopicsPage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");

  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  const authHeaders = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  const loadTopics = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/v1/learning/topics", {
        headers: authHeaders,
      });
      if (res.ok) {
        const data = await res.json();
        setTopics(data.topics || []);
      } else {
        setError("Failed to load topics");
      }
    } catch {
      setError("Failed to load topics");
    } finally {
      setLoading(false);
    }
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!token) return;
    loadTopics();
  }, [token, loadTopics]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      const res = await fetch("/api/v1/learning/topics", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ name: newName.trim() }),
      });
      if (res.ok) {
        setNewName("");
        setShowForm(false);
        await loadTopics();
      } else {
        setError("Failed to create topic");
      }
    } catch {
      setError("Failed to create topic");
    }
  };

  const handleUpdate = async (topicId: string) => {
    if (!editName.trim()) return;
    try {
      const res = await fetch(`/api/v1/learning/topics/${topicId}`, {
        method: "PUT",
        headers: authHeaders,
        body: JSON.stringify({ name: editName.trim() }),
      });
      if (res.ok) {
        setEditingId(null);
        setEditName("");
        await loadTopics();
      } else {
        setError("Failed to update topic");
      }
    } catch {
      setError("Failed to update topic");
    }
  };

  const handleDelete = async (topicId: string, name: string) => {
    if (
      !confirm(
        `Delete topic "${name}"? Sessions linked to it will not be deleted.`,
      )
    )
      return;
    try {
      const res = await fetch(`/api/v1/learning/topics/${topicId}`, {
        method: "DELETE",
        headers: authHeaders,
      });
      if (res.ok) {
        await loadTopics();
      } else {
        setError("Failed to delete topic");
      }
    } catch {
      setError("Failed to delete topic");
    }
  };

  if (loading) return <div style={{ padding: "20px" }}>Loading...</div>;

  return (
    <div style={{ maxWidth: "720px", margin: "0 auto", padding: "20px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Link
            href="/learning"
            style={{ color: "#007bff", textDecoration: "none" }}
          >
            ← Learning
          </Link>
          <h1 style={{ margin: 0 }}>Topics</h1>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            padding: "8px 14px",
            backgroundColor: "#007bff",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          {showForm ? "Cancel" : "New Topic"}
        </button>
      </div>

      {error && (
        <div style={{ color: "red", marginBottom: "12px" }}>{error}</div>
      )}

      {showForm && (
        <form
          onSubmit={handleCreate}
          style={{ display: "flex", gap: "8px", marginBottom: "20px" }}
        >
          <input
            type="text"
            placeholder="Topic name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
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
            Create
          </button>
        </form>
      )}

      {topics.length === 0 ? (
        <p style={{ color: "#666" }}>
          No topics yet. Create one to group your learning sessions.
        </p>
      ) : (
        <div>
          {topics.map((topic) => (
            <div
              key={topic.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "10px 12px",
                border: "1px solid #eee",
                borderRadius: "6px",
                marginBottom: "8px",
              }}
            >
              {editingId === topic.id ? (
                <>
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    style={{
                      flex: 1,
                      padding: "6px",
                      borderRadius: "4px",
                      border: "1px solid #ddd",
                    }}
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleUpdate(topic.id);
                      if (e.key === "Escape") {
                        setEditingId(null);
                        setEditName("");
                      }
                    }}
                  />
                  <button
                    onClick={() => handleUpdate(topic.id)}
                    style={{
                      padding: "6px 12px",
                      backgroundColor: "#28a745",
                      color: "white",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    Save
                  </button>
                  <button
                    onClick={() => {
                      setEditingId(null);
                      setEditName("");
                    }}
                    style={{
                      padding: "6px 12px",
                      backgroundColor: "#6c757d",
                      color: "white",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <span style={{ flex: 1, fontWeight: 500 }}>{topic.name}</span>
                  <span style={{ fontSize: "12px", color: "#999" }}>
                    {new Date(topic.created_at).toLocaleDateString()}
                  </span>
                  <button
                    onClick={() => {
                      setEditingId(topic.id);
                      setEditName(topic.name);
                    }}
                    style={{
                      padding: "4px 10px",
                      backgroundColor: "transparent",
                      color: "#007bff",
                      border: "1px solid #007bff",
                      borderRadius: "4px",
                      cursor: "pointer",
                      fontSize: "13px",
                    }}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(topic.id, topic.name)}
                    style={{
                      padding: "4px 10px",
                      backgroundColor: "transparent",
                      color: "#dc3545",
                      border: "1px solid #dc3545",
                      borderRadius: "4px",
                      cursor: "pointer",
                      fontSize: "13px",
                    }}
                  >
                    Delete
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
