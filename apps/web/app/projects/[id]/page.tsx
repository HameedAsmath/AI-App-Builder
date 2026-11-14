"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

type Msg = { role: "user" | "assistant"; content: string };
type Project = { id: string; name: string; preview_url: string | null };

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Load project + chat history
  useEffect(() => {
    api<Project>(`/projects/${id}`)
      .then((p) => {
        setProject(p);
        setPreviewUrl(p.preview_url);
      })
      .catch(() => router.push("/projects"));
    api<Msg[]>(`/projects/${id}/messages`)
      .then(setMessages)
      .catch(() => {});
  }, [id, router]);

  function appendToLast(text: string) {
    setMessages((prev) => {
      const copy = [...prev];
      const last = copy[copy.length - 1];
      copy[copy.length - 1] = { ...last, content: last.content + text };
      return copy;
    });
  }

  function reloadPreview() {
    if (iframeRef.current && previewUrl) iframeRef.current.src = previewUrl;
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;

    setInput("");
    setBusy(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "" },
    ]);

    const res = await fetch(`/api/projects/${id}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    if (!res.ok || !res.body) {
      appendToLast("⚠️ Request failed");
      setBusy(false);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";
      for (const event of events) {
        if (!event.startsWith("data: ")) continue;
        const data = JSON.parse(event.slice(6));
        if (data.type === "token") appendToLast(data.text);
        if (data.type === "status") setStatus(data.text);
        if (data.type === "preview") setPreviewUrl(data.url);
        if (data.type === "error") appendToLast(`\n\n⚠️ ${data.message}`);
      }
    }
    setBusy(false);
    reloadPreview();
  }

  return (
    <main className="flex h-screen">
      {/* Chat */}
      <section className="flex w-[420px] flex-col border-r p-4">
        <Link
          href="/projects"
          className="mb-2 text-sm text-muted-foreground hover:underline"
        >
          ← Projects
        </Link>
        <h1 className="mb-4 font-semibold">{project?.name}</h1>

        <div className="flex-1 space-y-3 overflow-y-auto">
          {messages.length === 0 && (
            <p className="text-muted-foreground">
              Describe the app you want to build.
            </p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`whitespace-pre-wrap rounded-lg p-3 text-sm ${m.role === "user" ? "ml-8 bg-muted" : "mr-8 border"}`}
            >
              {m.content || "…"}
            </div>
          ))}
        </div>

        {status && (
          <p className="mt-2 text-xs text-muted-foreground">{status}</p>
        )}

        <form onSubmit={send} className="mt-2 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Create a todo application"
            disabled={busy}
          />
          <Button type="submit" disabled={busy}>
            {busy ? "…" : "Send"}
          </Button>
        </form>
      </section>

      {/* Preview */}
      <section className="flex flex-1 flex-col">
        <div className="flex items-center justify-between border-b px-4 py-2 text-xs text-muted-foreground">
          <span className="truncate">{previewUrl ?? "No preview yet"}</span>
          {previewUrl && (
            <Button variant="ghost" size="sm" onClick={reloadPreview}>
              Reload
            </Button>
          )}
        </div>
        {previewUrl ? (
          <iframe ref={iframeRef} src={previewUrl} className="flex-1" />
        ) : (
          <div className="flex flex-1 items-center justify-center text-muted-foreground">
            Send a message to start building
          </div>
        )}
      </section>
    </main>
  );
}
