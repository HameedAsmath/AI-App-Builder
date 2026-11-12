"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

type Msg = { role: "user" | "assistant"; content: string };

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  // Load chat history
  useEffect(() => {
    api<Msg[]>(`/projects/${id}/messages`)
      .then(setMessages)
      .catch(() => router.push("/projects"));
  }, [id, router]);

  // Add streamed text to the last (assistant) message
  function appendToLast(text: string) {
    setMessages((prev) => {
      const copy = [...prev];
      const last = copy[copy.length - 1];
      copy[copy.length - 1] = { ...last, content: last.content + text };
      return copy;
    });
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

    // Read the SSE stream chunk by chunk
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? ""; // keep any incomplete event for the next chunk
      for (const event of events) {
        if (!event.startsWith("data: ")) continue;
        const data = JSON.parse(event.slice(6));
        if (data.type === "token") appendToLast(data.text);
        if (data.type === "error") appendToLast(`\n\n⚠️ ${data.message}`);
      }
    }
    setBusy(false);
  }

  return (
    <main className="mx-auto flex h-screen max-w-3xl flex-col p-4">
      <Link
        href="/projects"
        className="mb-4 text-sm text-muted-foreground hover:underline"
      >
        ← Projects
      </Link>

      <div className="flex-1 space-y-4 overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-muted-foreground">
            Describe the app you want to build.
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`whitespace-pre-wrap rounded-lg p-3 ${m.role === "user" ? "ml-12 bg-muted" : "mr-12 border"}`}
          >
            {m.content || "…"}
          </div>
        ))}
      </div>

      <form onSubmit={send} className="mt-4 flex gap-2">
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
    </main>
  );
}
